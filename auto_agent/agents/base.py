class BaseAgent:
    """Base class for all agents."""

    def run(self, **kwargs):
        raise NotImplementedError("Agents must implement run()")
