import ast, logging, json, re
import html

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q, When, Case, CharField, F, Q, Value
from django.db.models.functions import Concat

from rest_framework.response import Response
from rest_framework import viewsets, status, mixins, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi

# from llama_index import GPTVectorStoreIndex
# from llama_index.data_structs.node import Node

from sanusi.analysis.entity_recognition import extract_topics

from .models import Chat, ChatStatus, Message, Customer
from .serializers import (
    AutoResponseSerializer,
    ChatListDetailSerializer,
    ChatSerializer,
    CreateChatRequestSerializer,
    IdsSerializer,
    MessageSerializer,
    CustomerSerializer,
    RestructureTextSerializer,
)
from .models import Chat, Message, Customer, SENDER_CHOICES

from sanusi.views import (
    generate_response,
    generate_response_chat,
    generate_response_chat_v2,
    generate_response_email,
    generate_response_email_v2,
    construct_index,
    structure_response,
)
from business.models import Business
from business.private.models import Category, KnowledgeBase, Product
from sanusi.models import Message as sanusi_message
from sanusi.utils import (
    is_valid_format,
    parse_answer_with_regex,
    parse_json_from_answer,
    parse_response_data,
    save_chat_and_message,
    try_parse_json,
)


instructions_for_auto_response = "Return your response as each of these parameters in a JSON format. Json format should be {'response': '[Generated response based on the information provided]',set escalation_department to 'none' if escalate Issue is false 'escalate Issue : boolean, 'escalation_department': '[sales/operations/billing/engineering]', 'severity': '[low/medium/high]','sentiment': '[positive/negative/neutral]'}."

logger = logging.getLogger(__name__)

# Open the JSON file and read its contents
with open("sanusi/instructions.json") as json_file:
    json_data = json.load(json_file)

# Access the values in the dictionary
email_v1_instructions = json_data["email_v1_instructions"]
chat_v1_instructions = json_data["chat_v1_instructions"]
chat_v2_instructions = json_data["chat_v2_instructions"]
response_instructions = json_data["response_instructions"]
escalate_issue_instructions = json_data["escalate_issue"]
escalation_instructions = json_data["escalation_instructions"]
sentiment_analysis = json_data["sentiment_analysis"]
severity_instructions = json_data["severity_instructions"]
dummy_knowledge_base = json_data["dummy_knowledge_base"]
response_instructions_chat = json_data["response_instructions_chat"]
chat_context_instructions = json_data["chat_context_instructions"]
valid_channels = ["chat", "whatsapp", "telegram", "instagram", "tiktok"]


