import html
import json
import logging

from typing import List, Tuple
from sanusi.views import generate_response_chat
from sanusi.utils import save_chat_and_message
from auto_agent import (
    AgentManager,
    ResponseAgent,
    EscalationAgent,
    SentimentAgent,
    SeverityAgent,
    ChatContextAgent,
)

from .models import Chat, Message, Customer
from django.shortcuts import get_object_or_404
from sanusi_backend.utils.error_handler import LogicException

logger = logging.getLogger(__name__)

# Load prompt instructions
with open("sanusi/instructions.json") as json_file:
    _json_data = json.load(json_file)

email_v1_instructions = _json_data["email_v1_instructions"]
response_instructions = _json_data["response_instructions"]
escalation_instructions = _json_data["escalation_instructions"]
sentiment_analysis = _json_data["sentiment_analysis"]
severity_instructions = _json_data["severity_instructions"]
response_instructions_chat = _json_data["response_instructions_chat"]
chat_context_instructions = _json_data["chat_context_instructions"]
valid_channels = ["chat", "whatsapp", "telegram", "instagram", "tiktok"]


class AutoResponseService:
    """Service layer handling OpenAI auto response logic."""

    def __init__(self, business):
        self.business = business
        self.manager = AgentManager()
        self.manager.register(
            "response",
            ResponseAgent(response_instructions_chat),
        )
        self.manager.register(
            "escalation",
            EscalationAgent(escalation_instructions),
        )
        self.manager.register(
            "sentiment",
            SentimentAgent(sentiment_analysis),
        )
        self.manager.register(
            "severity",
            SeverityAgent(severity_instructions),
        )
        self.manager.register(
            "context",
            ChatContextAgent(chat_context_instructions),
        )

    # Internal helpers -----------------------------------------------------
    def get_knowledge_base_contents(self) -> List[str]:
        kb = self.business.business_kb.all()
        if not kb:
            raise LogicException(
                "This business has no knowledge base, kindly create one to activate auto response"
            )
        return [item.cleaned_data for item in kb]

    def history(self, chat: Chat) -> Tuple[str, str, list]:
        all_messages = (
            Message.objects.filter(chat=chat)
            .order_by("-sent_time")
            .values_list("sanusi_response", "content")[:10]
        )
        result = list(all_messages)
        sanusi_response = [item[0] for item in result if item[0] is not None]
        content = [item[1] for item in result if item[1] is not None]
        last_message = Message.objects.filter(chat=chat, sender="customer")[:2]
        return ", ".join(sanusi_response), ", ".join(content), list(last_message)

    @staticmethod
    def html_format(text: str) -> str:
        html_text = html.escape(text).replace("\n", "<br/>")
        return f"<p>{html_text}</p>"

    def get_chat(
        self,
        channel: str,
        chat_identifier: str,
        customer_identifier: str | None = None,
        customer_name: str | None = None,
        customer_email: str | None = None,
    ) -> Chat:
        """Retrieve or create :class:`Chat` and optional :class:`Customer`."""
        if channel in {"email_v1", "email_v2", "email"}:
            customer, created = Customer.objects.get_or_create(
                identifier=customer_identifier,
                defaults={"name": customer_name or "", "email": customer_email},
            )
            if not created and (customer.name != customer_name or customer.email != customer_email):
                customer.name = customer_name
                customer.email = customer_email
                customer.save()

            chat, _ = Chat.objects.get_or_create(
                business=self.business,
                identifier=chat_identifier,
                defaults={"customer": customer},
            )
            return chat

        return get_object_or_404(Chat, business=self.business, identifier=chat_identifier)

    # Public API -----------------------------------------------------------
    def handle_email_v1(
        self,
        chat: Chat,
        message: str,
        customer_name: str,
        sender: str,
        channel: str,
    ) -> dict:
        """Generate auto response for ``email_v1`` channel."""
        kb_contents = self.get_knowledge_base_contents()
        sanusi_response_str, content_str, last_message = self.history(chat)

        response_instructions_prompt = [
            {"role": "system", "content": f"response_instructions: {response_instructions}"},
            {"role": "system", "content": f"knowledge base to answer from: {kb_contents}"},
            {
                "role": "system",
                "content": (
                    "User's previous messages for reflection: "
                    f"{last_message[0].content if last_message else ''} "
                    "and your last response was: "
                    f"{last_message[0].sanusi_response if last_message else ' '} and "
                    "user's name is "
                    f"{customer_name}"
                ),
            },
            {"role": "user", "content": message},
        ]
        answer_4_response = generate_response_chat(response_instructions_prompt, 300)

        escalation_department_prompt = [
            {
                "role": "system",
                "content": (
                    f"escalation_instructions: {escalation_instructions}. "
                    "Possible answers are 'sales', 'operations', 'billing', "
                    "'engineering', 'none'. none if you are unable to determine "
                    "the department from the options provided"
                ),
            },
            {"role": "assistant", "content": f"message to be analysed: {message}"},
        ]
        answer_4_escalation_department = generate_response_chat(escalation_department_prompt, 1)

        sentiment_analysis_prompt = [
            {
                "role": "system",
                "content": (
                    f"sentiment_analysis: {sentiment_analysis}. "
                    "Possible answers are 'positive', 'negative', 'neutral'."
                ),
            },
            {"role": "assistant", "content": f"message to be analysed: {message}"},
        ]
        answer_4_sentiment = generate_response_chat(sentiment_analysis_prompt, 1)

        severity_instructions_prompt = [
            {
                "role": "system",
                "content": (
                    f"severity_instructions: {severity_instructions}. "
                    "only answers are 'low', 'medium', 'high'."
                ),
            },
            {"role": "assistant", "content": f"message to be analysed: {message}"},
        ]
        answer_4_severity = generate_response_chat(severity_instructions_prompt, 1)
        severity = answer_4_severity["choices"][0]["message"]["content"].lower().strip()
        if severity not in ["low", "medium", "high"]:
            severity = "low"

        chat_context_instructions_prompt = [
            {
                "role": "system",
                "content": f"Chat Context instructions: {chat_context_instructions}",
            },
            {
                "role": "assistant",
                "content": (
                    f"Chat to be analysed: ('sanusi previous responses': {sanusi_response_str}), "
                    f"('the user messages': {content_str}), ('user's current message': {message})"
                ),
            },
        ]
        answer_4_chat_context = generate_response_chat(chat_context_instructions_prompt, 1)

        text = answer_4_response["choices"][0]["message"]["content"]
        response_html = self.html_format(text)

        response_json = {
            "response": response_html,
            "escalate_issue": (
                True
                if answer_4_escalation_department["choices"][0]["message"]["content"].lower()
                in ["sales", "operations", "billing", "engineering", "support"]
                else False
            ),
            "escalation_department": answer_4_escalation_department["choices"][0]["message"][
                "content"
            ],
            "severity": severity,
            "sentiment": answer_4_sentiment["choices"][0]["message"]["content"],
            "chat_context": answer_4_chat_context["choices"][0]["message"]["content"],
        }
        save_chat_and_message(chat, sender, message, response_json, channel)
        return response_json

    def handle_chat_v2(
        self,
        chat: Chat,
        message: str,
        customer_name: str,
        sender: str,
        channel: str,
    ) -> dict:
        """Generate auto response for ``chat_v2`` channel."""
        kb_contents = self.get_knowledge_base_contents()
        sanusi_response_str, content_str, _ = self.history(chat)

        response_text = self.manager.run(
            "response",
            message=message,
            knowledge_base=kb_contents,
            history=content_str,
            customer_name=customer_name,
        )

        escalation_department = self.manager.run("escalation", message=message)
        sentiment = self.manager.run("sentiment", message=message)
        severity = self.manager.run("severity", message=message)
        context = self.manager.run(
            "context",
            sanusi_response=sanusi_response_str,
            content=content_str,
            message=message,
        )

        response_json = {
            "response": self.html_format(response_text),
            "escalate_issue": escalation_department in [
                "sales",
                "operations",
                "billing",
                "engineering",
                "support",
            ],
            "escalation_department": escalation_department,
            "severity": severity,
            "sentiment": sentiment,
            "chat_context": context,
        }

        save_chat_and_message(chat, sender, message, response_json, channel)
        return response_json
