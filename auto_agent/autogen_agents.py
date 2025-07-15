"""Utilities for setting up AutoGen agents with custom helpers."""

from __future__ import annotations

import os
from typing import Annotated, Any, Dict, Literal, Tuple

import autogen
from django.conf import settings
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.utils import timezone
import requests


class AutogenAgents:
    """Create assistant and user proxy agents with registered helper functions."""

    def __init__(self) -> None:
        self.token_cache: Dict[str, Dict[str, Any]] = {}
        self.chatbot, self.user_proxy = self._initialize_agents()
        self._register_functions()

    def _initialize_agents(self) -> Tuple[autogen.AssistantAgent, autogen.UserProxyAgent]:
        config_list = [
            {
                "model": "gpt-4o",
                "api_key": "none",
                "base_url": f"{settings.BASE_URL}/openai-proxy/",
                "http_client": autogen.ProxyClient(http2=True, verify=False),
            }
        ]
        llm_config = {
            "cache_seed": 42,
            "config_list": config_list,
            "timeout": 600,
        }
        chatbot = autogen.AssistantAgent(
            name="chatbot",
            system_message=(
                "For performing actions, only use the functions you have been provided with and "
                "only call the functions if its needed. If you need additional data you can call "
                "the registered functions with the required parameters. and finally "
                "Reply TERMINATE when the task is done."
            ),
            llm_config=llm_config,
        )
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
        )
        return chatbot, user_proxy

    def _register_functions(self) -> None:
        """Register utility functions accessible to the LLM."""

        @self.user_proxy.register_for_execution()
        @self.chatbot.register_for_llm(description="Get a key from the environment variables")
        def get_key_from_env(
            key: Annotated[str, "Key to get from the environment variables"],
        ) -> str | None:
            return os.getenv(key)

        @self.user_proxy.register_for_execution()
        @self.chatbot.register_for_llm(
            description="Try fetch a token from the cache by the group_id"
        )
        def get_token_from_cache(
            group_id: Annotated[str, "Group ID to get the token for"],
        ) -> str | None:
            token_data = self.token_cache.get(group_id)
            if not token_data:
                return None
            expiry_time = token_data.get("expires_at")
            if expiry_time and timezone.now() >= expiry_time:
                self.token_cache.pop(group_id, None)
                return None
            return token_data.get("token")

        @self.user_proxy.register_for_execution()
        @self.chatbot.register_for_llm(
            description="Store or replace a token in the cache by the group_id"
        )
        def store_token_in_cache(
            group_id: Annotated[str, "Group ID to store the token for"],
            token: Annotated[str, "Token to be stored"],
            expires_in_seconds: Annotated[int, "Seconds until the token expires"] = 3600,
        ) -> str:
            expiry_time = timezone.now() + timezone.timedelta(seconds=expires_in_seconds)
            self.token_cache[group_id] = {"token": token, "expires_at": expiry_time}
            return "Token stored in cache"

        @self.user_proxy.register_for_execution()
        @self.chatbot.register_for_llm(description="Run a database query to fetch a user by id")
        def query_user(user_id: Annotated[int, "ID of the user"]) -> Dict[str, Any]:
            User = get_user_model()
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return {"error": "User not found"}
            return model_to_dict(user)

        @self.user_proxy.register_for_execution()
        @self.chatbot.register_for_llm(
            description="Do an Api call according to the given parameters"
        )
        def api_call_for_llm(
            end_point: Annotated[str, "Endpoint to hit API"],
            method: Annotated[Literal["GET", "POST", "PUT", "DELETE"], "HTTP method"],
            body: Annotated[Dict[str, Any] | None, "Data to be sent to the API"] = None,
            query_params: Annotated[
                Dict[str, Any] | None, "Optional Query params to be sent to the API"
            ] = None,
            headers: Annotated[Dict[str, Any] | None, "Headers to be sent to the API"] = None,
        ) -> Dict[str, Any]:
            try:
                if method in ["POST", "PUT", "PATCH"]:
                    response = requests.request(
                        method,
                        end_point,
                        json=body,
                        headers=headers or {},
                        verify=False,
                    )
                else:
                    response = requests.request(
                        method,
                        end_point,
                        params=query_params or {},
                        headers=headers or {},
                        verify=False,
                    )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as exc:
                return {"error": str(exc)}
            except ValueError:
                return {"text": response.text}

        @self.user_proxy.register_for_execution()
        @self.chatbot.register_for_llm(description="Analyze a user account for potential issues")
        def audit_user_account(
            user_id: Annotated[int, "ID of the user to audit"],
        ) -> Dict[str, Any]:
            user_data = query_user(user_id)
            if "error" in user_data:
                return user_data
            api_data = api_call_for_llm(f"users/{user_id}", method="GET")
            issues = []
            if not user_data.get("is_active", True):
                issues.append("inactive user")
            if not user_data.get("email"):
                issues.append("missing email")
            if api_data.get("suspended"):
                issues.append("account suspended")
            return {"user_id": user_id, "issues": issues, "api_data": api_data}


def initialize_autogen_agents() -> Tuple[autogen.AssistantAgent, autogen.UserProxyAgent]:
    """Return freshly initialized AutoGen agents."""

    agents = AutogenAgents()
    return agents.chatbot, agents.user_proxy
