"""Safe error types for the Podman MCP server.

All errors inherit from ToolError so FastMCP returns them as tool errors
rather than crashing the server.
"""

import logging

from fastmcp.exceptions import ToolError

logger = logging.getLogger(__name__)


class PodmanApiError(ToolError):
    """Error from the Podman REST API."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"Podman API error {code}: {message}")


class ContainerNotFoundError(ToolError):
    """Container does not exist."""

    def __init__(self, name: str) -> None:
        safe_name = name[:80] if len(name) > 80 else name
        super().__init__(f"Container not found: {safe_name}")


class ImageNotFoundError(ToolError):
    """Image does not exist."""

    def __init__(self, name: str) -> None:
        safe_name = name[:120] if len(name) > 120 else name
        super().__init__(f"Image not found: {safe_name}")


class PodNotFoundError(ToolError):
    """Pod does not exist."""

    def __init__(self, name: str) -> None:
        safe_name = name[:80] if len(name) > 80 else name
        super().__init__(f"Pod not found: {safe_name}")


class NetworkNotFoundError(ToolError):
    """Network does not exist."""

    def __init__(self, name: str) -> None:
        safe_name = name[:80] if len(name) > 80 else name
        super().__init__(f"Network not found: {safe_name}")


class VolumeNotFoundError(ToolError):
    """Volume does not exist."""

    def __init__(self, name: str) -> None:
        safe_name = name[:80] if len(name) > 80 else name
        super().__init__(f"Volume not found: {safe_name}")


class SocketConnectionError(ToolError):
    """Cannot connect to the Podman socket."""

    def __init__(self, socket_path: str) -> None:
        super().__init__(
            f"Cannot connect to Podman socket at {socket_path}. "
            "Ensure the Podman API service is running: "
            "systemctl --user start podman.socket (rootless) or "
            "systemctl start podman.socket (rootful)"
        )


class ConfigurationError(ToolError):
    """Server configuration is invalid."""


class ServiceNotFoundError(ToolError):
    """Systemd unit does not exist."""

    def __init__(self, name: str) -> None:
        safe_name = name[:120] if len(name) > 120 else name
        super().__init__(f"Systemd unit not found: {safe_name}")


class ServiceNotPodmanError(ToolError):
    """Systemd unit does not manage a Podman container."""

    def __init__(self, name: str) -> None:
        safe_name = name[:120] if len(name) > 120 else name
        super().__init__(
            f"Unit '{safe_name}' is not a Podman container service. "
            "Only units with /usr/bin/podman in ExecStart are allowed."
        )


class ServiceOperationError(ToolError):
    """Systemd operation failed."""