class CustomerViewSet(
    mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        business_id = self.kwargs.get("business_id")
        if business_id:
            queryset = queryset.filter(
                customer_chats__business_chats__company_id=business_id
            )
        return queryset

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ChatViewSet(viewsets.GenericViewSet):
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()
    filter_backend = filters.SearchFilter
    search_fields = ["channel", "read", "customer__name", "status"]

    @transaction.atomic
    @swagger_auto_schema(request_body=CreateChatRequestSerializer)
    @action(
        detail=False,
        methods=["post"],
        url_path="(?P<business_id>[^/.]+)/create-chat",
    )
    def create_chat(self, request, business_id):
        serializer = CreateChatRequestSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        customer_name = serializer.validated_data["name"]
        customer_email = serializer.validated_data.get("customer_email", "")
        phone_number = serializer.validated_data.get("phone_number", "")

        business = get_object_or_404(Business, company_id=business_id)

        customer = Customer(
            name=customer_name, email=customer_email, phone_number=phone_number
        )
        customer.generate_identifier()
        customer.save()
        chat = Chat.objects.create(customer=customer, business=business)
        chat.generate_identifier()
        chat.save()

        chat_serializer = ChatSerializer(chat)
        company_id = str(chat.business.company_id)

        return Response(
            {
                "success": True,
                "chat_identifier": chat_serializer.data["identifier"],
                "business_id": company_id,
            }
        )

    @swagger_auto_schema(request_body=no_body)
    @action(
        detail=False,
        methods=["delete"],
        url_path="(?P<business_id>[^/.]+)/(?P<chat_identifier>[^/.]+)/delete-chat",
    )
    def delete_chat(self, request, business_id, chat_identifier):
        business = get_object_or_404(Business, company_id=business_id)
        chat = get_object_or_404(Chat, business=business, identifier=chat_identifier)
        chat.delete()
        return Response(data=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["put"],
        url_path="(?P<business_id>[^/.]+)/(?P<chat_identifier>[^/.]+)/end-chat",
    )
    @swagger_auto_schema(request_body=no_body)
    def end_chat(self, request, business_id, chat_identifier):
        business = get_object_or_404(Business, company_id=business_id)
        chat = get_object_or_404(Chat, business=business, identifier=chat_identifier)
        chat.status = ChatStatus.RESOLVED
        chat.end_time = timezone.now()
        chat.save()
        return Response({"success": True})

    @transaction.atomic
    @swagger_auto_schema(request_body=MessageSerializer)
    @action(
        detail=False,
        methods=["post"],
        url_path="(?P<business_id>[^/.]+)/(?P<chat_identifier>[^/.]+)/send-message",
    )
    def send_message(self, request, business_id, chat_identifier):
        serializer = MessageSerializer(data=request.data)
        business = get_object_or_404(Business, company_id=business_id)
        chat = get_object_or_404(
            Chat,
            business=business,
            identifier=chat_identifier,
            status=ChatStatus.ACTIVE,
        )
        if serializer.is_valid():
            chat.save()
            serializer.save(chat=chat)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    @swagger_auto_schema(request_body=IdsSerializer)
    @action(
        detail=False,
        methods=["post"],
        url_path="(?P<business_id>[^/.]+)/bulk-toggle-chat-status",
    )
    def bulk_toggle_chat_status(self, request, business_id):
        serializer = IdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        business = get_object_or_404(Business, company_id=business_id)
        chat_ids = serializer.validated_data["ids"]

        # Retrieve chats with the given identifiers and update their status
        chats = Chat.objects.filter(Q(business=business) & Q(identifier__in=chat_ids))
        new_status = Case(
            When(status=ChatStatus.RESOLVED, then=Value(ChatStatus.ACTIVE)),
            default=Value(ChatStatus.RESOLVED),
            output_field=CharField(),
        )
        chats.update(status=new_status)
        return Response(
            {"detail": "Chat statuses updated successfully."}, status=status.HTTP_200_OK
        )

    @csrf_exempt
    @action(
        detail=False,
        methods=["get"],
        url_path="(?P<business_id>[^/.]+)/(?P<chat_identifier>[^/.]+)/get-messages",
    )
    def get_messages(self, request, business_id, chat_identifier):
        try:
            business = get_object_or_404(Business, company_id=business_id)
        except Http404:
            raise Http404("Business not found")

        try:
            chat = get_object_or_404(
                Chat, business=business, identifier=chat_identifier
            )
        except Http404:
            raise Http404("Chat not found")
        messages = chat.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @csrf_exempt
    @action(
        detail=False,
        methods=["get"],
        url_path="(?P<business_id>[^/]+)/get-all-chats",
    )
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search query string",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: ChatListDetailSerializer(many=True)},
    )
    def get_all_chats(self, request, business_id):
        business = get_object_or_404(Business, company_id=business_id)
        chats = Chat.objects.filter(business=business).order_by("-id")

        # Apply search filter based on search_fields from parent class
        search_query = request.query_params.get("search", "")
        if search_query:
            filter_kwargs = Q()
            for field in self.search_fields:
                filter_kwargs |= Q(**{f"{field}__icontains": search_query})
            chats = chats.filter(filter_kwargs)

        serializer = ChatListDetailSerializer(chats, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        url_path="(?P<business_id>[^/]+)/(?P<chat_identifier>[^/.]+)/toggle-chat-status",
    )
    @swagger_auto_schema(request_body=no_body)
    def toggle_chat_status(self, request, business_id, chat_identifier):
        try:
            business = get_object_or_404(Business, company_id=business_id)
        except Http404:
            raise Http404("Business not found")

        try:
            chat = get_object_or_404(
                Chat, business=business, identifier=chat_identifier
            )
        except Http404:
            raise Http404("Chat not found")

        if chat.status == ChatStatus.ACTIVE:
            chat.status = ChatStatus.RESOLVED
        else:
            chat.status = ChatStatus.ACTIVE
        chat.save()
        return Response(
            {"success": True, "message": f"Chat is now {chat.status}."},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(request_body=no_body)
    @action(
        detail=False,
        methods=["post"],
        url_path="(?P<business_id>[^/]+)/(?P<chat_identifier>[^/.]+)/toggle-chat-status",
    )
    def toggle_sanusi(self, request, business_id, chat_identifier):
        try:
            business = get_object_or_404(Business, company_id=business_id)
        except Http404:
            raise Http404("Business not found")

        try:
            chat = get_object_or_404(
                Chat, business=business, identifier=chat_identifier
            )
        except Http404:
            raise Http404("Chat not found")

        if chat.is_auto_response == True:
            chat.is_auto_response = False
            chat.save()
        else:
            chat.is_auto_response = True
            chat.save()

        return Response(
            {"message": f"sanusi auto response is {chat.is_auto_response}"},
            status=status.HTTP_202_ACCEPTED,
        )

    @swagger_auto_schema(request_body=AutoResponseSerializer)
    @action(
        detail=False,
        methods=["post"],
        url_path="(?P<business_id>[^/]+)/(?P<chat_identifier>[^/.]+)/auto-response",
    )
    @transaction.atomic
    def auto_response(self, request, business_id, chat_identifier):
        # Deserialize and validate request data
        business = get_object_or_404(Business, company_id=business_id)
        serializer = AutoResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract data from the validated serializer
        validated_data = serializer.validated_data
        message = validated_data["message"]
        channel = validated_data["channel"]
        sender = validated_data["sender"]
        customer_identifier = validated_data.get("customer_identifier")
        customer_name = validated_data.get("customer_name")
        customer_email = validated_data.get("customer_email")

        # Retrieve Business and Chat objects
        if channel == "email_v1" or channel == "email_v2":
            customer, created = Customer.objects.get_or_create(
                identifier=customer_identifier,
                defaults={"name": customer_name or "", "email": customer_email},
            )
            if not created and (
                customer.name != customer_name or customer.email != customer_email
            ):
                customer.name = customer_name
                customer.email = customer_email
                customer.save()

            chat, created = Chat.objects.get_or_create(
                business=business,
                identifier=chat_identifier,
                defaults={"customer": customer},
            )

        else:
            chat = get_object_or_404(
                Chat, business_id=business, identifier=chat_identifier
            )

        # Retrieve knowledge bases and instructions for the business
        knowledge_bases = business.business_kb.all()
        # knowledge_base_contents = dummy_knowledge_base
        if knowledge_bases:
            # instructions = business.reply_instructions
            # knowledge_base_contents = "\n".join(
            #     [kb.cleaned_data for kb in knowledge_bases]
            # )
            knowledge_base_contents = [kb.cleaned_data for kb in knowledge_bases]
        else:
            return Response(
                "This business has no knowledge base, kindly create one to activate auto response"
            )

        # Retrieve escalation departments for the business
        # escalation_departments = "/".join(
        #     [dept.name for dept in business.escalation_departments.all()]
        # )

        # Ensure messages are ordered by creation time (or however they should be ordered)
        all_messages = (
            Message.objects.filter(chat=chat)
            .order_by("-sent_time")
            .values_list("sanusi_response", "content")[:10]
        )
        result = list(all_messages)
        sanusi_response = [item[0] for item in result if item[0] is not None]
        content = [item[1] for item in result if item[1] is not None]

        sanusi_response_str = ", ".join(sanusi_response)
        content_str = ", ".join(content)
        last_message = Message.objects.filter(chat=chat, sender="customer")[:2]
        # Build the prompt
        prompt = []

        # add all knowlegdebase to the prompt
        # prompt.insert(
        #     1,
        #     {
        #         "role": "system",
        #         "content": (
        #             f"Knowledge base to answer based off: {knowledge_base_contents}"
        #         ),
        #     },
        # )

        if channel == "email_v4":
            prompt = "Hello, I'm having trouble with my account. Can you help?"
            ai_response = generate_response(prompt)

            structured_response = structure_response(
                ai_response,
                escalate_issue=True,
                escalation_department="support",
                severity="medium",
                sentiment="neutral",
            )
            sanusi_message.objects.create(chat_session=structured_response)
            return Response(structured_response, status=status.HTTP_200_OK)

        if channel == "email_v1" or channel == "email":
            response_instructions_prompt = [
                {
                    "role": "system",
                    "content": f"response_instructions: {response_instructions}",
                },
                {
                    "role": "system",
                    "content": f"knowledge base to answer from: {knowledge_base_contents}",
                },
                {
                    "role": "system",
                    "content": f"User's previous messages for reflection: {last_message.content if last_message else ''} and your last response was: {last_message.sanusi_response if last_message else ' '} and user's name is {customer_name}",
                },
                {"role": "user", "content": f"{message}"},
            ]
            answer_4_response = generate_response_chat(
                response_instructions_prompt, 300
            )

            escalation_department_prompt = [
                {
                    "role": "system",
                    "content": f"escalation_instructions: {escalation_instructions}. Possible answers are 'sales', 'operations', 'billing', 'engineering', 'none'. none if you are unable to determine the department from the options provided",
                },
                {
                    "role": "assistant",
                    "content": f"message to be analysed: {message}",
                },
            ]
            answer_4_escalation_department = generate_response_chat(
                escalation_department_prompt, 1
            )
            print(answer_4_escalation_department)

            sentiment_analysis_prompt = [
                {
                    "role": "system",
                    "content": f"sentiment_analysis: {sentiment_analysis}. Possible answers are 'positive', 'negative', 'neutral'.",
                },
                {
                    "role": "assistant",
                    "content": f"message to be analysed: {message}",
                },
            ]
            answer_4_sentiment = generate_response_chat(sentiment_analysis_prompt, 1)

            severity_instructions_prompt = [
                {
                    "role": "system",
                    "content": f"severity_instructions: {severity_instructions}. only answers are 'low', 'medium', 'high'.",
                },
                {
                    "role": "assistant",
                    "content": f"message to be analysed: {message}",
                },
            ]
            answer_4_severity = generate_response_chat(severity_instructions_prompt, 1)

            severity = (
                answer_4_severity["choices"][0]["message"]["content"].lower().strip()
            )
            if severity not in ["low", "medium", "high"]:
                severity = "low"  # default to 'low' if invalid response

            chat_context_instructions_prompt = [
                {
                    "role": "system",
                    "content": f"Chat Context instructions: {chat_context_instructions}",
                },
                {
                    "role": "assistant",
                    "content": f"Chat to be analysed: ('sanusi previous responses': {sanusi_response_str}), ('the user messages': {content_str}), ('user's current message': {message})",
                },
            ]
            answer_4_chat_context = generate_response_chat(
                chat_context_instructions_prompt, 1
            )

            text = answer_4_response["choices"][0]["message"]["content"]
            html_text = html.escape(text)  # This will escape the text

            html_text = html_text.replace(
                "\n", "<br/>"
            )  # Replace newline characters with HTML line breaks

            response_html = "<p>{}</p>".format(html_text)

            response_json = {
                "response": response_html,
                "escalate_issue": True
                if answer_4_escalation_department["choices"][0]["message"][
                    "content"
                ].lower()
                in ["sales", "operations", "billing", "engineering", "support"]
                else False,
                "escalation_department": answer_4_escalation_department["choices"][0][
                    "message"
                ]["content"],
                "severity": severity,
                "sentiment": answer_4_sentiment["choices"][0]["message"]["content"],
                "chat_context": answer_4_chat_context["choices"][0]["message"][
                    "content"
                ],
            }
            save_chat_and_message(chat, sender, message, response_json, channel)
            return Response(response_json, status=status.HTTP_200_OK)

        if channel == "email_v2":
            prompt.insert(0, f"Reply instructions: {email_v1_instructions}")
            prompt.insert(
                1, f"knowledge base to answer based off: {knowledge_base_contents}"
            )
            prompt.insert(
                2,
                f"User's previous messages for reflection: {last_message.content if last_message else ''}",
            )
            prompt.insert(3, f"User's name: {customer_name}")
            prompt.insert(4, f"User's Message to be replied to: {message}")

            response_content = generate_response_email(prompt)
            answer = response_content["choices"][0]["text"]
            max_retry_attempts = 3
            print("--------------------------------", response_content)

            for attempt in range(max_retry_attempts):
                logger.info({"answer": answer})
                try:
                    start_index = answer.index("{")
                    end_index = answer.rindex("}") + 1
                    response_json_str = answer[start_index:end_index]
                    response_json = json.loads(response_json_str)
                    print(
                        response_json,
                        "-----------this is the parsed response--------------",
                    )
                    save_chat_and_message(chat, sender, message, response_json, channel)
                    return Response(response_json, status=status.HTTP_200_OK)
                except ValueError:
                    print(answer, "-----------this is the answer--------------")
                    try:
                        response_json = parse_response_data(answer)
                        print(
                            response_json,
                            "-----------this is after value error for email_v1---------------------",
                        )
                        save_chat_and_message(
                            chat, sender, message, response_json, channel
                        )
                        return Response(response_json, status=status.HTTP_200_OK)
                    except (json.JSONDecodeError, ValueError, AttributeError) as e:
                        if attempt < max_retry_attempts - 1:  # not the last attempt
                            prompt[
                                0
                            ] += "\nRemember to adhere strictly to the response instructions provided. An assistant is supposed to listen to instructions."
                            logger.error(
                                f"Error occurred during attempt {attempt + 1}: {str(e)}"
                            )
                        else:
                            logger.error(f"All attempts failed. Error: {str(e)}")
                            print(answer)
                            response_json = {
                                "response": answer,
                                "escalate_issue": False,
                                "escalation_department": "",
                                "severity": "",
                                "sentiment": "",
                            }
                            save_chat_and_message(
                                chat, sender, message, response_json, channel
                            )
                            return Response(
                                data=response_json, status=status.HTTP_200_OK
                            )

            # chat.channel = channel
            # chat.save()

            # Message.objects.create(
            #     chat=chat,
            #     content=message,
            #     sender=str(sender),
            #     sanusi_response=response_json,
            # )
            # return Response(data=response_json, status=status.HTTP_200_OK)

        elif channel == "email_v3":
            max_retry_attempts = 3
            for attempt in range(max_retry_attempts):
                response_parts = generate_response_email_v2(prompt)

                # Check if response_parts is an error message
                if isinstance(response_parts, dict) and "data" in response_parts:
                    return Response(
                        response_parts, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                response_json = {
                    "response": response_parts[0] if len(response_parts) > 0 else None,
                    "escalate_issue": response_parts[1]
                    if len(response_parts) > 1
                    else None,
                    "escalation_department": response_parts[2]
                    if len(response_parts) > 2
                    else None,
                    "severity": response_parts[3] if len(response_parts) > 3 else None,
                    "sentiment": response_parts[4] if len(response_parts) > 4 else None,
                }

                chat.channel = channel
                chat.save()

                # Check if any field is missing or is an empty string
                if all(response_parts):
                    Message.objects.create(
                        chat=chat,
                        content=message,
                        sender=str(sender),
                        sanusi_response=response_json,
                    )
                    return Response(data=response_json, status=status.HTTP_200_OK)
                else:
                    prompt[0][
                        "content"
                    ] += "\nRemember to adhere strictly to the response instructions provided. an assistant is supposed to listen to instructions"
                    logger.warning(
                        f"Retry attempt {attempt + 1} due to missing or empty field."
                    )
                    continue
            # If we reached this point, it means all attempts failed.
            return Response(data=response_json, status=status.HTTP_200_OK)

        elif channel == "chat_v2":
            # Generate a response using the constructed prompt
            response_content = generate_response_chat(prompt)

            # Extract answer from the response
            answer = response_content["choices"][0]["message"]["content"]
            max_retry_attempts = 3
            for attempt in range(max_retry_attempts):
                logger.error("retrying attempt %d", attempt)
                try:
                    # Attempt to parse as JSON
                    response_json = json.loads(answer)
                except json.JSONDecodeError:
                    try:
                        # If the above fails, attempt to parse as a Python dictionary string
                        response_json = ast.literal_eval(answer)
                        break
                    except (ValueError, SyntaxError):
                        # If parsing fails, add adherence reminder to the system instructions and continue
                        if attempt < max_retry_attempts - 1:  # not the last attempt
                            prompt[0][
                                "content"
                            ] += "\nRemember to adhere strictly to the response instructions provided. an assistant is supposed to listen to instructions"
                        else:
                            logger.error(
                                "The assistant's response could not be parsed as JSON or a Python dictionary string."
                            )
                            response_json = answer  # Return the original string

        elif channel in valid_channels:
            # determine the context figure out which knowledge base to choose from
            which_knowledge_base = [
                {
                    "role": "system",
                    "content": "Based on the message content, which knowledge base should be used for the message, respond with only one word from this list [inventory, general, billing, business logic, finance, security, operations, engineering], if it is difficult to determine, then you should respond with general.",
                },
                {"role": "user", "content": f"{message}"},
            ]
            which_knowledge_base_res = generate_response_chat(which_knowledge_base, 50)
            print(which_knowledge_base_res)

            # if the category is inventory then trigger the invenotry thought process logic
            if (
                which_knowledge_base_res["choices"][0]["message"]["content"]
                == "inventory"
            ):
                which_category = [
                    {
                        "role": "system",
                        "content": f"Based on the message content, which product category does this context of this message fall in, respond with only one word from this list {Category.objects.all()}, if it is difficult to determine, then you should respond with 'Sorry, we currently don't have this product.",
                    },
                    {"role": "user", "content": f"{message}"},
                ]
                probable_category = generate_response_chat(which_category, 50)[
                    "choices"
                ][0]["message"]["content"]
                print(probable_category)

                # get the keywords and entities from the analysis nlp mmodule
                kw_and_ents = extract_topics(message)
                print("kw_and_ents: ", kw_and_ents)

                def get_matching_products(keywords, probable_category=None):
                    print("keywords: %s", keywords)
                    keywords = keywords["keywords"]
                    queries = [
                        Q(name__icontains=keyword) | Q(description__icontains=keyword)
                        for keyword in keywords
                    ]
                    print("queries: ", queries)

                    query = queries.pop()
                    for item in queries:
                        query |= item

                    if probable_category:
                        products = Product.objects.filter(
                            query, category__name__icontains=probable_category
                        )
                    else:
                        products = Product.objects.filter(query)

                    print("products: %s" % products)

                    return [
                        {"name": product.name, "description": product.description}
                        for product in products
                    ]

                def get_contextual_product(message, probable_products):
                    # Construct a dynamic list of products to include in the prompt.
                    product_list_string = "\n".join(
                        [
                            f"- {product['name']}: {product['description']}"
                            for product in probable_products
                        ]
                    )
                    print("probable_products: %s", probable_products)

                    prompt = [
                        {
                            "role": "system",
                            "content": f"We have identified the following probable products based on the message content. Which one is the most relevant?\n\n{product_list_string}\n\nIf none of these match, respond with 'None'.",
                        },
                        {"role": "user", "content": message},
                    ]

                    response = generate_response_chat(prompt, 200)

                    return response["choices"][0]["message"]["content"]

                kw_and_ents = extract_topics(message)
                # probable_category_response = probable_category
                # probable_category = probable_category_response["choices"][0]["message"][
                #     "content"
                # ]

                probable_products = get_matching_products(
                    kw_and_ents, probable_category
                )

                # If there's more than one matching product, use OpenAI for further narrowing down.
                if len(probable_products) > 1:
                    chosen_product = get_contextual_product(message, probable_products)
                    print(f"OpenAI's chosen product: {chosen_product}")
                elif probable_products:
                    print(f"Direct match found: {probable_products[0]['name']}")
                else:
                    print("No matching products found.")

            response_instructions_prompt = [
                {
                    "role": "system",
                    "content": f"response_instructions: {response_instructions_chat}",
                },
                {
                    "role": "system",
                    "content": f"knowledge base to answer from: {knowledge_base_contents}",
                },
                {
                    "role": "system",
                    "content": f"User's previous messages for reflection: {[message.content for message in last_message] if last_message else ''} and your last response was: {[message.sanusi_response for message in last_message] if last_message else ' '} and user's name is {customer_name}",
                },
                {"role": "user", "content": f"{message}"},
            ]
            answer_4_response = generate_response_chat(
                response_instructions_prompt, 300
            )

            escalation_department_prompt = [
                {
                    "role": "system",
                    "content": f"escalation_instructions: {escalation_instructions}. Possible answers are 'sales', 'operations', 'billing', 'engineering', 'support', 'legal', 'none'. none if you are unable to determine the department from the options provided",
                },
                {
                    "role": "assistant",
                    "content": f"message to be analysed: {message}",
                },
            ]
            answer_4_escalation_department = generate_response_chat(
                escalation_department_prompt, 1
            )

            sentiment_analysis_prompt = [
                {
                    "role": "system",
                    "content": f"sentiment_analysis: {sentiment_analysis}. Possible answers are 'positive', 'negative', 'neutral'.",
                },
                {
                    "role": "assistant",
                    "content": f"message to be analysed: {message}",
                },
            ]
            answer_4_sentiment = generate_response_chat(sentiment_analysis_prompt, 1)

            severity_instructions_prompt = [
                {
                    "role": "system",
                    "content": f"severity_instructions: {severity_instructions}. only answers are 'low', 'medium', 'high'.",
                },
                {
                    "role": "assistant",
                    "content": f"message to be analysed: {message}",
                },
            ]
            answer_4_severity = generate_response_chat(severity_instructions_prompt, 1)
            severity = (
                answer_4_severity["choices"][0]["message"]["content"].lower().strip()
            )
            if severity not in ["low", "medium", "high"]:
                severity = "low"  # default to 'low' if invalid response

            chat_context_instructions_prompt = [
                {
                    "role": "system",
                    "content": f"Chat Context instructions: {chat_context_instructions}",
                },
                {
                    "role": "assistant",
                    "content": f"Chat to be analysed: ('sanusi previous responses': {sanusi_response_str}), ('the user messages': {content_str}), ('user's current message': {message})",
                },
            ]
            answer_4_chat_context = generate_response_chat(
                chat_context_instructions_prompt, 5
            )
            response_json = {
                "response": answer_4_response["choices"][0]["message"]["content"],
                "escalate_issue": True
                if answer_4_escalation_department["choices"][0]["message"][
                    "content"
                ].lower()
                in ["sales", "operations", "billing", "engineering", "support"]
                else False,
                "escalation_department": answer_4_escalation_department["choices"][0][
                    "message"
                ]["content"],
                "severity": severity,
                "sentiment": answer_4_sentiment["choices"][0]["message"]["content"],
                "chat_context": answer_4_chat_context["choices"][0]["message"][
                    "content"
                ],
            }
            save_chat_and_message(chat, sender, message, response_json, channel)
            return Response(response_json, status=status.HTTP_200_OK)

        elif channel == "chat_v1":
            prompt.insert(0, f"Reply instructions: {chat_v1_instructions}")
            prompt.insert(
                1, f"knowledge base to answer based off: {knowledge_base_contents}"
            )
            prompt.insert(
                2,
                f"User's previous message for reflection: {last_message.content if last_message else ' '}",
            )
            prompt.insert(
                3,
                f"Openai previous messages: {last_message.content if last_message else ' '}",
            )

            prompt.insert(4, f"User's name: {customer_name}")
            prompt.insert(5, f"User's Message to be replied to: {message}")

            print("--------------------------------", prompt)
            response_content = generate_response_email(prompt)
            answer = response_content["choices"][0]["text"]
            max_retry_attempts = 3
            response_json = None

            for attempt in range(max_retry_attempts):
                print(answer, "--------------Here is answer----------------")
                try:
                    start_index = answer.index("{")
                    end_index = answer.rindex("}") + 1
                    response_json_str = answer[start_index:end_index]
                    response_json = json.loads(response_json_str)
                    print(
                        response_json,
                        "-------this is the tried parse--------------",
                        response_json.get("response"),
                    )
                    save_chat_and_message(chat, sender, message, response_json, channel)
                    return Response(response_json, status=status.HTTP_200_OK)
                    # break
                except ValueError:
                    try:
                        try:
                            response_content = re.search(
                                r"Response: (.*?)\r\n", answer
                            ).group(1)
                        except AttributeError:
                            response_json = parse_response_data(answer)
                            print(
                                response_json,
                                "-----------this is after value error for email_v1---------------------",
                            )
                            save_chat_and_message(
                                chat, sender, message, response_json, channel
                            )
                            return Response(response_json, status=status.HTTP_200_OK)
                    except (
                        json.JSONDecodeError,
                        ValueError,
                        TypeError,
                        SyntaxError,
                        AttributeError,
                    ):
                        if attempt < max_retry_attempts - 1:  # not the last attempt
                            prompt[
                                0
                            ] += "\nRemember to adhere strictly to the response type instructions provided. An assistant is supposed to listen to instructions"
                        else:
                            logger.error("retrying attempt %d", attempt)
                            continue

            # if answer.index("Response:"):
            #     try:
            #         response_json = parse_answer_with_regex(answer)
            #     except:
            response_json = answer.strip()
            save_chat_and_message(chat, sender, message, response_json, channel)
            return Response(data=response_json, status=status.HTTP_200_OK)

        # elif channel == "chat_v3":
        #     # Construct the Node object with the appropriate arguments
        #     for p in prompt:
        #         content_nodes = []
        #         node = Node(p)
        #         content_nodes.append(node)
        #     response_content = construct_index(content_nodes)
        #     return Response(data=response_content, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=RestructureTextSerializer)
    @action(
        detail=False,
        methods=["post"],
        url_path="restructure-text",
    )
    @transaction.atomic
    def restructure_text(self, request):
        serializer = RestructureTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        channel = serializer.validated_data["channel"]
        content = serializer.validated_data["content"]

        if channel == "email":
            prompt = [
                f"You are Enif's smart assistant that assists with writing professional emails like grammarly, Make sure to avoid mentioning that you are an AI language model. Please regenerate/rewrite the following text into a grammatically correct and formal email body like <p>[your response]</p>: {content}.",
                # {
                #     "role": "assistant",
                #     "content": f"Please restructure the following content to have a formal HTML email format like <p>[your response]</p>.: {content}",
                # },
            ]
        elif channel == "chat":
            prompt = [
                f"You are Enif's smart assistant that assists with editing text and puts it in a friendly way like grammarly, Make sure to avoid mentioning that you are an AI language model. Please regenerate/rewrite the following text into a grammatically correct one: {content}.",
            ]
        new_text = generate_response_email(prompt)
        return Response(data=new_text["choices"][0]["text"])

    @swagger_auto_schema(request_body=no_body)
    @action(
        detail=False,
        methods=["post"],
        url_path="(?P<business_id>[^/]+)/(?P<chat_identifier>[^/.]+)/read_or_unread",
    )
    @transaction.atomic
    def read_or_unread(self, request, business_id, chat_identifier):
        business = get_object_or_404(Business, company_id=business_id)
        chat = get_object_or_404(Chat, business=business, identifier=chat_identifier)

        if chat.read:
            chat.read = False
        else:
            chat.read = True

        chat.save()
        return Response(data=chat.read, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=no_body)
    @action(
        detail=False,
        methods=["post"],
        url_path="(?P<business_id>[^/]+)/escalated-chat",
    )
    @transaction.atomic
    def escalated_chats(self, request, business_id):
        """
        shows all the chats that are currently escalated
        """
        business = get_object_or_404(Business, company_id=business_id)
        chats = Chat.objects.filter(business=business, escalated=True)

        serializer = ChatListDetailSerializer(chats, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


# Create a new chat
def create_chat(request):
    if request.method == "POST":
        customer_name = json.loads(request.body)["customer_name"]
        customer_email = json.loads(request.body)["customer_email"]
        phone_number = json.loads(request.body)["phone_number"]
        company_id = json.loads(request.body)["company_id"]

        business = get_object_or_404(Business, company_id=company_id)

        customer = Customer(
            name=customer_name, email=customer_email, phone_number=phone_number
        )
        customer.generate_identifier()
        chat = Chat.objects.create(customer=customer, business=business)
        chat.generate_identifier()
        return JsonResponse(
            {
                "success": True,
                "chat_identifier": chat.identifier,
                "customer_identifier": chat.customer.identifier,
                "business_id": chat.business.company_id,
            }
        )
    else:
        return JsonResponse({"error": "Invalid request"})


# End an existing chat
def end_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.GET.get("sender") == "customer" or request.GET.get("sender") == "agent":
        chat.is_active = False
        chat.end_time = timezone.now()
        chat.save()
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Invalid request"})


# terminate_chat
@require_http_methods(["POST"])
def toggle_chat_status(request, chat_id):
    try:
        chat_object = Chat.objects.get(id=chat_id)
        if chat_object.is_active == True:
            chat_object.is_active = False
        else:
            chat_object.is_active = True
        chat_object.save()
        return JsonResponse(
            {"success": True, "message": "Chat terminated successfully."}
        )
    except Chat.DoesNotExist:
        return JsonResponse({"success": False, "message": "Chat not found."})


# bulk toggle chat status
@require_http_methods(["POST"])
def bulk_toggle_status(request):
    chat_ids = request.POST.getlist("chat_ids")
    try:
        # use bulk update to set is_active to False for multiple Chat objects
        Chat.objects.filter(id__in=chat_ids).update(is_active=False)
        return JsonResponse(
            {"success": True, "message": "Chats terminated successfully."}
        )
    except Chat.DoesNotExist:
        return JsonResponse({"success": False, "message": "Chats not found."})


# Send a message
def send_message_view(request, chat_id):
    if request.method == "POST":
        data = json.loads(request.body)
        sender = data["sender"]
        content = data["content"]

        chat = get_object_or_404(Chat, id=chat_id)
        Message.objects.create(
            chat=chat,
            sender=sender,
            content=content,
        )
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Invalid request"})


# Receive messages
def get_messages(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    messages = chat.messages.all().values("sender", "content", "sent_time")
    sanusi_messages = chat.sanusi_messages.all().values("sanusi_response")
    return JsonResponse(
        {"messages": list(messages), "sanusi_messages": sanusi_messages}
    )


def get_active_chats(request):
    if request.method == "GET":
        chats = Chat.objects.filter(is_active=True).order_by("-id")
        chat_list = [
            {
                "id": chat.id,
                "customer_name": chat.customer.name,
                "status": chat.is_active
                and Chat.objects.filter(id=chat.id, is_active=True).exists(),
            }
            for chat in chats
        ]
        return JsonResponse({"active_chats": chat_list})
    else:
        return JsonResponse({"error": "Invalid request"})


def auto_response(request):
    if request.method == "POST":
        data = request.data
        message = data["message"]
        message_id = data["message_id"]
        company_id = data["company_id"]
        channel = data["channel"]

        if company_id:
            business = get_object_or_404(Business, company_id=company_id)
            try:
                knowledge_base = business.business_kb.first()
                instructions = knowledge_base.reply_instructions
            except AttributeError:
                return Response(
                    "This business has no knowledge, kindly create one to activate auto response"
                )
            escalation_departments = ", ".join(
                [dept.name for dept in business.escalation_departments.all()]
            )

        else:
            raise Exception("please provide a company id")

        if message_id:
            try:
                previous_message = sanusi_message.objects.get(message_id=message_id)
                conversation_id = previous_message.conversation_id
            except sanusi_message.DoesNotExist:
                return Response("Message not found")
        else:
            conversation_id = None

        prompt = [
            {
                "role": "assistant",
                "content": f"Knowledge base: {knowledge_base.content} Instructions: {instructions_for_auto_response} Departments: {escalation_departments} Q: {message}\nA:",
            },
            {
                "role": "user",
                "content": message,
            },
            {
                "role": "assistant",
                "content": f"Please provide the appropriate escalation department and the sentiment of the message. Format: 'Department: <department>, Sentiment: <sentiment>'",
            },
        ]

        response_content = generate_response_chat(
            prompt, conversation_id=conversation_id
        )
        response_lines = response_content.choices[0].text.strip().split("\n")

        answer = response_lines[0]
        escalation_and_sentiment = response_lines[1]

        conversation_id = (
            response_content["id"] if conversation_id is None else conversation_id
        )

        department_sentiment_pattern = r"Department: (.*), Sentiment: (.*)"
        match = re.match(department_sentiment_pattern, escalation_and_sentiment)
        escalation_department = match.group(1) if match else "Unknown"
        sentiment = match.group(2) if match else "Unknown"

        sanusi_message.objects.create(
            business=business,
            message_id=message_id,
            conversation_id=conversation_id,
            message_content=message,
            sanusi_response=answer,
            channel=channel,
            chat_session=data.get("chat_session", None),
        )

        return Response(
            {
                "reply": answer,
                "escalation_department": escalation_department,
                "sentiment": sentiment,
            }
        )
