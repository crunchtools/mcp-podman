"""Async HTTP client for the Podman REST API over Unix sockets.

Uses httpx AsyncHTTPTransport with UDS (Unix Domain Socket) support.
The base URL hostname is a placeholder — actual connection goes through
the socket.
"""

import json
import logging
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

logger = logging.getLogger(__name__)

MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB
API_VERSION = "v5.0.0"

HTTP_NO_CONTENT = 204
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409

_client: "PodmanClient | None" = None

# Names that an HTTP client resolves away instead of sending: "" leaves an empty
# segment, and "." and ".." are dot segments that quote() does not encode.
UNADDRESSABLE_NAMES = frozenset({"", ".", ".."})


def path_segment(name: str) -> str:
    """Encode a caller-supplied name as exactly one segment of an API path."""
    if name in UNADDRESSABLE_NAMES:
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
        response = await self._send("GET", path, params, None)
        self._check_response(response, path)
        return response.text

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
        response = await self._send(method, path, params, json_data, timeout)
        self._check_response(response, path)
        return self._parse_response(response)

    async def _send(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None,
        json_data: dict[str, Any] | None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Send the HTTP request, raising clean errors on transport failures."""
        client = await self._get_client()
        try:
            return await client.request(
                method=method,
                url=path,
                params=params,
                json=json_data,
                # None would disable the timeout outright, so fall back to the
                # client's configured one explicitly.
                timeout=httpx.USE_CLIENT_DEFAULT if timeout is None else timeout,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            # ConnectTimeout subclasses TimeoutException, not ConnectError, so it
            # must be caught here or a hung socket loses the remediation message.
            raise SocketConnectionError(self._config.socket_path) from e
        except httpx.TimeoutException as e:
            raise PodmanApiError(0, f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise PodmanApiError(0, f"Request failed: {e}") from e

    def _check_response(self, response: httpx.Response, path: str) -> None:
        """Validate response size and status."""
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > MAX_RESPONSE_SIZE:
            raise PodmanApiError(0, "Response too large")
        if not response.is_success:
            self._handle_error(response, path)

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        """Parse a successful response into a dict."""
        if response.status_code == HTTP_NO_CONTENT or not response.text:
            return {"status": "success"}

        content_type = response.headers.get("content-type", "")
        if "text/plain" in content_type:
            return {"content": response.text}

        try:
            parsed = response.json()
        except ValueError as e:
            parsed = PodmanClient._parse_json_stream(response, e)

        if isinstance(parsed, list):
            return {"items": parsed, "count": len(parsed)}
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}

    @staticmethod
    def _parse_json_stream(response: httpx.Response, cause: ValueError) -> Any:
        """Return the final report of a newline-delimited JSON stream.

        Streaming endpoints such as /images/pull answer 200 with one JSON
        object per line: progress, then a report carrying either the result
        or an "error". A failure mid-stream arrives in-band, so it is raised
        here rather than returned as success.
        """
        last: Any = None
        for line in response.text.splitlines():
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
            raise PodmanApiError(response.status_code, f"Invalid JSON response: {cause}") from cause
        return last

    def _handle_error(self, response: httpx.Response, path: str) -> None:
        """Handle error responses from the Podman API."""
        status_code = response.status_code

        error_msg = "Unknown error"
        try:
            error_body = response.json()
            if isinstance(error_body, dict):
                error_msg = str(error_body.get("cause", error_body.get("message", error_msg)))
            else:
                error_msg = str(error_body)
        except ValueError:
            error_msg = response.text[:200] if response.text else "Unknown error"

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
