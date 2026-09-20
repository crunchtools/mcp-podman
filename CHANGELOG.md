# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

Entries prior to 2026-09-19 are back-filled from GitHub Release notes (RT #1484).

## [Unreleased]

### Fixed
- `container_logs` now routes through the shared request path. Mid-stream transport
  failures (`ReadError`, `RemoteProtocolError`) during a log fetch escaped as raw httpx
  exceptions instead of typed errors, and the call bypassed the `MAX_RESPONSE_SIZE`
  guard entirely — the one endpoint most likely to return tens of megabytes had no cap.
- A hung Podman socket now returns the socket remediation message. `httpx.ConnectTimeout`
  subclasses `TimeoutException` rather than `ConnectError`, so it fell through to the
  generic "Request timeout" path and lost the `systemctl start podman.socket` hint.

### Added
- `TestClientErrorHandling` covering the transport and HTTP error paths (profile
  section IV). `tests/conftest.py` gains `_patch_client_raising()` for injecting
  transport exceptions, and `test_container_logs` no longer patches out `get_text`,
  the method it is meant to exercise.

## [1.0.0] - 2026-09-19

### Removed
- **Breaking change:** the six `service_*` tools are removed. 36 tools → 30.

  | removed | use instead (mcp-systemd) |
  |---|---|
  | `service_list_tool` | `unit_list_tool(pattern=...)` |
  | `service_status_tool` | `unit_status_tool` |
  | `service_start_tool` | `unit_start_tool` |
  | `service_stop_tool` | `unit_stop_tool` |
  | `service_restart_tool` | `unit_restart_tool` |
  | `service_logs_tool` | `journal_query_tool(unit=..., lines=..., since=...)` |

  The old tools only matched units whose `ExecStart` contained `/usr/bin/podman`,
  so they could not touch any non-container unit.
  [mcp-systemd](https://github.com/crunchtools/mcp-systemd) drops that filter and
  guards the wider scope with a protected-unit denylist instead (RT #1465).
- The `dbus-fast` dependency — nothing in this server talks to D-Bus any more.

## [0.2.2] - 2026-06-15

### Fixed
- Switched from the systemctl CLI to dbus-fast for D-Bus communication.
  systemctl refuses to run inside containers when PID 1 isn't systemd.

## [0.2.1] - 2026-06-15

### Fixed
- Copy `libsystemd-shared` into the container. systemctl dynamically loads it
  from `/usr/lib64/systemd/` at runtime — `ldd` doesn't catch it.

## [0.2.0] - 2026-06-15

### Added
- 6 new tools for managing systemd units that run Podman containers:
  `service_list` (list Podman container service units), `service_status` (unit
  status — ActiveState, PID, memory, CPU), `service_restart` (the correct way to
  bounce containers), `service_start` / `service_stop`, and `service_logs`
  (journalctl output for a unit). Total tools: 36 (was 30).

### Security
- Only units whose `ExecStart` contains `/usr/bin/podman` are allowed. Operations
  on non-container services (sshd, firewalld, etc.) are rejected.

## [0.1.1] - 2026-06-15

### Changed
- Added the MCP Registry name tag to the README for registry publishing.

## [0.1.0] - 2026-06-14

Initial release of mcp-podman-crunchtools.

### Added
- MCP server for Podman container management via the Podman REST API over Unix
  sockets. 30 tools across 6 categories — Containers (12): list, inspect, start,
  stop, restart, kill, rm, logs, top, stats, create, prune; Images (5): list,
  inspect, pull, rm, prune; Pods (7): list, inspect, start, stop, restart, rm,
  create; Networks (2): list, inspect; Volumes (2): list, inspect; System (2):
  info, df.
- Support for both rootful and rootless Podman.
