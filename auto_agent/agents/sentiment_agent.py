from .base import BaseAgent
from sanusi.views import generate_response_chat


class SentimentAgent(BaseAgent):
    """Perform sentiment analysis on a message."""

    def __init__(self, instructions: str):
        self.instructions = instructions

    def run(self, message: str) -> str:
        prompt = [
            {"role": "system", "content": f"{self.instructions}"},
            {"role": "assistant", "content": f"message to be analysed: {message}"},
        ]
        response = generate_response_chat(prompt, 1)
        return response["choices"][0]["message"]["content"].lower().strip()
