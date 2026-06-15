"""Async D-Bus client for systemd service management.

Talks directly to systemd's D-Bus API over the system bus socket.
Only allows operations on units whose ExecStart contains /usr/bin/podman.

Uses dbus-fast for async D-Bus communication — this works inside
containers without requiring PID 1 to be systemd (unlike systemctl).
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from dbus_fast import Message, MessageType, Variant
from dbus_fast.aio import MessageBus

from .errors import ServiceNotFoundError, ServiceNotPodmanError, ServiceOperationError

logger = logging.getLogger(__name__)

SYSTEM_BUS_SOCKET = "/run/dbus/system_bus_socket"
PODMAN_EXEC_MARKER = "/usr/bin/podman"
SYSTEMD_BUS = "org.freedesktop.systemd1"
SYSTEMD_PATH = "/org/freedesktop/systemd1"
MANAGER_IFACE = "org.freedesktop.systemd1.Manager"
UNIT_IFACE = "org.freedesktop.systemd1.Unit"
SERVICE_IFACE = "org.freedesktop.systemd1.Service"
PROPS_IFACE = "org.freedesktop.DBus.Properties"


async def _get_bus() -> MessageBus:
    """Connect to the system D-Bus."""
    socket_path = Path(SYSTEM_BUS_SOCKET)
    if not socket_path.exists():
        msg = (
            f"D-Bus system bus socket not found at {SYSTEM_BUS_SOCKET}. "
            "Mount it into the container: "
            "-v /run/dbus/system_bus_socket:/run/dbus/system_bus_socket"
        )
        raise ServiceOperationError(msg)
    return await MessageBus(
        bus_address=f"unix:path={SYSTEM_BUS_SOCKET}",
    ).connect()


async def _call(bus: MessageBus, interface: str, member: str,
                signature: str = "", body: list[Any] | None = None,
                path: str = SYSTEMD_PATH) -> Message:
    """Make a D-Bus method call to systemd."""
    msg = Message(
        destination=SYSTEMD_BUS,
        path=path,
        interface=interface,
        member=member,
        signature=signature,
        body=body or [],
    )
    return await bus.call(msg)


async def _get_unit_path(bus: MessageBus, unit_name: str) -> str:
    """Get the D-Bus object path for a systemd unit."""
    reply = await _call(bus, MANAGER_IFACE, "GetUnit", "s", [unit_name])
    if reply.message_type == MessageType.ERROR:
        raise ServiceNotFoundError(unit_name)
    return str(reply.body[0])


async def _get_property(bus: MessageBus, path: str,
                        iface: str, prop: str) -> Any:
    """Get a single property from a D-Bus object."""
    reply = await _call(bus, PROPS_IFACE, "Get", "ss", [iface, prop], path=path)
    if reply.message_type == MessageType.ERROR:
        return None
    val = reply.body[0]
    return val.value if isinstance(val, Variant) else val


async def _is_podman_unit(bus: MessageBus, unit_path: str) -> bool:
    """Check if a systemd unit manages a Podman container."""
    exec_start = await _get_property(bus, unit_path, SERVICE_IFACE, "ExecStart")
    if exec_start is None:
        return False
    return any(PODMAN_EXEC_MARKER in str(entry) for entry in exec_start)


async def _validate_podman_unit(bus: MessageBus, unit_name: str) -> str:
    """Validate unit exists and is a Podman service. Returns the unit path."""
    unit_path = await _get_unit_path(bus, unit_name)

    load_state = await _get_property(bus, unit_path, UNIT_IFACE, "LoadState")
    if load_state == "not-found":
        raise ServiceNotFoundError(unit_name)

    if not await _is_podman_unit(bus, unit_path):
        raise ServiceNotPodmanError(unit_name)

    return unit_path


async def service_list() -> dict[str, Any]:
    """List systemd units that manage Podman containers."""
    bus = await _get_bus()
    try:
        reply = await _call(bus, MANAGER_IFACE, "ListUnits")
        if reply.message_type == MessageType.ERROR:
            raise ServiceOperationError(f"Failed to list units: {reply.body}")

        services = []
        for unit in reply.body[0]:
            name = unit[0]
            if not name.endswith(".service"):
                continue
            unit_path = unit[6]
            if await _is_podman_unit(bus, unit_path):
                services.append({
                    "unit": name,
                    "description": unit[1],
                    "load": unit[2],
                    "active": unit[3],
                    "sub": unit[4],
                })
        return {"items": services, "count": len(services)}
    finally:
        bus.disconnect()


async def service_status(unit_name: str) -> dict[str, Any]:
    """Get the status of a Podman container systemd unit."""
    bus = await _get_bus()
    try:
        unit_path = await _validate_podman_unit(bus, unit_name)
        props: dict[str, Any] = {}
        for prop, iface in [
            ("ActiveState", UNIT_IFACE),
            ("SubState", UNIT_IFACE),
            ("LoadState", UNIT_IFACE),
            ("Description", UNIT_IFACE),
            ("InvocationID", UNIT_IFACE),
            ("MainPID", SERVICE_IFACE),
            ("MemoryCurrent", SERVICE_IFACE),
            ("CPUUsageNSec", SERVICE_IFACE),
            ("Result", SERVICE_IFACE),
        ]:
            value = await _get_property(bus, unit_path, iface, prop)
            props[prop] = str(value) if value is not None else "unknown"
        return {"unit": unit_name, "properties": props}
    finally:
        bus.disconnect()


async def service_restart(unit_name: str) -> dict[str, Any]:
    """Restart a Podman container systemd unit."""
    bus = await _get_bus()
    try:
        await _validate_podman_unit(bus, unit_name)
        reply = await _call(bus, MANAGER_IFACE, "RestartUnit", "ss", [unit_name, "replace"])
        if reply.message_type == MessageType.ERROR:
            raise ServiceOperationError(f"Failed to restart {unit_name}: {reply.body}")
        return {"status": "restarted", "unit": unit_name}
    finally:
        bus.disconnect()


async def service_start(unit_name: str) -> dict[str, Any]:
    """Start a Podman container systemd unit."""
    bus = await _get_bus()
    try:
        await _validate_podman_unit(bus, unit_name)
        reply = await _call(bus, MANAGER_IFACE, "StartUnit", "ss", [unit_name, "replace"])
        if reply.message_type == MessageType.ERROR:
            raise ServiceOperationError(f"Failed to start {unit_name}: {reply.body}")
        return {"status": "started", "unit": unit_name}
    finally:
        bus.disconnect()


async def service_stop(unit_name: str) -> dict[str, Any]:
    """Stop a Podman container systemd unit."""
    bus = await _get_bus()
    try:
        await _validate_podman_unit(bus, unit_name)
        reply = await _call(bus, MANAGER_IFACE, "StopUnit", "ss", [unit_name, "replace"])
        if reply.message_type == MessageType.ERROR:
            raise ServiceOperationError(f"Failed to stop {unit_name}: {reply.body}")
        return {"status": "stopped", "unit": unit_name}
    finally:
        bus.disconnect()


async def service_logs(
    unit_name: str, lines: int = 50, since: str | None = None,
) -> dict[str, Any]:
    """Get journal logs for a Podman container systemd unit."""
    bus = await _get_bus()
    try:
        await _validate_podman_unit(bus, unit_name)
    finally:
        bus.disconnect()

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
