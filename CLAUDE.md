# Repository Intelligence: LLMOps MCP Evaluator

This file provides pre-cached IDE instructions for autonomous development agents (Cursor, Claude Code) interacting with this repository.

## 🎯 Architectural Principles
- **Zero-Trust Tool Decoupling:** Tools must NEVER run in the agent's memory space. Expose all database lookups, vector operations, and codebase pagination exclusively through the isolated FastMCP JSON-RPC server (`src/mcp_server/`).
- **Dual-Layer Observability:** All execution calls must emit low-level transport spans via OpenTelemetry (`src/core/telemetry.py`) linked to high-level semantic graphs in Langfuse.
- **Spec-Driven Governance:** Pluggable multi-agent clients (`src/clients/`) must parse constraints strictly from `data/upfront_spec.md` prior to executing generation logic.
- **Deterministic Evaluation:** DeepEval assertions (`tests/evaluations/`) must use an isolated `gpt-4o` judge configured strictly to `Temperature = 0.0`.

## 🛠️ Custom Agent Skills & Build Execution

### Dependency Syncing
Use `uv` for all environment management:
```bash
uv venv
source .venv/bin/activate
uv pip install -e .

```

### Running the FastMCP Execution Server

```bash
uv run python -m src.mcp_server.server

```

### Executing the Automated Evaluation Suite

```bash
uv run deepeval test run tests/evaluations/

```

## 📐 Static Typing & Linting Enforcement

* Enforce complete type annotations on all function signatures using Pydantic V2 models for incoming and outgoing payload validation.
* Avoid loose dictionaries (`{}`) when representing states; always inherit from `pydantic.BaseModel` or typed dictionaries (`typing.TypedDict`).

---

### **Checkpoint Confirmation**

Please run the terminal setup commands, populate these first four initial files, and run:
```bash
uv venv
uv pip install -e .

```

Verify that your local environment resolves cleanly. Once you confirm setup is complete, reply with **"PROCEED"**, and we will immediately code **Phase 1: The Isolated FastMCP Server, Vector Benchmarker, and PageIndex Tools (`src/mcp_server/`)**.