from .base import BaseAgent
from sanusi.views import generate_response_chat


class ResponseAgent(BaseAgent):
    """Generate a full response based on chat history and knowledge base."""

    def __init__(self, instructions: str):
        self.instructions = instructions

    def run(
        self,
        message: str,
        knowledge_base: list[str],
        history: str,
        customer_name: str,
        max_tokens: int = 300,
    ) -> str:
        prompt = [
            {"role": "system", "content": f"response_instructions: {self.instructions}"},
            {"role": "system", "content": f"knowledge base to answer from: {knowledge_base}"},
            {
                "role": "system",
                "content": (
                    f"User's previous messages for reflection: {history} "
                    f"and user's name is {customer_name}"
                ),
            },
            {"role": "user", "content": message},
        ]
        response = generate_response_chat(prompt, max_tokens)
        return response["choices"][0]["message"]["content"]
