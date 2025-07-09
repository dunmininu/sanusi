from .base import BaseAgent
from sanusi.views import generate_response_chat


class SeverityAgent(BaseAgent):
    """Determine message severity."""

    def __init__(self, instructions: str):
        self.instructions = instructions

    def run(self, message: str) -> str:
        prompt = [
            {"role": "system", "content": f"{self.instructions}"},
            {"role": "assistant", "content": f"message to be analysed: {message}"},
        ]
        response = generate_response_chat(prompt, 1)
        value = response["choices"][0]["message"]["content"].lower().strip()
        if value not in {"low", "medium", "high"}:
            return "low"
        return value
