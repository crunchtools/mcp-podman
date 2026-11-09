"""The outbound HTTP contract (constitution v1.36.0, MCP Server profile Layer 3).

A real `httpx.AsyncClient` over a `MockTransport`, rather than the shared
`_mock_client` helper that stands in for the client. That matters for two of
these: the agent string is a header the *client* adds, and the ceiling is
enforced while the client reads.
"""

from collections.abc import AsyncIterator, Callable
from importlib.metadata import version
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from mcp_podman_crunchtools import client as client_mod
from mcp_podman_crunchtools.errors import PodmanApiError
from tests.conftest import _mock_config

Handler = Callable[[httpx.Request], httpx.Response]


async def _chunks(chunk: bytes, times: int) -> AsyncIterator[bytes]:
    """A chunked body, which carries no content-length -- what the logs endpoint sends."""
    for _ in range(times):
        yield chunk


def _serving(handler: Handler) -> Any:
    """Hand every PodmanClient a real client on a MockTransport."""
    import mcp_podman_crunchtools.config as config_mod

    config_mod._config = _mock_config()
    client_mod._client = None
    real = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url=f"http://podman/{client_mod.API_VERSION}/libpod",
        headers={"User-Agent": client_mod.USER_AGENT},
    )

    async def mock_get_client(_self: object) -> httpx.AsyncClient:
        return real

    return patch("mcp_podman_crunchtools.client.PodmanClient._get_client", mock_get_client)


class TestUserAgent:
    """A request says what it is, even over a unix socket."""

    async def test_outgoing_request_names_the_product_and_version(self) -> None:
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers["User-Agent"])
            return httpx.Response(200, json={"Id": "abc"})

        with _serving(handler):
            await client_mod.get_client().get("/containers/x/json")

        expected = (
            f"mcp-podman-crunchtools/{version('mcp-podman-crunchtools')} "
            "(+https://github.com/crunchtools/mcp-podman)"
        )
        assert seen == [expected]
        assert "python-httpx" not in seen[0]


class TestResponseCeiling:
    """The logs endpoint answers chunked, so a header check never sees it."""

    async def test_chunked_logs_over_the_cap_are_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(client_mod, "MAX_RESPONSE_SIZE", 4096)

        def handler(_request: httpx.Request) -> httpx.Response:
            response = httpx.Response(
                200, headers={"content-type": "text/plain"}, content=_chunks(b"x" * 1024, 16)
            )
            assert "content-length" not in response.headers
            return response

        with _serving(handler), pytest.raises(PodmanApiError) as caught:
            await client_mod.get_client().get_text("/containers/x/logs")

        message = str(caught.value)
        assert "over the 4096 byte limit" in message
        assert "/containers/x/logs" in message
        # The remediation, because this is the endpoint that hits the cap.
        assert "tail" in message

    async def test_a_single_oversized_chunk_is_refused_before_it_is_copied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(client_mod, "MAX_RESPONSE_SIZE", 1024)

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, headers={"content-type": "text/plain"}, content=_chunks(b"x" * 8192, 1)
            )

        with _serving(handler), pytest.raises(PodmanApiError) as caught:
            await client_mod.get_client().get_text("/containers/x/logs")

        assert "over the 1024 byte limit" in str(caught.value)

    async def test_logs_under_the_cap_come_back_whole(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, headers={"content-type": "text/plain"}, content=_chunks(b"a line\n", 3)
            )

        with _serving(handler):
            text = await client_mod.get_client().get_text("/containers/x/logs")

        assert text == "a line\na line\na line\n"


class TestErrorNamesTheRequest:
    """RT #1596: the message has to say what answered, and with what."""

    async def test_a_non_podman_error_body_is_quoted_with_the_request(self) -> None:
        """A proxy or an SELinux denial in front of the socket does not send Podman JSON."""

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                502, headers={"content-type": "text/html"}, text="<html>Bad Gateway</html>"
            )

        with _serving(handler), pytest.raises(PodmanApiError) as caught:
            await client_mod.get_client().get("/containers/x/json")

        message = str(caught.value)
        assert "Bad Gateway" in message
        assert "/containers/x/json" in message
        assert "text/html" in message

    async def test_podmans_own_error_shape_is_still_used_verbatim(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"cause": "container state improper"})

        with _serving(handler), pytest.raises(PodmanApiError) as caught:
            await client_mod.get_client().get("/containers/x/json")

        assert "container state improper" in str(caught.value)
