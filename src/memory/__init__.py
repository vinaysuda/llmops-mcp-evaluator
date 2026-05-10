"""
Persistent Reflection & Memory Engine.
Provides long-term structural learning loops to prevent cyclical agent errors.
Enforces OpenTelemetry tracing across all read/write memory operations.
"""

from src.memory.reflection import MemoryEntry, ReflectionEngine

__all__ = ["MemoryEntry", "ReflectionEngine"]
