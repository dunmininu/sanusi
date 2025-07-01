# import requests
# import json
# import ast
import time

from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status, serializers, generics, mixins

import openai
from llama_index import LLMPredictor, PromptHelper, GPTVectorStoreIndex
from langchain import OpenAI as oai

from chat.models import Message

# from .models import Message, ChannelTypes
from .serializers import (
    MessageInputSerializer,
    AllMessagesSerializer,
    MessageSerializer,
)

from business.private.models import KnowledgeBase

# Create your views here.
openai.api_key = settings.OPENAI_KEY


def construct_index(knowledge_base):
    max_input_size = 4096
    num_outputs = 256
    max_chunk_overlap = 0.2
    chunk_size_limit = 600

    prompt_helper = PromptHelper(
        max_input_size,
        num_outputs,
        max_chunk_overlap,
        chunk_size_limit=chunk_size_limit,
    )

    llm_predictor = LLMPredictor(
        llm=oai(
            temperature=0,
            model_name="text-davinci-003",
            max_tokens=num_outputs,
            openai_api_key=settings.OPENAI_KEY,
        )
    )

    index = GPTVectorStoreIndex(
        documents=knowledge_base,
        llm_predictor=llm_predictor,
        prompt_helper=prompt_helper,
    )

    return index


def generate_response_chat(prompt, max_tokens):
    response = None
    retries = 0
    while retries < 3:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=prompt,
                max_tokens=max_tokens,
                n=1,
                temperature=0.6,  # adjust as needed
                frequency_penalty=1.29,
                presence_penalty=1.02,
            )
            break
        except Exception as e:
            print(f"Error: {str(e)}. Retrying in 3 seconds...")
            time.sleep(3)
            retries += 1

    if response is None:
        return Response({"data": "Failed to generate response after double retries."})

    return response


def generate_response_chat_v2(prompt):
    field_prompts = [
        "Please provide a well-structured response based on the knowledge base provided. "
        "Do not instruct the user to send any emails or make any phone calls. Your sole "
        "responsibility is to respond as instructed and assure the user that the issue has "
        "been escalated, if applicable. Always maintain a courteous and professional demeanor "
        "throughout your interactions. If there are requests beyond your knowledge base, "
        "you should not mention that you're an AI.",
        'Should the issue be escalated? Type "true" if it should be '
        'escalated, or "false" if it should not.',
        "If the issue should be escalated, type the name of the department it "
        'should be escalated to: "sales", "operations", "billing", or "engineering". '
        "If the issue should not be escalated, leave it empty.",
        'Type the severity of the issue using only one word: "low", "medium", or "high".',
        "Type the sentiment of the user's message using only one word: "
        '"positive", "negative", or "neutral".',
    ]
    responses = []
    for field_prompt in field_prompts:
        prompt_text = (
            "\n".join([message["content"] for message in prompt]) + "\n" + field_prompt
        )
        response_text = ""
        max_retries = 3
        retries = 0
        while not response_text.strip() and retries < max_retries:
            try:
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=prompt_text,
                    max_tokens=250,  # adjust as needed
                    temperature=0.4,  # adjust as needed
                    frequency_penalty=0.3,
                    presence_penalty=0.7,
                )
                response_text = response.choices[0].text.strip()
                if response_text.strip():
                    responses.append(response_text)
                else:
                    print(f"Empty response received. Retrying {retries+1}/3...")
                    retries += 1
            except Exception as e:
                print(f"Error: {str(e)}. Retrying in 3 seconds...")
                time.sleep(3)
    return responses


def generate_response_email(prompt):
    response = None
    retries = 0
    prompt_text = ", ".join([i for i in prompt])

    while retries < 3:
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt_text,
                max_tokens=250,
                n=1,
                temperature=0.6,  # adjust as needed
                frequency_penalty=1.29,
                presence_penalty=1.02,
            )
            break
        except Exception as e:
            print(f"Error: {str(e)}. Retrying in 3 seconds...")
            time.sleep(3)
            retries += 1

    if response is None:
        return Response({"data": "Failed to generate response after double retries."})

    return response


def generate_response_email_v2(prompt):
    field_prompts = [
        "Please provide a well-structured response that could fit "
        "into an email body and would have a closing remark. Do not instruct "
        "the user to send any emails or make any phone calls. Your sole responsibility is "
        "to respond as instructed and assure the user that the issue has "
        "been escalated, if applicable. Always maintain a courteous "
        "and professional demeanor throughout your interactions.",
        'Should the issue be escalated? Type the word "true" if it should '
        'be escalated, or "false" if it should not.',
        "If the issue should be escalated, type the name of the department "
        'it should be escalated to: "sales", "operations", "billing", '
        'or "engineering". If the issue should not be escalated, type "null".',
        'Type the severity of the issue using only one word: "low", "medium", or "high".',
        "Type the sentiment of the user's message "
        'using only one word: "positive", '
        '"negative", or "neutral".',
    ]
    responses = []
    for field_prompt in field_prompts:
        prompt_text = (
            "\n".join([message["content"] for message in prompt]) + "\n" + field_prompt
        )
        response_text = ""
        max_retries = 3
        retries = 0
        while not response_text.strip() and retries < max_retries:
            try:
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=prompt_text,
                    max_tokens=250,  # adjust as needed
                    temperature=0.0,  # adjust as needed
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                response_text = response.choices[0].text.strip()
                if response_text.strip():
                    responses.append(response_text)
                else:
                    print(f"Empty response received. Retrying {retries+1}/3...")
                    retries += 1
            except Exception as e:
                print(f"Error: {str(e)}. Retrying in 3 seconds...")
                time.sleep(3)
    return responses

    # if type(response["choices"][0]["message"]["content"]) is not dict:
    #     data = response["choices"][0]["message"]["content"]
    #     reply_str = data.split("\n\n")[-1]
    #     reply = json.loads(reply_str)

    #     print(reply)
    #     return reply
    # else:

    # return ast.literal_eval(response_data["choices"][0]["message"]["content"])
    # return ast.literal_eval(response_data["error"])


