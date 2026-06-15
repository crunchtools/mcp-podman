"""Tool functions for the Podman MCP server."""

from .containers import (
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
)
from .images import (
    image_inspect,
    image_list,
    image_prune,
    image_pull,
    image_rm,
)
from .networks import (
    network_inspect,
    network_list,
)
from .pods import (
    pod_create,
    pod_inspect,
    pod_list,
    pod_restart,
    pod_rm,
    pod_start,
    pod_stop,
)
from .system import (
    system_df,
    system_info,
)
from .volumes import (
    volume_inspect,
    volume_list,
)

__all__ = [
    # Containers
    "container_list",
    "container_inspect",
    "container_start",
    "container_stop",
    "container_restart",
    "container_kill",
    "container_rm",
    "container_logs",
    "container_top",
    "container_stats",
    "container_create",
    "container_prune",
    # Images
    "image_list",
    "image_inspect",
    "image_pull",
    "image_rm",
    "image_prune",
    # Pods
    "pod_list",
    "pod_inspect",
    "pod_start",
    "pod_stop",
    "pod_restart",
    "pod_rm",
    "pod_create",
    # Networks
    "network_list",
    "network_inspect",
    # Volumes
    "volume_list",
    "volume_inspect",
    # System
    "system_info",
    "system_df",
]
