# mcp-podman-crunchtools

MCP server for Podman container management via the Podman REST API over Unix sockets.

## Quick Start

```bash
uv sync --all-extras
uv run pytest -v
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PODMAN_SOCKET` | No | Auto-detect | Unix socket path |
| `PODMAN_SOCKET_FILE` | No | — | File containing socket path |
| `PODMAN_TIMEOUT` | No | 30 | Request timeout (seconds) |

## Tools (36)

### Containers (12)
container_list, container_inspect, container_start, container_stop, container_restart, container_kill, container_rm, container_logs, container_top, container_stats, container_create, container_prune

### Images (5)
image_list, image_inspect, image_pull, image_rm, image_prune

### Pods (7)
pod_list, pod_inspect, pod_start, pod_stop, pod_restart, pod_rm, pod_create

### Services (6) — systemd units managing Podman containers
service_list, service_status, service_restart, service_start, service_stop, service_logs

### Networks (2)
network_list, network_inspect

### Volumes (2)
volume_list, volume_inspect

### System (2)
system_info, system_df

## Development Commands

```bash
uv run ruff check src tests       # Lint
uv run mypy src                    # Type check
uv run pytest -v                   # Tests
gourmand --full .                  # AI slop detection
podman build -f Containerfile .    # Container build
```

## Architecture

Two-layer tool pattern:
- `server.py` — `@mcp.tool()` wrappers with `_tool` suffix
- `tools/*.py` — pure async functions calling `client.py`

Client connects to Podman via httpx `AsyncHTTPTransport(uds=socket_path)`.
Service tools use systemctl CLI (D-Bus internally). Only units with
`/usr/bin/podman` in ExecStart are allowed — non-container services rejected.
