# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

Entries prior to 2026-09-19 are back-filled from GitHub Release notes (RT #1484).

## [Unreleased]

## [1.2.0] - 2026-10-10

### Added
- The fourteen tools that only read (`container_list`, `container_inspect`,
  `container_logs`, `container_stats`, `image_list`, `image_inspect`, `pod_list`,
  `pod_inspect`, `network_list`, `network_inspect`, `volume_list`, `volume_inspect`,
  `system_info`, `system_df`) publish `readOnlyHint: true`. A gateway uses it to
  decide whether an invalid optional argument may be dropped or must refuse the
  call (crunchtools/constitution#35). `container_top` is a GET but stays
  unannotated: libpod runs `ps` with the caller's `ps_args`, from the host or
  through an exec session in the container.
- Tests pin every registered tool into `READ_ONLY` or `WRITES`, and check that
  each read-only tool sends only GET requests, with a write tool as the control.

### Fixed
- Image, pod, network and volume names are URL-encoded as one path segment, as
  container names already were. Unencoded, `../containers/x/healthcheck?` passed
  to an inspect tool addressed `GET /containers/x/healthcheck`, which runs the
  container's health check.
- A resource name of `.`, `..`, the empty string, or more than 500 characters
  is rejected before any request is sent, for containers as well. URL-encoding
  leaves dots alone, and the HTTP client resolved `/pods/../json` to `/json`.

### Changed
- Inherits constitution v1.22.0; the workflow pins and the pre-commit hook rev
  move with it.
- Constitution is now a v1.18.0 manifest: only repo-specific facts remain;
  fleet and profile rules apply by reference.
- Constitution validation is pinned via `.github/workflows/constitution.yml`.
- Dependabot auto-merges GitHub Actions minor and patch updates.

## [1.1.0] - 2026-10-02

### Added
- `image_prune` takes the options of `podman image prune`: `all` (every image not used
  by a container, not just dangling ones), `external`, `build_cache`, and `filters`
  (`until`, `label`, `label!`, `dangling`). With no arguments it still removes only
  dangling images, which on a host that pulls tagged images reclaims almost nothing.
  Filter keys outside that set, and values over 255 characters, are rejected.

### Changed
- `image_prune` allows the request 600 seconds instead of `PODMAN_TIMEOUT`; removing many
  gigabytes of layers outlasts the default.

## [1.0.1] - 2026-10-01

### Security
- `container_inspect` redacts environment values. libpod returns every variable with its
  value in `Config.Env`, and the full `podman run` command, inline `-e NAME=value`
  included, in `Config.CreateCommand`; the tool passed both through to the calling model.
  Inspecting a container handed over whatever credentials it was started with. Names are
  kept, every value is replaced with `<redacted>`.
- Container names and IDs are URL-encoded as one path segment in every container
  endpoint. Unencoded, a name such as `../images/x` addressed a different endpoint.

### Fixed
- `image_pull` no longer reports every successful pull as "Invalid JSON response". libpod
  streams the pull as newline-delimited JSON, and the client parsed the whole body as one
  document. Streamed responses now return the final report, and an in-band `error`
  (a pull that fails after the 200) is raised instead of passing as success.
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
