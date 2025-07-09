from .base import BaseAgent
from sanusi.views import generate_response_chat


class ChatContextAgent(BaseAgent):
    """Summarize the current chat context."""

    def __init__(self, instructions: str):
        self.instructions = instructions

    def run(self, sanusi_response: str, content: str, message: str) -> str:
        prompt = [
            {"role": "system", "content": f"Chat Context instructions: {self.instructions}"},
            {
                "role": "assistant",
                "content": (
                    f"Chat to be analysed: ('sanusi previous responses': {sanusi_response}), "
                    f"('the user messages': {content}), ('user's current message': {message})"
                ),
            },
        ]
        response = generate_response_chat(prompt, 1)
        return response["choices"][0]["message"]["content"].lower().strip()
