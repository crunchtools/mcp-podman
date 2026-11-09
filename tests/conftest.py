"""Test fixtures for the Podman MCP server."""

import json
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

DEFAULT_TIMEOUT_SECONDS = 30


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
    config.timeout = DEFAULT_TIMEOUT_SECONDS
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


def _mock_client(**kwargs: Any) -> AsyncMock:
    """A stand-in for the client, whose `build_request` builds a real request.

    The client now streams: `build_request` then `send(..., stream=True)`. A
    real `httpx.Client` builds the request so that assertions on the url,
    params and timeout a caller passed still mean what they did, while `send`
    is what each test scripts.
    """
    builder = httpx.Client(base_url="http://podman/v5.0.0/libpod")
    mock_client = AsyncMock()
    mock_client.build_request = MagicMock(side_effect=builder.build_request)
    mock_client.send = AsyncMock(**kwargs)
    return mock_client


def _patching_get_client(mock_client: AsyncMock) -> Any:
    """Hand every `PodmanClient` the given stand-in."""

    async def mock_get_client(_self: Any) -> AsyncMock:
        return mock_client

    return patch(
        "mcp_podman_crunchtools.client.PodmanClient._get_client",
        mock_get_client,
    )


def _patch_client(response: httpx.Response) -> Any:
    """Patch the client so every request is answered with the given response."""
    return _patching_get_client(_mock_client(return_value=response))


def _patch_client_raising(exc: Exception) -> Any:
    """Patch the client so every request raises the given exception."""
    return _patching_get_client(_mock_client(side_effect=exc))
