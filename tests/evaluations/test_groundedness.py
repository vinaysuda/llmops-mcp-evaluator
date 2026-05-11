
import pytest
from deepeval import assert_test  # type: ignore[attr-defined, import-untyped, unused-ignore]
from deepeval.metrics import FaithfulnessMetric  # type: ignore[attr-defined, import-untyped, unused-ignore]
from deepeval.test_case import LLMTestCase  # type: ignore[attr-defined, import-untyped, unused-ignore]

from src.core.config import system_settings
from src.core.telemetry import active_tracer

# Point import to the newly authored Universal Judge
from tests.universal_judge import UniversalJudge


@pytest.fixture
def faithfulness_metric() -> FaithfulnessMetric:
    # Dynamically boots whichever provider is defined in EVAL_JUDGE_PROVIDER
    universal_model = UniversalJudge()
    return FaithfulnessMetric(
        threshold=system_settings.min_groundedness_score,
        model=universal_model,
        include_reason=True,
        strict_mode=system_settings.deepeval_strict_mode,
    )


@pytest.mark.asyncio
async def test_mission_critical_telemetry_groundedness(faithfulness_metric: FaithfulnessMetric) -> None:
    with active_tracer.start_as_current_span("deepeval_ci_gate_assertion") as span:
        span.set_attribute("eval.metric", "faithfulness")
        span.set_attribute("eval.threshold", system_settings.min_groundedness_score)
        # Log exactly which judge execution path processed the assertion
        if faithfulness_metric.model is not None:
            span.set_attribute("eval.judge_target", faithfulness_metric.model.get_model_name())

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
            # Deterministically flush keep-alive background connections safely
            if faithfulness_metric.model is not None and hasattr(faithfulness_metric.model, "aclose"):
                await faithfulness_metric.model.aclose()
