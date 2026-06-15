"""FastMCP server setup for Podman MCP."""

import logging
from typing import Any

from fastmcp import FastMCP

from .tools import (
    container_create,
    container_inspect,
    container_kill,
    container_list,
    container_logs,
    container_prune,
    container_restart,
    container_rm,
    container_start,
    container_stats,
    container_stop,
    container_top,
    image_inspect,
    image_list,
    image_prune,
    image_pull,
    image_rm,
    network_inspect,
    network_list,
    pod_create,
    pod_inspect,
    pod_list,
    pod_restart,
    pod_rm,
    pod_start,
    pod_stop,
    service_list,
    service_logs,
    service_restart,
    service_start,
    service_status,
    service_stop,
    system_df,
    system_info,
    volume_inspect,
    volume_list,
)

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="mcp-podman-crunchtools",
    version="0.2.0",
    instructions=(
        "MCP server for Podman container management via the Podman REST API. "
        "Manages containers, images, pods, networks, volumes, and system info. "
        "Supports both rootful and rootless Podman."
    ),
)


# --- Container Tools ---


@mcp.tool()
async def container_list_tool(
    all_containers: bool = False,
    filters: dict[str, list[str]] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """List containers.

    Args:
        all_containers: Show all containers (default shows only running)
        filters: Filter by key/value pairs (e.g. {"name": ["myapp"]})
        limit: Maximum number of containers to return

    Returns:
        List of containers with count
    """
    return await container_list(all_containers=all_containers, filters=filters, limit=limit)


@mcp.tool()
async def container_inspect_tool(name: str) -> dict[str, Any]:
    """Get detailed information about a container.

    Args:
        name: Container name or ID

    Returns:
        Container details including config, state, and network settings
    """
    return await container_inspect(name)


@mcp.tool()
async def container_start_tool(name: str) -> dict[str, Any]:
    """Start a stopped container.

    Args:
        name: Container name or ID

    Returns:
        Start result
    """
    return await container_start(name)


@mcp.tool()
async def container_stop_tool(name: str, timeout: int = 10) -> dict[str, Any]:
    """Stop a running container.

    Args:
        name: Container name or ID
        timeout: Seconds to wait before killing (default: 10)

    Returns:
        Stop result
    """
    return await container_stop(name, timeout=timeout)


@mcp.tool()
async def container_restart_tool(name: str, timeout: int = 10) -> dict[str, Any]:
    """Restart a container.

    Args:
        name: Container name or ID
        timeout: Seconds to wait before killing (default: 10)

    Returns:
        Restart result
    """
    return await container_restart(name, timeout=timeout)


@mcp.tool()
async def container_kill_tool(name: str, signal: str = "SIGTERM") -> dict[str, Any]:
    """Send a signal to a container.

    Args:
        name: Container name or ID
        signal: Signal to send (default: SIGTERM)

    Returns:
        Kill result
    """
    return await container_kill(name, signal=signal)


@mcp.tool()
async def container_rm_tool(
    name: str, force: bool = False, volumes: bool = False,
) -> dict[str, Any]:
    """Remove a container.

    Args:
        name: Container name or ID
        force: Force removal of running container
        volumes: Remove associated anonymous volumes

    Returns:
        Removal result
    """
    return await container_rm(name, force=force, volumes=volumes)


@mcp.tool()
async def container_logs_tool(
    name: str,
    tail: int | None = None,
    since: str | None = None,
    timestamps: bool = False,
) -> dict[str, Any]:
    """Get container logs.

    Args:
        name: Container name or ID
        tail: Number of lines from the end of the logs
        since: Show logs since timestamp (e.g. "2024-01-01T00:00:00Z")
        timestamps: Add timestamps to each log line

    Returns:
        Container log output
    """
    return await container_logs(name, tail=tail, since=since, timestamps=timestamps)


@mcp.tool()
async def container_top_tool(name: str, ps_args: str | None = None) -> dict[str, Any]:
    """List processes running inside a container.

    Args:
        name: Container name or ID
        ps_args: Arguments to pass to ps (e.g. "aux")

    Returns:
        Process list with titles and entries
    """
    return await container_top(name, ps_args=ps_args)


@mcp.tool()
async def container_stats_tool(name: str) -> dict[str, Any]:
    """Get container resource usage statistics.

    Args:
        name: Container name or ID

    Returns:
        CPU, memory, network, and block I/O statistics
    """
    return await container_stats(name, stream=False)


@mcp.tool()
async def container_create_tool(
    image: str,
    name: str | None = None,
    command: list[str] | None = None,
    env: dict[str, str] | None = None,
    labels: dict[str, str] | None = None,
    volumes: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new container.

    Args:
        image: Container image (e.g. "registry.access.redhat.com/ubi9/ubi:latest")
        name: Container name
        command: Command to run
        env: Environment variables
        labels: Container labels
        volumes: Volume mounts (format: "host_path:container_path[:options]")

    Returns:
        Created container ID and warnings
    """
    return await container_create(
        image=image, name=name, command=command, env=env, labels=labels, volumes=volumes,
    )


@mcp.tool()
async def container_prune_tool() -> dict[str, Any]:
    """Remove all stopped containers.

    Returns:
        List of removed container IDs and reclaimed space
    """
    return await container_prune()


# --- Image Tools ---


@mcp.tool()
async def image_list_tool(
    filters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """List images.

    Args:
        filters: Filter by key/value pairs (e.g. {"reference": ["ubi9"]})

    Returns:
        List of images with count
    """
    return await image_list(filters=filters)


@mcp.tool()
async def image_inspect_tool(name: str) -> dict[str, Any]:
    """Get detailed information about an image.

    Args:
        name: Image name, tag, or ID

    Returns:
        Image details including layers, config, and history
    """
    return await image_inspect(name)


@mcp.tool()
async def image_pull_tool(reference: str) -> dict[str, Any]:
    """Pull an image from a registry.

    Args:
        reference: Image reference (e.g. "quay.io/crunchtools/rotv:latest")

    Returns:
        Pull result with image ID
    """
    return await image_pull(reference)


@mcp.tool()
async def image_rm_tool(name: str, force: bool = False) -> dict[str, Any]:
    """Remove an image.

    Args:
        name: Image name, tag, or ID
        force: Force removal even if in use

    Returns:
        Removal result
    """
    return await image_rm(name, force=force)


@mcp.tool()
async def image_prune_tool() -> dict[str, Any]:
    """Remove unused images.

    Returns:
        List of removed image IDs and reclaimed space
    """
    return await image_prune()


# --- Pod Tools ---


@mcp.tool()
async def pod_list_tool(
    filters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """List pods.

    Args:
        filters: Filter by key/value pairs (e.g. {"name": ["mypod"]})

    Returns:
        List of pods with count
    """
    return await pod_list(filters=filters)


@mcp.tool()
async def pod_inspect_tool(name: str) -> dict[str, Any]:
    """Get detailed information about a pod.

    Args:
        name: Pod name or ID

    Returns:
        Pod details including containers and state
    """
    return await pod_inspect(name)


@mcp.tool()
async def pod_start_tool(name: str) -> dict[str, Any]:
    """Start a pod and all its containers.

    Args:
        name: Pod name or ID

    Returns:
        Start result
    """
    return await pod_start(name)


@mcp.tool()
async def pod_stop_tool(name: str, timeout: int = 10) -> dict[str, Any]:
    """Stop a pod and all its containers.

    Args:
        name: Pod name or ID
        timeout: Seconds to wait before killing (default: 10)

    Returns:
        Stop result
    """
    return await pod_stop(name, timeout=timeout)


@mcp.tool()
async def pod_restart_tool(name: str) -> dict[str, Any]:
    """Restart a pod and all its containers.

    Args:
        name: Pod name or ID

    Returns:
        Restart result
    """
    return await pod_restart(name)


@mcp.tool()
async def pod_rm_tool(name: str, force: bool = False) -> dict[str, Any]:
    """Remove a pod and all its containers.

    Args:
        name: Pod name or ID
        force: Force removal of running pod

    Returns:
        Removal result
    """
    return await pod_rm(name, force=force)


@mcp.tool()
async def pod_create_tool(
    name: str,
    labels: dict[str, str] | None = None,
    infra: bool = True,
    share: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new pod.

    Args:
        name: Pod name
        labels: Pod labels
        infra: Create an infra container (default: True)
        share: Namespaces to share (ipc, net, uts, pid)

    Returns:
        Created pod ID
    """
    return await pod_create(name=name, labels=labels, infra=infra, share=share)


# --- Network Tools ---


@mcp.tool()
async def network_list_tool(
    filters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """List networks.

    Args:
        filters: Filter by key/value pairs

    Returns:
        List of networks with count
    """
    return await network_list(filters=filters)


@mcp.tool()
async def network_inspect_tool(name: str) -> dict[str, Any]:
    """Get detailed information about a network.

    Args:
        name: Network name or ID

    Returns:
        Network details including subnets and connected containers
    """
    return await network_inspect(name)


# --- Volume Tools ---


@mcp.tool()
async def volume_list_tool(
    filters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """List volumes.

    Args:
        filters: Filter by key/value pairs

    Returns:
        List of volumes with count
    """
    return await volume_list(filters=filters)


@mcp.tool()
async def volume_inspect_tool(name: str) -> dict[str, Any]:
    """Get detailed information about a volume.

    Args:
        name: Volume name

    Returns:
        Volume details including mount point and driver
    """
    return await volume_inspect(name)


# --- Service Tools (systemd units managing Podman containers) ---


@mcp.tool()
async def service_list_tool() -> dict[str, Any]:
    """List systemd units that manage Podman containers.

    Only shows units whose ExecStart contains /usr/bin/podman.
    Non-container services (sshd, firewalld, etc.) are excluded.

    Returns:
        List of Podman container service units with status
    """
    return await service_list()


@mcp.tool()
async def service_status_tool(unit_name: str) -> dict[str, Any]:
    """Get the status of a Podman container systemd unit.

    Args:
        unit_name: Systemd unit name (e.g. "acquacotta.crunchtools.com.service")

    Returns:
        Unit properties including ActiveState, MainPID, memory, CPU usage
    """
    return await service_status(unit_name)


@mcp.tool()
async def service_restart_tool(unit_name: str) -> dict[str, Any]:
    """Restart a Podman container systemd unit.

    This is the correct way to bounce containers on systems where
    containers are managed by systemd. Using podman restart directly
    would conflict with systemd's process management.

    Args:
        unit_name: Systemd unit name (e.g. "acquacotta.crunchtools.com.service")

    Returns:
        Restart confirmation
    """
    return await service_restart(unit_name)


@mcp.tool()
async def service_start_tool(unit_name: str) -> dict[str, Any]:
    """Start a Podman container systemd unit.

    Args:
        unit_name: Systemd unit name (e.g. "acquacotta.crunchtools.com.service")

    Returns:
        Start confirmation
    """
    return await service_start(unit_name)


@mcp.tool()
async def service_stop_tool(unit_name: str) -> dict[str, Any]:
    """Stop a Podman container systemd unit.

    Args:
        unit_name: Systemd unit name (e.g. "acquacotta.crunchtools.com.service")

    Returns:
        Stop confirmation
    """
    return await service_stop(unit_name)


@mcp.tool()
async def service_logs_tool(
    unit_name: str, lines: int = 50, since: str | None = None,
) -> dict[str, Any]:
    """Get journal logs for a Podman container systemd unit.

    Args:
        unit_name: Systemd unit name (e.g. "acquacotta.crunchtools.com.service")
        lines: Number of log lines to return (default: 50)
        since: Show logs since timestamp (e.g. "1 hour ago", "2024-01-01")

    Returns:
        Journal log output for the unit
    """
    return await service_logs(unit_name, lines=lines, since=since)


# --- System Tools ---


@mcp.tool()
async def system_info_tool() -> dict[str, Any]:
    """Get Podman system information.

    Returns:
        System details including version, storage, registries, and runtime
    """
    return await system_info()


@mcp.tool()
async def system_df_tool() -> dict[str, Any]:
    """Get Podman disk usage.

    Returns:
        Disk usage by images, containers, and volumes
    """
    return await system_df()
