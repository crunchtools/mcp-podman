"""Async HTTP client for the Podman REST API over Unix sockets.

Uses httpx AsyncHTTPTransport with UDS (Unix Domain Socket) support.
The base URL hostname is a placeholder — actual connection goes through
the socket.
"""

import logging
from typing import Any

import httpx

from .config import get_config
from .errors import (
    ContainerNotFoundError,
    ImageNotFoundError,
    NetworkNotFoundError,
    PodmanApiError,
    PodNotFoundError,
    SocketConnectionError,
    VolumeNotFoundError,
)

logger = logging.getLogger(__name__)

MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB
API_VERSION = "v5.0.0"

_client: "PodmanClient | None" = None


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
    ) -> dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", path, params=params, json_data=json_data)

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
        client = await self._get_client()
        try:
            response = await client.request("GET", path, params=params)
        except httpx.ConnectError as e:
            raise SocketConnectionError(self._config.socket_path) from e
        except httpx.TimeoutException as e:
            raise PodmanApiError(0, f"Request timeout: {e}") from e

        if not response.is_success:
            self._handle_error(response, path)

        return response.text

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request with error handling."""
        client = await self._get_client()
        logger.debug("API request: %s %s", method, path)
        response = await self._send(client, method, path, params, json_data)
        self._check_response(response, path)
        return self._parse_response(response)

    async def _send(
        self,
        client: httpx.AsyncClient,
        method: str,
        path: str,
        params: dict[str, Any] | None,
        json_data: dict[str, Any] | None,
    ) -> httpx.Response:
        """Send the HTTP request, raising clean errors on transport failures."""
        try:
            return await client.request(
                method=method, url=path, params=params, json=json_data,
            )
        except httpx.ConnectError as e:
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
        if response.status_code == 204 or not response.text:
            return {"status": "success"}

        content_type = response.headers.get("content-type", "")
        if "text/plain" in content_type:
            return {"content": response.text}

        try:
            parsed = response.json()
        except ValueError as e:
            raise PodmanApiError(
                response.status_code, f"Invalid JSON response: {e}"
            ) from e

        if isinstance(parsed, list):
            return {"items": parsed, "count": len(parsed)}
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}

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

        if status_code == 404:
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

        if status_code == 409:
            raise PodmanApiError(status_code, f"Conflict: {error_msg}")

        raise PodmanApiError(status_code, error_msg)
