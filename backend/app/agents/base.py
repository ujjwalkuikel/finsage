"""
Agent base. (Phase 4+) — see docs/02 §2-3.

THE RULE: agents reason and call the deterministic engine/validation as TOOLS.
An agent never computes an indicator or sets risk itself — it asks the engine and
interprets the result. Agents import the engine; the engine never imports agents.
"""
from abc import ABC, abstractmethod


class Agent(ABC):
    name = "base"

    @abstractmethod
    def run(self, context: dict) -> dict:
        """Take context, optionally call engine tools, return a structured,
        explainable result (conclusion + evidence + which inputs were used)."""
        ...
