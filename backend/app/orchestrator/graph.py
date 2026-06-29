"""
LangGraph orchestrator. (Phase 5)

Decides which agents run, in what order, and passes state between them, then
synthesizes their views with explainability. Add agents one at a time; the graph
coordinates them. Keep risk/execution deterministic downstream of the graph.

TODO: define state schema, nodes (one per agent), edges, and the synthesis node.
"""

def build_graph():
    raise NotImplementedError("Phase 5: assemble the LangGraph multi-agent graph")
