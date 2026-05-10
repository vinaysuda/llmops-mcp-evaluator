import asyncio
import os
from collections.abc import Generator
from typing import Any

import pytest

# Ensure strict mode flags are explicitly recognized in the test environment
os.environ["DEEPEVAL_STRICT_MODE"] = "true"


@pytest.fixture(scope="session", autouse=True)
def setup_enterprise_test_environment() -> Generator[None, None, None]:
    """
    Global session setup enforcing strict, immutable test boundaries.
    Manages the session-level event loop policy to guarantee clean teardowns.
    """
    yield

    # Forcibly reap any lingering background keep-alive connections at the session boundary
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()

    if pending and not loop.is_closed():
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))


@pytest.fixture(scope="function", autouse=True)
def clean_asyncio_lifecycle() -> Generator[None, None, None]:
    """Function-level boundary to catch immediate pending HTTP transport buffers."""
    yield

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    # Cancel orphaned keep-alive monitors gracefully for the active function
    pending = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    for task in pending:
        task.cancel()

    # Allow TCP teardowns to process physically without crashing the active runner
    if pending and not loop.is_closed():
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))


# Explicitly instruct pytest-asyncio to maintain a unified session loop scope
def pytest_collection_modifyitems(items: list[Any]) -> None:
    """Ensures DeepEval and Google GenAI share the exact same execution loop scope."""
    for item in items:
        if item.get_closest_marker("asyncio"):
            item.add_marker(pytest.mark.asyncio(loop_scope="session"))
