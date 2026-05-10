from typing import Any

from src.core.telemetry import active_tracer


def execute_autogen_dispatch(initial_message: str) -> dict[str, Any]:
    """
    Simulates an AutoGen multi-agent turn-based dialogue.
    Tracks proxy negotiation passes inside an isolated telemetry span.
    """
    with active_tracer.start_as_current_span("autogen_dialogue_dispatch") as span:
        span.set_attribute("framework", "autogen")
        span.add_event("user_proxy_message_sent")

        simulated_dialogue_log = [
            {"speaker": "UserProxy", "message": initial_message},
            {
                "speaker": "EnterpriseAssistant",
                "message": "Acknowledged. Proceeding under zero-trust tool execution rules.",
            },
        ]

        return {
            "framework": "AutoGen",
            "turns": len(simulated_dialogue_log),
            "dialogue_history": simulated_dialogue_log,
        }
