import os
from typing import Any

from deepeval.models import DeepEvalBaseLLM  # type: ignore[attr-defined, import-untyped, unused-ignore]
from langchain_anthropic import ChatAnthropic  # type: ignore[import-not-found]

# Frontier Provider Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pydantic import BaseModel


class UniversalJudge(DeepEvalBaseLLM):  # type: ignore[no-untyped-call]
    """
    Universal DeepEval Judge supporting dynamic fallback and multi-provider routing.
    Safely handles connection pooling and strict async lifecycle teardowns across providers.
    """

    def __init__(self) -> None:
        self.provider: str = os.getenv("EVAL_JUDGE_PROVIDER", "gemini").lower()
        self.model_name: str = "unknown"

        # 1. Instantiate the correct frontier model FIRST to avoid lifecycle race conditions
        if self.provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY missing for Gemini Judge execution.")
            self.model_name = "gemini-2.5-flash"
            self.model: Any = ChatGoogleGenerativeAI(model=self.model_name, api_key=api_key, temperature=0.0)

        elif self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY missing for OpenAI Judge execution.")
            self.model_name = "gpt-4o"
            self.model = ChatOpenAI(model=self.model_name, api_key=api_key, temperature=0.0)

        elif self.provider == "azure":
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
            if not all([api_key, endpoint, deployment]):
                raise ValueError("Incomplete Azure OpenAI environment variables.")
            self.model_name = str(deployment)
            self.model = AzureChatOpenAI(
                azure_deployment=self.model_name,
                api_key=api_key,
                azure_endpoint=str(endpoint),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                temperature=0.0,
            )

        elif self.provider == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY missing for Claude Judge execution.")
            self.model_name = "claude-3-5-sonnet-latest"
            self.model = ChatAnthropic(model_name=self.model_name, api_key=api_key, temperature=0.0)

        else:
            raise ValueError(f"Unsupported EVAL_JUDGE_PROVIDER: {self.provider}")

        # 2. Safely initialize the base class now that self.model is firmly attached
        super().__init__()

    def load_model(self, *args: Any, **kwargs: Any) -> Any:
        return self.model

    def generate(self, prompt: str, schema: BaseModel | None = None) -> str:
        client = self.load_model()
        res = client.invoke(prompt)
        return str(res.content)

    async def a_generate(self, prompt: str, schema: BaseModel | None = None) -> str:
        client = self.load_model()
        res = await client.ainvoke(prompt)
        return str(res.content)

    def get_model_name(self) -> str:
        return f"{self.provider}:{self.model_name}"

    async def aclose(self) -> None:
        """Deterministically flushes underlying keep-alive HTTP sockets per provider."""
        try:
            # Handle Gemini/aiohttp persistent connector teardowns
            if self.provider == "gemini" and hasattr(self.model, "client"):
                if hasattr(self.model.client, "_session") and self.model.client._session:
                    if not self.model.client._session.closed:
                        await self.model.client._session.close()
            # Handle async httpx connection pool teardowns for OpenAI/Anthropic
            elif hasattr(self.model, "async_client") and self.model.async_client:
                if not self.model.async_client.is_closed:
                    await self.model.async_client.aclose()
        except Exception:
            pass
