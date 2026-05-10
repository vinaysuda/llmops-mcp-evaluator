import logging

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)

from src.core.config import system_settings

logger = logging.getLogger("CoreTelemetry")


def initialize_opentelemetry_bridge() -> trace.Tracer:
    """
    Bootstraps the native OpenTelemetry provider.
    Binds process metrics directly to the unified service namespace.
    """
    # Establish the immutable execution resource entity
    resource = Resource.create(
        attributes={"service.name": system_settings.otel_service_name, "telemetry.sdk.language": "python"}
    )

    # Initialize the core trace provider
    provider = TracerProvider(resource=resource)

    # Configure the targeted output exporter based on environment flags
    exporter: SpanExporter | None = None
    if system_settings.otel_traces_exporter.lower() == "console":
        exporter = ConsoleSpanExporter()

    if exporter:
        # Batch export spans asynchronously to prevent thread blocking
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        logger.info("OpenTelemetry Console Span Exporter successfully bound.")
    else:
        logger.warning(f"Unsupported OTel exporter target: {system_settings.otel_traces_exporter}. Spans will drop.")

    # Register the active global trace provider
    trace.set_tracer_provider(provider)

    # Return the named tracer singleton used to decorate functional boundaries
    return trace.get_tracer("llmops.mcp.tracer")


# Expose the active execution tracer singleton
active_tracer = initialize_opentelemetry_bridge()
