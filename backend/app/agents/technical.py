"""
TechnicalAgent — the FIRST agent to build. (Phase 4)

Reachable from the web app and Telegram. Flow:
  ticker -> call engine for real indicators/backtest -> LLM interprets numbers
  -> returns an evidence-backed English analysis. NO execution on this path.

This is the smallest proof of the whole agentic+algo pattern. Build it first.
"""
from app.agents.base import Agent


class TechnicalAgent(Agent):
    name = "technical"

    def run(self, context: dict) -> dict:
        raise NotImplementedError("Phase 4: call engine tools, then LLM interprets")
