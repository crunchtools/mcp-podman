"""Secure configuration from environment variables.

Unlike most CrunchTools MCP servers, this one has no API token —
authentication is via Unix socket file permissions. The config
is just the socket path and request timeout.
"""

import logging
import os
import stat
from pathlib import Path

from .errors import ConfigurationError

logger = logging.getLogger(__name__)

_config: "Config | None" = None


def get_config() -> "Config":
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


class Config:
    """Podman MCP server configuration."""

    def __init__(self) -> None:
        self._socket_path = self._resolve_socket_path()
        self._timeout = int(os.environ.get("PODMAN_TIMEOUT", "30"))

        self._validate_socket()

    def _resolve_socket_path(self) -> str:
        """Resolve the Podman socket path from env vars or auto-detect."""
        socket_file = os.environ.get("PODMAN_SOCKET_FILE")
        if socket_file:
            path = Path(socket_file)
            if not path.exists():
                raise ConfigurationError(f"PODMAN_SOCKET_FILE does not exist: {socket_file}")
            file_stat = path.stat()
            if file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH):
                logger.warning(
                    "Socket path file %s has permissions more permissive than 0600", socket_file
                )
            return path.read_text().strip()

        explicit = os.environ.get("PODMAN_SOCKET")
        if explicit:
            return explicit

        xdg = os.environ.get("XDG_RUNTIME_DIR")
        if xdg:
            rootless = f"{xdg}/podman/podman.sock"
            if Path(rootless).exists():
                logger.info("Auto-detected rootless socket: %s", rootless)
                return rootless

        uid = os.getuid()
        rootless_fallback = f"/run/user/{uid}/podman/podman.sock"
        if Path(rootless_fallback).exists():
            logger.info("Auto-detected rootless socket: %s", rootless_fallback)
            return rootless_fallback

        rootful = "/run/podman/podman.sock"
        if Path(rootful).exists():
            logger.info("Auto-detected rootful socket: %s", rootful)
            return rootful

        raise ConfigurationError(
            "No Podman socket found. Set PODMAN_SOCKET, start the socket service "
            "(systemctl --user start podman.socket), or run as root for rootful access."
        )

    def _validate_socket(self) -> None:
        """Validate the socket path exists and is a socket."""
        path = Path(self._socket_path)
        if not path.exists():
            raise ConfigurationError(f"Podman socket does not exist: {self._socket_path}")
        if not path.is_socket():
            raise ConfigurationError(f"Path is not a Unix socket: {self._socket_path}")

    @property
    def socket_path(self) -> str:
        """Get the Podman socket path."""
        return self._socket_path

    @property
    def timeout(self) -> int:
        """Get the request timeout in seconds."""
        return self._timeout

    def __repr__(self) -> str:
        return f"Config(socket={self._socket_path})"
