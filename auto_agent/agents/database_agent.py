from typing import Any, Callable
from .base import BaseAgent


class DatabaseQueryAgent(BaseAgent):
    """Agent for executing database queries using Django's ORM."""

    def __init__(self, query_func: Callable[..., Any]):
        self.query_func = query_func

    def run(self, *args: Any, **kwargs: Any) -> Any:
        return self.query_func(*args, **kwargs)
