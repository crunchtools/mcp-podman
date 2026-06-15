# mcp-podman-crunchtools Constitution

> **Version:** 0.1.0
> **Ratified:** 2026-06-14
> **Status:** Active
> **Inherits:** [crunchtools/constitution](https://github.com/crunchtools/constitution) v1.0.0
> **Profile:** MCP Server

## Project Identity

**Name:** mcp-podman-crunchtools
**Purpose:** MCP server for Podman container management via the Podman REST API over Unix sockets. Supports both rootful and rootless Podman.

## Credentials

| Variable | Purpose |
|----------|---------|
| `PODMAN_SOCKET` | Path to the Podman Unix socket |
| `PODMAN_SOCKET_FILE` | File containing the socket path (preferred for containers) |
| `PODMAN_TIMEOUT` | Request timeout in seconds (default: 30) |

## Deployment

| Key | Value |
|-----|-------|
| HTTP Port | 8023 |
| systemd Service | `mcp-podman.service` |
| Container (Quay) | `quay.io/crunchtools/mcp-podman` |
| Container (GHCR) | `ghcr.io/crunchtools/mcp-podman` |

## Project-Specific Requirements

1. The server communicates with Podman via the REST API over Unix domain sockets — never via shell commands or subprocess.
2. Socket auto-detection tries rootless first, then rootful.
3. When running in a container, the host Podman socket must be mounted with `:z` (SELinux relabel) and the container must use `--security-opt label=type:container_runtime_t`.
