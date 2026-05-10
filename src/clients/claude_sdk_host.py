import os
from typing import Any

from anthropic import Anthropic
from pydantic import BaseModel, Field

from src.core.config import system_settings
from src.core.telemetry import active_tracer


class ClaudeExecutionResult(BaseModel):
    """Structured payload validation for native Claude SDK responses."""

    raw_output: str = Field(..., description="The generated text payload.")
    model_used: str = Field(..., description="The specific frontier model identifier.")
    input_tokens: int = Field(..., description="Total prompt tokens consumed.")
    output_tokens: int = Field(..., description="Total completion tokens generated.")


def _load_upfront_spec() -> str:
    """Loads enterprise governance constraints from the local specification file."""
    spec_path = os.path.join("data", "upfront_spec.md")
    if os.path.exists(spec_path):
        with open(spec_path, encoding="utf-8") as f:
            return f.read().strip()
    return "No explicit governance constraints defined."


def execute_claude_standard_dispatch(
    prompt: str,
    model: str = "claude-3-5-sonnet-20241022",
    temperature: float = 0.0,
) -> ClaudeExecutionResult:
    """
    Executes a prompt against the Anthropic API wrapped inside an OpenTelemetry span.
    Injects mandatory upfront specifications into the system instructions.
    """
    # Fail deterministically if the client key is absent
    if not system_settings.anthropic_api_key:
        raise ValueError("Anthropic API key is missing from system configuration.")

    client = Anthropic(api_key=system_settings.anthropic_api_key)
    governance_spec = _load_upfront_spec()

    system_instruction = (
        f"You are an enterprise AI agent. You MUST adhere strictly to the following "
        f"upfront governance specification:\n\n{governance_spec}"
    )

    # Wrap the remote network call in a low-level OpenTelemetry span
    with active_tracer.start_as_current_span("claude_native_dispatch") as span:
        span.set_attribute("llm.provider", "anthropic")
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.temperature", temperature)

        response = client.messages.create(
            model=model,
            max_tokens=2048,
            temperature=temperature,
            system=system_instruction,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract strict usage metrics safely
        usage: Any | None = getattr(response, "usage", None)
        in_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        out_tokens = getattr(usage, "output_tokens", 0) if usage else 0

        # Safely parse the text block content
        content_block = response.content[0] if response.content else None
        output_text = getattr(content_block, "text", "") if content_block else ""

        span.set_attribute("llm.usage.input_tokens", in_tokens)
        span.set_attribute("llm.usage.output_tokens", out_tokens)

        return ClaudeExecutionResult(
            raw_output=output_text,
            model_used=model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
        )
