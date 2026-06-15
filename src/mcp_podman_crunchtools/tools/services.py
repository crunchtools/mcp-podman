"""Systemd service management tools for Podman container units.

Only operates on systemd units whose ExecStart contains /usr/bin/podman.
Rejects operations on non-container services (sshd, firewalld, etc.).
"""

from typing import Any

from ..dbus_client import (
    service_list as _service_list,
)
from ..dbus_client import (
    service_logs as _service_logs,
)
from ..dbus_client import (
    service_restart as _service_restart,
)
from ..dbus_client import (
    service_start as _service_start,
)
from ..dbus_client import (
    service_status as _service_status,
)
from ..dbus_client import (
    service_stop as _service_stop,
)


async def service_list() -> dict[str, Any]:
    """List systemd units that manage Podman containers."""
    return await _service_list()


async def service_status(unit_name: str) -> dict[str, Any]:
    """Get the status of a Podman container systemd unit."""
    return await _service_status(unit_name)


async def service_restart(unit_name: str) -> dict[str, Any]:
    """Restart a Podman container systemd unit."""
    return await _service_restart(unit_name)


async def service_start(unit_name: str) -> dict[str, Any]:
    """Start a Podman container systemd unit."""
    return await _service_start(unit_name)


async def service_stop(unit_name: str) -> dict[str, Any]:
    """Stop a Podman container systemd unit."""
    return await _service_stop(unit_name)


async def service_logs(
    unit_name: str, lines: int = 50, since: str | None = None,
) -> dict[str, Any]:
    """Get journal logs for a Podman container systemd unit."""
    return await _service_logs(unit_name, lines=lines, since=since)
