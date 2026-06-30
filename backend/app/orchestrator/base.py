from abc import ABC, abstractmethod

class BaseOrchestrator(ABC):
    @abstractmethod
    def orchestrate(self, symbol: str, proposed_trade: dict = None) -> dict:
        """
        Runs the orchestrator flow for a given symbol and optional proposed trade context.
        Returns a synthesized state report containing reviews from all specialist agents.
        """
        pass
