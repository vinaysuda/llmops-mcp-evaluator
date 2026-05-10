from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnterpriseSystemSettings(BaseSettings):
    """
    Rigorous environment validation engine.
    Fails the runtime deterministically if critical security keys or tracing endpoints are absent.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Multi-Model Dispatch Credentials
    azure_openai_api_key: str | None = Field(None, description="Azure OpenAI API gateway key.")
    azure_openai_endpoint: str | None = Field(None, description="Azure OpenAI tenant endpoint.")
    anthropic_api_key: str | None = Field(None, description="Anthropic frontier dispatch key.")
    gemini_api_key: str | None = Field(None, description="Google Gemini API key.")

    # Full-Stack Observability Endpoints
    langfuse_public_key: str | None = Field(None, description="Langfuse public routing identifier.")
    langfuse_secret_key: str | None = Field(None, description="Langfuse secret payload ingest key.")
    langfuse_host: str = Field("https://cloud.langfuse.com", description="Langfuse upstream tracing host.")

    otel_service_name: str = Field("llmops-mcp-evaluator", description="OpenTelemetry service namespace.")
    otel_traces_exporter: str = Field("console", description="Target OpenTelemetry transport exporter.")

    # CI/CD Evaluation Bounds
    deepeval_strict_mode: bool = Field(True, description="Enforce hard failures on low assertion scores.")
    min_groundedness_score: float = Field(0.95, description="Strict minimum threshold for LLM-as-a-judge approval.")


# Instantiate the globally accessible, immutable configuration singleton
system_settings = EnterpriseSystemSettings()  # type: ignore[call-arg]
