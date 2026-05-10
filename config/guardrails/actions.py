from typing import Any

from nemoguardrails.actions import action  # type: ignore[import-untyped]

from src.core.telemetry import active_tracer


@action(is_system_action=True)  # type: ignore[untyped-decorator]
async def check_enterprise_compliance(context: dict[str, Any] | None = None) -> bool:
    """
    Custom NeMo Guardrails action verifying strict enterprise compliance.
    Intercepts unauthorized command overrides and emits isolated telemetry spans.
    """
    with active_tracer.start_as_current_span("guardrails_compliance_check") as span:
        span.set_attribute("guardrail.type", "semantic_firewall")

        # Extract user input safely from the runtime context
        user_input = ""
        if context and isinstance(context, dict):
            user_input = str(context.get("last_user_message", ""))

        span.set_attribute("input.length", len(user_input))

        # Hardcoded deterministic assertion checks for critical injection phrases
        blocked_terms = ["bypass_override", "drop_tables", "ignore_previous_instructions"]
        for term in blocked_terms:
            if term in user_input.lower():
                span.set_attribute("compliance.status", "FAILED")
                span.add_event("malicious_injection_intercepted")
                return False

        span.set_attribute("compliance.status", "PASSED")
        return True