def generate_response(prompt, tokens=200, temperature=0.5):
    """
    This function uses OpenAI's GPT-3 to generate a response based on a given prompt.

    Parameters:
    - prompt: A string which acts as the starting point
    for the AI to generate a response.
    - tokens: The maximum number of tokens to generate. Fewer tokens may be generated
    if the total cost of tokens exceeds the model’s maximum limit.
    - temperature: This parameter controls the randomness of the AI’s output. A
    higher value like 0.8 makes the output more random, while a lower value like
    0.2 makes the output more deterministic.

    Returns: A string which is the AI's response.
    """
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=tokens,
        temperature=temperature,
    )
    return response.choices[0].text.strip()


def structure_response(response, escalate_issue, escalation_department, severity, sentiment):
    """
    This function structures a response in the desired format.

    Parameters:
    - response: The AI-generated response.
    - escalate_issue: A boolean indicating whether the issue needs to be escalated.
    - escalation_department: The department to which the issue should be escalated.
        This is 'null' if escalate_issue is False.
    - severity: The severity of the issue, which can be 'low', 'medium', or 'high'.
    - sentiment: The sentiment of the response, which can be 'positive',
        'negative', or 'neutral'.

    Returns: A dictionary representing the structured response.
    """
    return {
        "response": f"<p>{response}</p>",
        "escalate_issue": str(escalate_issue).lower(),
        "escalation_department": escalation_department,
        "severity": severity,
        "sentiment": sentiment,
    }


class SanusiMessageChannelViewSet(mixins.CreateModelMixin, generics.GenericAPIView):
    serializer_class = MessageInputSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # name = data.get("name")
        message = data["message"]
        channel = data["channel"]
        knowledge_base_prompt = data.get("knowledge_base")
        business_id = data.get("business_id")
        knowledge_id = data.get("knowledge_id")
        instructions = data.get("instructions")

        try:
            message_obj = Message.objects.get(id=data["message_id"])
            if not knowledge_base_prompt and message_obj:
                knowledge_base = message_obj.business.business_kb.first()
                prompt = [
                    {
                        "role": "user",
                        "content": message,
                    }
                ]
                response = generate_response_chat(prompt)
            else:
                if not knowledge_id:
                    raise serializers.ValidationError("Invalid request data")

                try:
                    knowledge_base = KnowledgeBase.objects.get(id=knowledge_id)
                except KnowledgeBase.DoesNotExist:
                    raise serializers.ValidationError("Knowledge base not found")

                prompt = [
                    {
                        "role": "assistant",
                        "content": f"""
                            Knowledge base:{knowledge_base.content} 
                            Instructions: {instructions} Q:{message}\nA:
                        """,
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ]
                response = generate_response_chat(prompt)
                conversation_id = response["id"]  # noqa F841
        except ObjectDoesNotExist:
            if not knowledge_base_prompt:
                raise serializers.ValidationError("Invalid request data")

            knowledge_base = knowledge_base_prompt
            prompt = [
                {"role": "assistant", "content": f"{knowledge_base}\nQ:{message}\nA:"},
                {"role": "user", "content": message},
            ]

            response = generate_response_chat(prompt)

        chat_session = [
            {"role": "user", "content": message},
            {
                "role": "assistant",
                "content": response["choices"][0]["message"]["content"],
            },
        ]

        if message_obj:
            message_obj.chat_session = chat_session
            message_obj.sanusi_response = chat_session[-1]["content"]
            message_obj.save()
        else:
            Message.objects.create(
                business_id=business_id,
                id=data["message_id"],
                message_content=message,
                sanusi_response=chat_session[-1]["content"],
                sender_email="",
                chat_session=chat_session,
                channel=channel,
            )

        return Response(
            {"response": chat_session[-1]["content"]}, status=status.HTTP_201_CREATED
        )


@csrf_exempt
@api_view(["GET"])
def get_single_chat_session(request, message_id):
    try:
        message_obj = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({"message": "Message not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = MessageSerializer(message_obj)

    # Return chat session
    return Response(serializer.data)


@api_view(["GET"])
def get_messages(request):
    messages = Message.objects.all()
    serializer = AllMessagesSerializer(messages, many=True)
    return Response(serializer.data)
