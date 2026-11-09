"""Async HTTP client for the Podman REST API over Unix sockets.

Uses httpx AsyncHTTPTransport with UDS (Unix Domain Socket) support.
The base URL hostname is a placeholder — actual connection goes through
the socket.
"""

import json
import logging
from importlib.metadata import version
from typing import Any
from urllib.parse import quote

import httpx

from .config import get_config
from .errors import (
    ContainerNotFoundError,
    ImageNotFoundError,
    InvalidNameError,
    NetworkNotFoundError,
    PodmanApiError,
    PodNotFoundError,
    SocketConnectionError,
    VolumeNotFoundError,
)
from .models import MAX_IMAGE_LENGTH

logger = logging.getLogger(__name__)

MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB
API_VERSION = "v5.0.0"

# Identify this client by name, as every other server in the fleet now does
# (constitution v1.36.0, MCP Server profile Layer 3). The socket on the other
# end does not challenge a nameless agent, but an exception for one client is a
# branch in the rule that rots, and `podman --log-level=debug` showing which
# process asked is worth the one line.
USER_AGENT = (
    f"mcp-podman-crunchtools/{version('mcp-podman-crunchtools')} "
    "(+https://github.com/crunchtools/mcp-podman)"
)

# How much of a body to quote back in an error. Enough to recognise an HTML
# error from a proxy in front of the socket, or a truncated JSON stream.
BODY_SNIPPET_CHARS = 200
ELLIPSIS = "..."


def _body_snippet(body: bytes) -> str:
    """A short, single-line excerpt of a response body, for an error message."""
    prefix = body[: BODY_SNIPPET_CHARS * 4]
    collapsed = " ".join(prefix.decode("utf-8", errors="replace").split())
    if not collapsed:
        return "<empty body>"
    if len(collapsed) > BODY_SNIPPET_CHARS or len(body) > len(prefix):
        return collapsed[: BODY_SNIPPET_CHARS - len(ELLIPSIS)] + ELLIPSIS
    return collapsed


def _error_detail(response: httpx.Response, body: bytes) -> str:
    """Podman's own error text, or the body quoted with the request it answered.

    The fallback is what tells a proxy or an SELinux denial in front of the
    socket apart from the API refusing something: neither of those answers with
    Podman's `cause`/`message` shape, and before this they both arrived as
    "Unknown error". Its own function because `_handle_error` dispatches on
    status over five exception types and this is the one part that reads a body.
    """
    try:
        parsed = json.loads(body)
    except ValueError:
        parsed = None
    detail = ""
    if isinstance(parsed, dict):
        detail = str(parsed.get("cause", parsed.get("message", ""))).strip()
    elif parsed is not None:
        detail = str(parsed)
    return detail or f"{_where(response)} returned {_body_snippet(body)}"


def _where(response: httpx.Response) -> str:
    """Which request a response answered, for an error message.

    The URL carries the API path, which is what identifies the endpoint here.
    Which socket it went to is already in `SocketConnectionError`, and the host
    in the URL is the placeholder a UDS transport requires.
    """
    return (
        f"{response.request.method} {response.request.url} "
        f"(HTTP {response.status_code}, {response.headers.get('content-type', 'no content-type')})"
    )


HTTP_NO_CONTENT = 204
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409

_client: "PodmanClient | None" = None

# Names that an HTTP client resolves away instead of sending: "" leaves an empty
# segment, and "." and ".." are dot segments that quote() does not encode.
UNADDRESSABLE_NAMES = frozenset({"", ".", ".."})


def path_segment(name: str) -> str:
    """Encode a caller-supplied name as exactly one segment of an API path.

    The bound is the image reference limit, the longest name any resource takes.
    """
    if name in UNADDRESSABLE_NAMES or len(name) > MAX_IMAGE_LENGTH:
        raise InvalidNameError(name)
    return quote(name, safe="")


def get_client() -> "PodmanClient":
    """Get the global Podman client instance."""
    global _client
    if _client is None:
        _client = PodmanClient()
    return _client


