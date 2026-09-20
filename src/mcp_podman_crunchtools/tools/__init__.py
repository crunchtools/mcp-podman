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
    "container_create",
    "container_inspect",
    "container_kill",
    "container_list",
    "container_logs",
    "container_prune",
    "container_restart",
    "container_rm",
    "container_start",
    "container_stats",
    "container_stop",
    "container_top",
    "image_inspect",
    "image_list",
    "image_prune",
    "image_pull",
    "image_rm",
    "network_inspect",
    "network_list",
    "pod_create",
    "pod_inspect",
    "pod_list",
    "pod_restart",
    "pod_rm",
    "pod_start",
    "pod_stop",
    "system_df",
    "system_info",
    "volume_inspect",
    "volume_list",
]
