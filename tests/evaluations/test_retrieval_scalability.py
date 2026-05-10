import pytest
from deepeval import assert_test  # type: ignore[attr-defined, import-untyped, unused-ignore]
from deepeval.metrics import ContextualRecallMetric  # type: ignore[attr-defined, import-untyped, unused-ignore]
from deepeval.test_case import LLMTestCase  # type: ignore[attr-defined, import-untyped, unused-ignore]

from src.core.config import system_settings
from src.core.telemetry import active_tracer
from src.mcp_server.vector_benchmarker import MultiTenantVectorEngine


@pytest.fixture
def contextual_recall_metric() -> ContextualRecallMetric:
    return ContextualRecallMetric(
        threshold=system_settings.min_groundedness_score,
        model="gpt-4o",
        include_reason=True,  # Fixed parameter mismatch
        strict_mode=system_settings.deepeval_strict_mode,
    )


def test_vector_retrieval_scalability_and_recall(
    contextual_recall_metric: ContextualRecallMetric,
) -> None:
    with active_tracer.start_as_current_span("eval_retrieval_scalability") as span:
        engine = MultiTenantVectorEngine()

        target_tenant = "tenant-finance-audit"
        query = "What are the isolation requirements for transactional databases?"

        result = engine.execute_benchmark_query(
            engine="qdrant",
            tenant_id=target_tenant,
            query=query,
            top_k=2,
        )

        span.set_attribute("latency_ms", result.latency_ms)

        assert result.latency_ms < 100.0, f"Retrieval latency {result.latency_ms}ms breached 100ms SLA."

        retrieved_texts = [str(chunk.get("text", "")) for chunk in result.retrieved_chunks]
        expected_answer = "Cross-border transactional databases require encrypted isolation."

        test_case = LLMTestCase(
            input=query,
            actual_output=expected_answer,
            retrieval_context=retrieved_texts,
            expected_output=expected_answer,
        )

        span.add_event("executing_recall_eval")
        assert_test(test_case, [contextual_recall_metric])
