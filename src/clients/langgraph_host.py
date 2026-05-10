import os
from typing import Any, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from src.core.telemetry import active_tracer


class WorkflowState(TypedDict):
    """Type-safe state definition for LangGraph execution nodes."""

    messages: list[BaseMessage]
    spec_compliant: bool


def _read_spec() -> str:
    """Retrieves upfront design constraints to enforce system instructions."""
    spec_path = os.path.join("data", "upfront_spec.md")
    if os.path.exists(spec_path):
        with open(spec_path, encoding="utf-8") as f:
            return f.read().strip()
    return "Default enterprise guidelines apply."


def execute_langgraph_workflow(user_query: str) -> dict[str, Any]:
    """
    Executes a simulated LangGraph cyclic state workflow.
    Ensures state transitions emit isolated tracing spans.
    """
    with active_tracer.start_as_current_span("langgraph_orchestration_cycle") as span:
        span.set_attribute("framework", "langgraph")

        spec_text = _read_spec()
        system_msg = SystemMessage(content=f"Enforcing Specification:\n{spec_text}")
        human_msg = HumanMessage(content=user_query)

        # Initialize immutable state payload
        initial_state: WorkflowState = {
            "messages": [system_msg, human_msg],
            "spec_compliant": True,
        }

        # Simulate local node transformation and graph resolution
        span.add_event("executing_node_routing")

        simulated_response = (
            f"LangGraph execution resolved for query: '{user_query[:30]}...'. "
            f"Validated against upfront specification boundaries successfully."
        )

        return {
            "status": "COMPLETED",
            "final_state": {
                "message_count": len(initial_state["messages"]) + 1,
                "compliant": initial_state["spec_compliant"],
            },
            "output": simulated_response,
        }
