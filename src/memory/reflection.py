import json
import os

from pydantic import BaseModel, Field

from src.core.telemetry import active_tracer


class MemoryEntry(BaseModel):
    """Immutable memory entry representing an evaluated agent reflection or rule."""

    entry_id: str = Field(..., description="Unique identifier for the memory entry.")
    category: str = Field(..., description="Category of reflection (e.g., 'error_correction', 'tool_optimization').")
    content: str = Field(..., description="The core actionable insight or reflection.")
    confidence_score: float = Field(..., description="Confidence score of the insight from 0.0 to 1.0.")


class ReflectionEngine:
    """
    Persistent Reflection & Memory Engine.
    Manages long-term structural learnings across multi-agent runs,
    enforcing persistent feedback loops and reducing repeating errors.
    """

    def __init__(self, storage_path: str = "data/agent_memory.json") -> None:
        self.storage_path = storage_path
        self._memory_store: dict[str, MemoryEntry] = {}
        self._load_memory()

    def _load_memory(self) -> None:
        """Loads existing reflection layers from the persistent local datastore."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, encoding="utf-8") as f:
                    raw_data = json.load(f)
                    for k, v in raw_data.items():
                        self._memory_store[k] = MemoryEntry(**v)
            except Exception:
                # Fallback cleanly to an empty store if parsing fails or file is corrupted
                self._memory_store = {}

    def _save_memory(self) -> None:
        """Flushes current memory entries atomically to persistent storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        raw_data = {k: v.model_dump() for k, v in self._memory_store.items()}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)

    def add_reflection(self, entry_id: str, category: str, content: str, confidence_score: float = 0.95) -> MemoryEntry:
        """
        Commits a new operational insight to the persistent reflection store.
        Wraps execution inside an OpenTelemetry observability span.
        """
        with active_tracer.start_as_current_span("commit_agent_reflection") as span:
            span.set_attribute("memory.entry_id", entry_id)
            span.set_attribute("memory.category", category)
            span.set_attribute("memory.confidence", confidence_score)

            entry = MemoryEntry(
                entry_id=entry_id,
                category=category,
                content=content,
                confidence_score=confidence_score,
            )
            self._memory_store[entry_id] = entry
            self._save_memory()

            span.add_event("memory_flushed_to_disk")
            return entry

    def retrieve_relevant_insights(
        self, category: str | None = None, min_confidence: float = 0.80
    ) -> list[MemoryEntry]:
        """
        Retrieves high-confidence persistent learnings to inject into agent system prompts.
        """
        with active_tracer.start_as_current_span("retrieve_agent_reflections") as span:
            span.set_attribute("query.category", category or "all")
            span.set_attribute("query.min_confidence", min_confidence)

            results = []
            for entry in self._memory_store.values():
                if entry.confidence_score >= min_confidence:
                    if category is None or entry.category.lower() == category.lower():
                        results.append(entry)

            span.set_attribute("results.count", len(results))
            return results
