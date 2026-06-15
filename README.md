# mcp-podman-crunchtools

<!-- mcp-name: io.github.crunchtools/podman -->

MCP server for Podman container management via the Podman REST API. Manages containers, images, pods, networks, volumes, and system info. Supports both rootful and rootless Podman.

## Installation

```bash
# uvx (zero-install)
uvx mcp-podman-crunchtools

# pip
pip install mcp-podman-crunchtools

# Container
podman run -v /run/podman/podman.sock:/run/podman/podman.sock:z \
  --security-opt label=type:container_runtime_t \
  quay.io/crunchtools/mcp-podman
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PODMAN_SOCKET` | No | Auto-detect | Unix socket path |
| `PODMAN_SOCKET_FILE` | No | — | File containing socket path |
| `PODMAN_TIMEOUT` | No | 30 | Request timeout in seconds |

Socket auto-detection order:
1. `$XDG_RUNTIME_DIR/podman/podman.sock` (rootless)
2. `/run/user/$UID/podman/podman.sock` (rootless fallback)
3. `/run/podman/podman.sock` (rootful)

## Claude Code Integration

```bash
claude mcp add mcp-podman-crunchtools \
  --env PODMAN_SOCKET=/run/podman/podman.sock \
  -- uvx mcp-podman-crunchtools
```

## Tools (30)

### Containers (12)
| Tool | Description |
|------|-------------|
| `container_list` | List containers |
| `container_inspect` | Get container details |
| `container_start` | Start a container |
| `container_stop` | Stop a container |
| `container_restart` | Restart a container |
| `container_kill` | Send signal to container |
| `container_rm` | Remove a container |
| `container_logs` | Get container logs |
| `container_top` | List processes |
| `container_stats` | Resource usage |
| `container_create` | Create a container |
| `container_prune` | Remove stopped containers |

### Images (5)
| Tool | Description |
|------|-------------|
| `image_list` | List images |
| `image_inspect` | Get image details |
| `image_pull` | Pull from registry |
| `image_rm` | Remove an image |
| `image_prune` | Remove unused images |

### Pods (7)
| Tool | Description |
|------|-------------|
| `pod_list` | List pods |
| `pod_inspect` | Get pod details |
| `pod_start` | Start a pod |
| `pod_stop` | Stop a pod |
| `pod_restart` | Restart a pod |
| `pod_rm` | Remove a pod |
| `pod_create` | Create a pod |

### Networks (2)
| Tool | Description |
|------|-------------|
| `network_list` | List networks |
| `network_inspect` | Get network details |

### Volumes (2)
| Tool | Description |
|------|-------------|
| `volume_list` | List volumes |
| `volume_inspect` | Get volume details |

### System (2)
| Tool | Description |
|------|-------------|
| `system_info` | Podman system info |
| `system_df` | Disk usage |

## License

AGPL-3.0-or-later
