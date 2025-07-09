from typing import Any, Dict, Optional
from .base import BaseAgent
from .database_agent import DatabaseQueryAgent
from .api_agent import APICallAgent


class AccountAuditAgent(BaseAgent):
    """Analyze a user's account data for potential issues."""

    def __init__(
        self,
        db_agent: DatabaseQueryAgent,
        api_agent: Optional[APICallAgent] = None,
    ) -> None:
        self.db_agent = db_agent
        self.api_agent = api_agent

    def run(self, user_id: Any) -> Dict[str, Any]:
        user = self.db_agent.run(id=user_id).first()
        if user is None:
            raise ValueError("User not found")

        api_data: Dict[str, Any] = {}
        if self.api_agent is not None:
            try:
                api_data = self.api_agent.run(f"users/{user_id}")
            except Exception as exc:  # noqa: BLE001
                api_data = {"error": str(exc)}

        return self._analyze(user, user_id, api_data)

    def _analyze(self, user: Any, user_id: Any, api_data: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        if not getattr(user, "is_active", True):
            issues.append("inactive user")
        if not getattr(user, "email", ""):
            issues.append("missing email")
        if api_data.get("suspended"):
            issues.append("account suspended")

        return {
            "user_id": str(getattr(user, "id", user_id)),
            "issues": issues,
            "api_data": api_data,
        }
