"""Test fixtures for the Podman MCP server."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


@pytest.fixture(autouse=True)
def _reset_client_singleton() -> Generator[None, None, None]:
    """Reset the global client and config singletons between tests."""
    import mcp_podman_crunchtools.client as client_mod
    import mcp_podman_crunchtools.config as config_mod

    client_mod._client = None
    config_mod._config = None
    yield
    client_mod._client = None
    config_mod._config = None


def _mock_config(socket_path: str = "/var/run/test.sock") -> MagicMock:
    """Create a mock Config object."""
    config = MagicMock()
    config.socket_path = socket_path
    config.timeout = 30
    return config


def _mock_response(
    status_code: int = 200,
    json_data: Any = None,
    text: str = "",
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Build a mock httpx.Response."""
    resp_headers = headers or {}
    if json_data is not None:
        import json
        content = json.dumps(json_data).encode()
        resp_headers.setdefault("content-type", "application/json")
    else:
        content = text.encode()
        resp_headers.setdefault("content-type", "text/plain")

    return httpx.Response(
        status_code=status_code,
        content=content,
        headers=resp_headers,
        request=httpx.Request("GET", "http://podman/test"),
    )


def _patch_client(response: httpx.Response) -> Any:
    """Patch httpx.AsyncClient to return the given response."""
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=response)

    async def mock_get_client(self: Any) -> AsyncMock:  # noqa: ARG001
        return mock_client

    return patch(
        "mcp_podman_crunchtools.client.PodmanClient._get_client",
        mock_get_client,
    )
