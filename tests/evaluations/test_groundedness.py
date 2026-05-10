import pytest
from deepeval import assert_test  # type: ignore[attr-defined, import-untyped, unused-ignore]
from deepeval.metrics import FaithfulnessMetric  # type: ignore[attr-defined, import-untyped, unused-ignore]
from deepeval.test_case import LLMTestCase  # type: ignore[attr-defined, import-untyped, unused-ignore]

from src.core.config import system_settings
from src.core.telemetry import active_tracer
from tests.gemini_judge import GeminiJudge


@pytest.fixture
def faithfulness_metric() -> FaithfulnessMetric:
    gemini_model = GeminiJudge(model_name="gemini-2.5-flash-lite")
    return FaithfulnessMetric(
        threshold=system_settings.min_groundedness_score,
        model=gemini_model,
        include_reason=True,
        strict_mode=system_settings.deepeval_strict_mode,
    )


@pytest.mark.asyncio
async def test_mission_critical_telemetry_groundedness(faithfulness_metric: FaithfulnessMetric) -> None:
    with active_tracer.start_as_current_span("deepeval_ci_gate_assertion") as span:
        span.set_attribute("eval.metric", "faithfulness")
        span.set_attribute("eval.threshold", system_settings.min_groundedness_score)

        retrieved_context: list[str] = [
            "Resource SYS-CLUSTER-02 reports error_rate_percentage at 5.8% with status CRITICAL as of 2026-05-10T08:05:00Z."
        ]

        agent_output: str = (
            "The enterprise resource SYS-CLUSTER-02 is currently in a CRITICAL state "
            "due to an error rate percentage reaching 5.8%."
        )

        test_case = LLMTestCase(
            input="What is the current operational status of SYS-CLUSTER-02?",
            actual_output=agent_output,
            retrieval_context=retrieved_context,
        )

        span.add_event("executing_llm_as_a_judge_evaluation")

        try:
            assert_test(test_case, [faithfulness_metric])
            span.set_attribute("eval.status", "PASSED")
        except AssertionError as e:
            span.set_attribute("eval.status", "FAILED")
            span.record_exception(e)
            raise e
        finally:
            # Deterministically flush keep-alive background connections
            # Explicitly narrow out None first to satisfy Mypy strict union rules
            if faithfulness_metric.model is not None and hasattr(faithfulness_metric.model, "aclose"):
                await faithfulness_metric.model.aclose()
