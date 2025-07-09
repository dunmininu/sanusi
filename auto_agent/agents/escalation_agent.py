from .base import BaseAgent
from sanusi.views import generate_response_chat


class EscalationAgent(BaseAgent):
    """Determine if and where to escalate the issue."""

    def __init__(self, instructions: str):
        self.instructions = instructions

    def run(self, message: str) -> str:
        prompt = [
            {
                "role": "system",
                "content": (
                    f"escalation_instructions: {self.instructions}. "
                    "Possible answers are 'sales', 'operations', 'billing', "
                    "'engineering', 'support', 'none'."
                ),
            },
            {"role": "assistant", "content": f"message to be analysed: {message}"},
        ]
        response = generate_response_chat(prompt, 1)
        return response["choices"][0]["message"]["content"].lower().strip()
