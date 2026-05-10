import pytest
from deepeval import assert_test  # type: ignore[attr-defined, import-untyped, unused-ignore]
from deepeval.metrics import GEval  # type: ignore[attr-defined, import-untyped, unused-ignore]
from deepeval.test_case import (  # type: ignore[attr-defined, import-untyped, unused-ignore]
    LLMTestCase,
    LLMTestCaseParams,
)

from src.core.config import system_settings
from src.core.telemetry import active_tracer


@pytest.fixture
def task_fidelity_metric() -> GEval:
    return GEval(
        name="TaskSpecFidelity",
        criteria="Assess whether the actual output completely and accurately fulfills the user query while strictly obeying the provided enterprise specification context.",
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT,
        ],
        threshold=0.90,
        model="gpt-4o",
        strict_mode=system_settings.deepeval_strict_mode,
    )


def test_multi_agent_spec_fidelity(task_fidelity_metric: GEval) -> None:
    with active_tracer.start_as_current_span("eval_task_fidelity") as span:
        user_query = "Summarize the telemetry status for cluster monitoring."
        upfront_spec = "All summaries must include the explicit status label (NOMINAL or CRITICAL) and the timestamp."

        agent_output = "Cluster monitoring reports a CRITICAL status as of 2026-05-10T08:05:00Z."

        test_case = LLMTestCase(
            input=user_query,
            actual_output=agent_output,
            retrieval_context=[upfront_spec],
        )

        span.add_event("executing_fidelity_eval")
        assert_test(test_case, [task_fidelity_metric])
