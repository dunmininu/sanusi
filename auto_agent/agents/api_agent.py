from typing import Any, Dict
import requests
from .base import BaseAgent


class APICallAgent(BaseAgent):
    """Agent for making HTTP API calls."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def run(
        self,
        endpoint: str,
        method: str = "GET",
        timeout: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return {"text": response.text}
