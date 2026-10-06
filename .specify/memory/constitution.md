# mcp-podman-crunchtools Constitution

> **Version:** 0.2.0
> **Ratified:** 2026-06-14
> **Amended:** 2026-10-02
> **Status:** Active
> **Inherits:** [crunchtools/constitution](https://github.com/crunchtools/constitution) v1.20.0
> **Profile:** MCP Server

This file holds what is specific to mcp-podman. The fleet rules and the MCP
Server profile (five-layer security model, two-layer tools, distribution
channels, transport modes, quality gates, Gourmand) apply at the inherited
version and are checked against this repo's files by `constitution.yml`. They
are not restated here.

## Security Model Specifics

- **Credentials:** none. Authentication is the Unix socket's file
  permissions; there are no API tokens. A socket more permissive than 0600
  raises a warning.
- **Input limits:** container, image and pod names are validated before any
  API call; every user-provided string is length-bounded.
- **API:** the Podman REST API over a Unix domain socket, never a network
  listener. Responses above 10 MB are rejected, requests time out, and path
  parameters are URL-encoded to prevent traversal.
- **Surface:** pure Podman REST API wrappers. No filesystem access, shell
  execution or code evaluation.

## Socket Discovery

The server MUST work with both rootless and rootful Podman. The socket is
resolved in this order:

1. `PODMAN_SOCKET`, an explicit path
2. `PODMAN_SOCKET_FILE`, a file containing the path (preferred in containers)
3. Auto-detect: rootless `$XDG_RUNTIME_DIR/podman/podman.sock`, then rootful
   `/run/podman/podman.sock`

## SELinux and Socket Mount

When the container runs with the host Podman socket mounted:

- run it with `--security-opt label=type:container_runtime_t`, the domain
  that can `connectto` the Podman socket;
- mount the socket with the `:z` relabel flag.

## Instance

| Context | Name |
|---------|------|
| GitHub repo | `crunchtools/mcp-podman` |
| PyPI package | `mcp-podman-crunchtools` |
| Python module | `mcp_podman_crunchtools` |
| Container image | `quay.io/crunchtools/mcp-podman` |
| systemd service | `mcp-podman.service` |
| HTTP port | 8023 |

## History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-06-14 | Initial constitution |
| 0.2.0 | 2026-10-02 | Manifest under constitution v1.18.0: profile restatement removed, mcp-podman specifics kept |