class PodmanClient:
    """Async HTTP client for the Podman Libpod REST API."""

    def __init__(self) -> None:
        self._config = get_config()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client with UDS transport."""
        if self._client is None:
            transport = httpx.AsyncHTTPTransport(uds=self._config.socket_path)
            self._client = httpx.AsyncClient(
                transport=transport,
                base_url=f"http://podman/{API_VERSION}/libpod",
                timeout=httpx.Timeout(float(self._config.timeout)),
                headers={"User-Agent": USER_AGENT},
            )
        return self._client

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Make a POST request.

        timeout overrides the configured request timeout for operations that
        legitimately run long, such as pruning images.
        """
        return await self._request(
            "POST", path, params=params, json_data=json_data, timeout=timeout
        )

    async def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self._request("DELETE", path, params=params)

    async def get_text(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Make a GET request and return raw text (for logs)."""
        logger.debug("API request: GET %s", path)
        response, body = await self._send("GET", path, params, None)
        self._check_response(response, body, path)
        return body.decode("utf-8", errors="replace")

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Make an API request with error handling."""
        logger.debug("API request: %s %s", method, path)
        response, body = await self._send(method, path, params, json_data, timeout)
        self._check_response(response, body, path)
        return self._parse_response(response, body)

    async def _send(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None,
        json_data: dict[str, Any] | None,
        timeout: float | None = None,
    ) -> tuple[httpx.Response, bytes]:
        """Send the request and return the response with its bounded body.

        Streamed rather than read whole, because the cap has to hold while the
        body arrives: `/containers/{name}/logs` answers chunked, so a
        `content-length` check never sees it.
        """
        client = await self._get_client()
        try:
            request = client.build_request(
                method=method,
                url=path,
                params=params,
                json=json_data,
                # None would disable the timeout outright, so fall back to the
                # client's configured one explicitly.
                timeout=httpx.USE_CLIENT_DEFAULT if timeout is None else timeout,
            )
            response = await client.send(request, stream=True)
            try:
                return response, await self._read_capped(response)
            finally:
                await response.aclose()
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            # ConnectTimeout subclasses TimeoutException, not ConnectError, so it
            # must be caught here or a hung socket loses the remediation message.
            raise SocketConnectionError(self._config.socket_path) from e
        except httpx.TimeoutException as e:
            raise PodmanApiError(0, f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise PodmanApiError(0, f"Request failed: {e}") from e

    @staticmethod
    async def _read_capped(response: httpx.Response) -> bytes:
        """Read the body, aborting as soon as it would pass MAX_RESPONSE_SIZE.

        One buffer, measured before the copy: `aiter_bytes()` promises nothing
        about chunk size -- one chunk can be the whole body -- so appending
        first would copy in exactly the response being refused.
        """
        declared = response.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_RESPONSE_SIZE:
            raise PodmanApiError(
                response.status_code,
                f"{_where(response)} declared {declared} bytes, over the "
                f"{MAX_RESPONSE_SIZE} byte limit",
            )
        body = bytearray()
        async for chunk in response.aiter_bytes():
            if len(body) + len(chunk) > MAX_RESPONSE_SIZE:
                raise PodmanApiError(
                    response.status_code,
                    f"{_where(response)} sent over the {MAX_RESPONSE_SIZE} byte limit. "
                    "For container logs, ask for fewer lines with `tail`.",
                )
            body += chunk
        return bytes(body)

    def _check_response(self, response: httpx.Response, body: bytes, path: str) -> None:
        """Raise for an unsuccessful status. The size was bounded while reading."""
        if not response.is_success:
            self._handle_error(response, body, path)

    @staticmethod
    def _parse_response(response: httpx.Response, body: bytes) -> dict[str, Any]:
        """Parse a successful response into a dict."""
        if response.status_code == HTTP_NO_CONTENT or not body:
            return {"status": "success"}

        content_type = response.headers.get("content-type", "")
        if "text/plain" in content_type:
            return {"content": body.decode("utf-8", errors="replace")}

        try:
            parsed = json.loads(body)
        except ValueError as e:
            parsed = PodmanClient._parse_json_stream(response, body, e)

        if isinstance(parsed, list):
            return {"items": parsed, "count": len(parsed)}
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}

    @staticmethod
    def _parse_json_stream(response: httpx.Response, body: bytes, cause: ValueError) -> Any:
        """Return the final report of a newline-delimited JSON stream.

        Streaming endpoints such as /images/pull answer 200 with one JSON
        object per line: progress, then a report carrying either the result
        or an "error". A failure mid-stream arrives in-band, so it is raised
        here rather than returned as success.
        """
        last: Any = None
        for line in body.decode("utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                last = json.loads(line)
            except ValueError:
                last = None
                break
            if isinstance(last, dict) and last.get("error"):
                raise PodmanApiError(response.status_code, str(last["error"]))
        if last is None:
            raise PodmanApiError(
                response.status_code,
                f"{_where(response)} is not JSON ({cause}): {_body_snippet(body)}",
            ) from cause
        return last

    def _handle_error(self, response: httpx.Response, body: bytes, path: str) -> None:
        """Handle error responses from the Podman API."""
        status_code = response.status_code
        error_msg = _error_detail(response, body)

        if status_code == HTTP_NOT_FOUND:
            if "/containers/" in path:
                raise ContainerNotFoundError(error_msg)
            if "/images/" in path:
                raise ImageNotFoundError(error_msg)
            if "/pods/" in path:
                raise PodNotFoundError(error_msg)
            if "/networks/" in path:
                raise NetworkNotFoundError(error_msg)
            if "/volumes/" in path:
                raise VolumeNotFoundError(error_msg)

        if status_code == HTTP_CONFLICT:
            raise PodmanApiError(status_code, f"Conflict: {error_msg}")

        raise PodmanApiError(status_code, error_msg)
