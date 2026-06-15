# mcp-podman-crunchtools Constitution

> **Version:** 0.1.0
> **Ratified:** 2026-06-14
> **Status:** Active
> **Inherits:** [crunchtools/constitution](https://github.com/crunchtools/constitution) v1.0.0
> **Profile:** MCP Server

This constitution establishes the core principles, constraints, and workflows that govern all development on mcp-podman-crunchtools.

---

## I. Core Principles

### 1. Five-Layer Security Model

Every change MUST preserve all five security layers. No exceptions.

**Layer 1 — Credential Protection:**
- This server uses Unix socket file permissions for authentication — no API tokens
- Socket path loaded from `PODMAN_SOCKET` or `PODMAN_SOCKET_FILE` (per `SecretStr`-equivalent file-based pattern)
- Socket file permission warnings when more permissive than 0600

**Layer 2 — Input Validation:**
- Pydantic models enforce strict data types with `extra="forbid"`
- Container/image/pod names validated before API calls
- Field length limits on all user-provided strings

**Layer 3 — API Hardening:**
- Communication via Unix domain socket (not network-exposed)
- Request timeouts and response size limits (10MB)
- URL-encoded path parameters to prevent path traversal

**Layer 4 — Dangerous Operation Prevention:**
- No filesystem access, shell execution, or code evaluation
- No `eval()`/`exec()` functions
- Tools are pure Podman REST API wrappers with no side effects

**Layer 5 — Supply Chain Security:**
- Weekly automated CVE scanning via GitHub Actions
- Hummingbird container base images (minimal CVE surface)
- Gourmand AI slop detection gating all PRs

### 2. Two-Layer Tool Architecture

Tools follow a strict two-layer pattern:
- `server.py` — `@mcp.tool()` decorated functions that validate args and delegate
- `tools/*.py` — Pure async functions that call `client.py` HTTP methods

Never put business logic in `server.py`. Never put MCP registration in `tools/*.py`.

### 3. Socket Auto-Detection

The server MUST work with both rootless and rootful Podman:
- `PODMAN_SOCKET` explicit path (highest priority)
- `PODMAN_SOCKET_FILE` file containing the path (preferred for containers)
- Auto-detect: rootless (`$XDG_RUNTIME_DIR/podman/podman.sock`) then rootful (`/run/podman/podman.sock`)

### 4. Three Distribution Channels

Every release MUST be available through all three channels simultaneously:

| Channel | Command | Use Case |
|---------|---------|----------|
| uvx | `uvx mcp-podman-crunchtools` | Zero-install, Claude Code |
| pip | `pip install mcp-podman-crunchtools` | Virtual environments |
| Container | `podman run quay.io/crunchtools/mcp-podman` | Isolated, systemd |

### 5. Three Transport Modes

The server MUST support all three MCP transports:
- **stdio** (default) — spawned per-session by Claude Code
- **SSE** — legacy HTTP transport
- **streamable-http** — production HTTP, systemd-managed containers

### 6. Semantic Versioning

Follow [Semantic Versioning 2.0.0](https://semver.org/) strictly.

**MAJOR** (breaking changes): Removed/renamed tools, changed parameters
**MINOR** (new functionality): New tools, new optional parameters
**PATCH** (fixes): Bug fixes, security patches, test improvements

### 7. AI Code Quality

All code MUST pass Gourmand checks before merge. Zero violations required.

---

## II. Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.10+ |
| MCP Framework | FastMCP | Latest |
| HTTP Client | httpx | Latest |
| Validation | Pydantic | v2 |
| Container Base | Hummingbird | Latest |
| Package Manager | uv | Latest |
| Build System | hatchling | Latest |
| Linter | ruff | Latest |
| Type Checker | mypy (strict) | Latest |
| Tests | pytest + pytest-asyncio | Latest |
| Slop Detector | gourmand | Latest |

---

## III. Testing Standards

### Mocked API Tests (MANDATORY)

Every tool MUST have a corresponding mocked test. Tests use `httpx.AsyncClient` mocking — no live API calls, no sockets required in CI.

**Pattern:**
1. Build a mock `httpx.Response` with `_mock_response()` helper
2. Patch `PodmanClient._get_client` via `_patch_client()` context manager
3. Call the tool function directly (not the `_tool` wrapper)
4. Assert response structure and values

**Singleton reset:** The `_reset_client_singleton` autouse fixture resets `client._client` and `config._config` between every test.

**Tool count assertion:** `test_tool_count` MUST be updated whenever tools are added or removed.

### Input Validation Tests

Every Pydantic model MUST have tests in `test_validation.py`:
- Valid minimal input
- Valid full input
- Invalid/rejected inputs (empty strings, too-long values, extra fields)

---

## IV. Gourmand (AI Slop Detection)

All code MUST pass `gourmand --full .` with **zero violations** before merge.

### Configuration

- `gourmand.toml` — Check settings, excluded paths
- `gourmand-exceptions.toml` — Documented exceptions with justifications
- `.gourmand-cache/` — Must be in `.gitignore`

### Exception Policy

Exceptions MUST have documented justifications in `gourmand-exceptions.toml`. Acceptable reasons:
- Standard API patterns (HTTP status codes, timeout defaults)
- Test-specific patterns (intentional invalid input)
- Framework requirements (CLAUDE.md for Claude Code)

---

## V. Code Quality Gates

Every code change must pass through these gates in order:

1. **Lint** — `uv run ruff check src tests`
2. **Type Check** — `uv run mypy src`
3. **Tests** — `uv run pytest -v` (all passing, mocked httpx)
4. **Gourmand** — `gourmand --full .` (zero violations)
5. **Container Build** — `podman build -f Containerfile .`

---

## VI. Naming Conventions

| Context | Name |
|---------|------|
| GitHub repo | `crunchtools/mcp-podman` |
| PyPI package | `mcp-podman-crunchtools` |
| CLI command | `mcp-podman-crunchtools` |
| Python module | `mcp_podman_crunchtools` |
| Container image | `quay.io/crunchtools/mcp-podman` |
| systemd service | `mcp-podman.service` |
| HTTP port | 8023 |
| License | AGPL-3.0-or-later |

---

## VII. Development Workflow

### Adding a New Tool

1. Add the async function to the appropriate `tools/*.py` file
2. Export it from `tools/__init__.py`
3. Import it in `server.py` and register with `@mcp.tool()`
4. Add a mocked test in `tests/test_tools.py`
5. Update the tool count in `test_tool_count`
6. Run all five quality gates
7. Update CLAUDE.md tool listing

### Adding a New Tool Group

1. Create `tools/new_group.py` with async functions
2. Add imports and `__all__` entries in `tools/__init__.py`
3. Add `@mcp.tool()` wrappers in `server.py`
4. Add a `TestNewGroupTools` class in `tests/test_tools.py`
5. Run all five quality gates

---

## VIII. SELinux and Container Deployment

When running in a container with the host Podman socket mounted:
- Use `--security-opt label=type:container_runtime_t` on the container
- Mount socket with `:z` relabel flag
- The container runs as `container_runtime_t` domain, which can `connectto` the Podman socket

---

## IX. Governance

### Amendment Process

1. Create a PR with proposed changes to this constitution
2. Document rationale in PR description
3. Require maintainer approval
4. Update version number upon merge

### Ratification History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-06-14 | Initial constitution |
