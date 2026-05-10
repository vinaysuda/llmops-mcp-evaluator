"""
Pluggable multi-agent dispatch clients.
Enforces Spec-Driven Governance by parsing upfront specifications and wrapping executions in OTel spans.
"""

from src.clients.autogen_host import execute_autogen_dispatch
from src.clients.claude_sdk_host import execute_claude_standard_dispatch
from src.clients.crewai_host import execute_crewai_dispatch
from src.clients.langgraph_host import execute_langgraph_workflow

__all__ = [
    "execute_autogen_dispatch",
    "execute_claude_standard_dispatch",
    "execute_crewai_dispatch",
    "execute_langgraph_workflow",
]
