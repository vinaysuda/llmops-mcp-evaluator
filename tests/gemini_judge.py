from typing import Any

from deepeval.models import DeepEvalBaseLLM  # type: ignore[attr-defined, import-untyped, unused-ignore]
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from src.core.config import system_settings


class GeminiJudge(DeepEvalBaseLLM):  # type: ignore[no-untyped-call]
    """
    Custom DeepEval Judge wrapping Google Gemini.
    Intercepts all automated evaluation scoring prompts and routes them cleanly through the Gemini gateway.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash-lite") -> None:
        if not system_settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is missing from the environment.")

        self.model_name = model_name

        # 1. Instantiate and assign the underlying model FIRST
        self.model: Any = ChatGoogleGenerativeAI(
            model=model_name,
            api_key=system_settings.gemini_api_key,
            temperature=0.0,
        )

        # 2. Safely initialize the base class now that self.model exists
        super().__init__()

    def load_model(self, *args: Any, **kwargs: Any) -> Any:
        """Matches the exact signature and flexible return type expected by DeepEvalBaseLLM."""
        return self.model

    def generate(self, prompt: str, schema: BaseModel | None = None) -> str:
        """Standard raw text generation pass requested by DeepEval metrics."""
        chat_model: ChatGoogleGenerativeAI = self.load_model()
        res = chat_model.invoke(prompt)
        return str(res.content)

    async def a_generate(self, prompt: str, schema: BaseModel | None = None) -> str:
        """Asynchronous generation pass required for parallel CI/CD gate execution."""
        chat_model: ChatGoogleGenerativeAI = self.load_model()
        res = await chat_model.ainvoke(prompt)
        return str(res.content)

    def get_model_name(self) -> str:
        return self.model_name

    async def aclose(self) -> None:
        """
        Deterministically closes the underlying HTTP transport connections.
        Prevents lingering keep-alive sockets from throwing 'Task was destroyed'
        warnings during aggressive pytest event loop teardowns.
        """
        # Access the private underlying aiohttp client session if established by the SDK
        try:
            if hasattr(self.model, "client") and hasattr(self.model.client, "_session"):
                session = self.model.client._session
                if session and not session.closed:
                    await session.close()
        except Exception:
            pass
