class AgentManager:
    """Register and run AI agents."""

    def __init__(self):
        self._agents = {}

    def register(self, name, agent):
        self._agents[name] = agent

    def run(self, name, **kwargs):
        if name not in self._agents:
            raise ValueError(f"Agent {name} is not registered")
        return self._agents[name].run(**kwargs)
