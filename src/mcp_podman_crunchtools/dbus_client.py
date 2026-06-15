"""Async D-Bus client for systemd service management.

Uses the systemd D-Bus API to manage units. Only allows operations
on units whose ExecStart contains /usr/bin/podman — this prevents
managing non-container services like sshd or firewalld.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from .errors import ServiceNotFoundError, ServiceNotPodmanError, ServiceOperationError

logger = logging.getLogger(__name__)

SYSTEM_BUS_SOCKET = "/run/dbus/system_bus_socket"
PODMAN_EXEC_MARKER = "/usr/bin/podman"


def _get_dbus_socket() -> str:
    """Get the D-Bus system bus socket path."""
    path = Path(SYSTEM_BUS_SOCKET)
    if not path.exists():
        msg = (
            f"D-Bus system bus socket not found at {SYSTEM_BUS_SOCKET}. "
            "Mount it into the container: "
            "-v /run/dbus/system_bus_socket:/run/dbus/system_bus_socket:z"
        )
        raise ServiceOperationError(msg)
    return str(path)


async def _run_systemctl(*args: str) -> str:
    """Run a systemctl command and return its output.

    This uses systemctl CLI over the D-Bus socket rather than raw D-Bus
    protocol, which is simpler and equally capable for our needs.
    The systemctl binary communicates with systemd via D-Bus internally.
    """
    cmd = ["systemctl", *args]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    output = stdout.decode().strip()
    if proc.returncode != 0:
        error = stderr.decode().strip() or output
        raise ServiceOperationError(f"systemctl {' '.join(args)} failed: {error}")
    return output


async def _is_podman_unit(unit_name: str) -> bool:
    """Check if a systemd unit manages a Podman container."""
    try:
        output = await _run_systemctl("show", unit_name, "--property=ExecStart", "--no-pager")
    except ServiceOperationError:
        return False
    return PODMAN_EXEC_MARKER in output


async def _validate_podman_unit(unit_name: str) -> None:
    """Validate that a unit exists and manages a Podman container."""
    try:
        load_state = await _run_systemctl(
            "show", unit_name, "--property=LoadState", "--value", "--no-pager",
        )
    except ServiceOperationError as e:
        raise ServiceNotFoundError(unit_name) from e

    if load_state == "not-found":
        raise ServiceNotFoundError(unit_name)

    if not await _is_podman_unit(unit_name):
        raise ServiceNotPodmanError(unit_name)


async def service_list() -> dict[str, Any]:
    """List systemd units that manage Podman containers."""
    output = await _run_systemctl(
        "list-units", "--type=service", "--all", "--no-legend", "--no-pager",
        "--plain", "--full",
    )
    services = []
    for line in output.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 4:
            continue
        unit_name = parts[0]
        if not unit_name.endswith(".service"):
            continue
        if await _is_podman_unit(unit_name):
            services.append({
                "unit": unit_name,
                "load": parts[1],
                "active": parts[2],
                "sub": parts[3],
                "description": parts[4] if len(parts) > 4 else "",
            })
    return {"items": services, "count": len(services)}


async def service_status(unit_name: str) -> dict[str, Any]:
    """Get the status of a Podman container systemd unit."""
    await _validate_podman_unit(unit_name)
    props = {}
    for prop in [
        "ActiveState", "SubState", "LoadState", "Description",
        "MainPID", "ExecMainStartTimestamp", "MemoryCurrent",
        "CPUUsageNSec", "InvocationID", "Result",
    ]:
        try:
            value = await _run_systemctl(
                "show", unit_name, f"--property={prop}", "--value", "--no-pager",
            )
            props[prop] = value
        except ServiceOperationError:
            props[prop] = "unknown"
    return {"unit": unit_name, "properties": props}


async def service_restart(unit_name: str) -> dict[str, Any]:
    """Restart a Podman container systemd unit."""
    await _validate_podman_unit(unit_name)
    await _run_systemctl("restart", unit_name)
    return {"status": "restarted", "unit": unit_name}


async def service_start(unit_name: str) -> dict[str, Any]:
    """Start a Podman container systemd unit."""
    await _validate_podman_unit(unit_name)
    await _run_systemctl("start", unit_name)
    return {"status": "started", "unit": unit_name}


async def service_stop(unit_name: str) -> dict[str, Any]:
    """Stop a Podman container systemd unit."""
    await _validate_podman_unit(unit_name)
    await _run_systemctl("stop", unit_name)
    return {"status": "stopped", "unit": unit_name}


async def service_logs(
    unit_name: str, lines: int = 50, since: str | None = None,
) -> dict[str, Any]:
    """Get journal logs for a Podman container systemd unit."""
    await _validate_podman_unit(unit_name)
    args = ["journalctl", "-u", unit_name, "--no-pager", f"-n{lines}"]
    if since:
        args.extend(["--since", since])
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _stderr = await proc.communicate()
    return {"unit": unit_name, "logs": stdout.decode()}
