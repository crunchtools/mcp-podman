# Security Design Document

This document describes the security architecture of mcp-podman-crunchtools.

## 1. Threat Model

### 1.1 Assets to Protect

| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| Podman Socket Access | Critical | Full container/host control |
| Container Data | High | Data exfiltration, manipulation |
| Host Filesystem (via mounts) | High | Arbitrary file access |

### 1.2 Attack Vectors

| Vector | Description | Mitigation |
|--------|-------------|------------|
| **Socket Hijacking** | Unauthorized socket access | Unix file permissions |
| **Container Escape** | Break out of container | Rootless Podman, SELinux |
| **Input Injection** | Malicious container names | Pydantic validation |
| **Resource Exhaustion** | Create unlimited containers | Rate awareness |
| **Supply Chain** | Compromised dependencies | Automated CVE scanning |

## 2. Security Architecture

### 2.1 Defense in Depth

- **Layer 1 — Input Validation:** Pydantic models with `extra="forbid"` and field limits
- **Layer 2 — Socket Security:** Unix permissions (no network exposure)
- **Layer 3 — API Client:** Request timeouts, response size limits
- **Layer 4 — No Shell Execution:** Pure HTTP API calls, no subprocess/eval/exec
- **Layer 5 — Supply Chain:** Weekly CVE scanning, Hummingbird base images

### 2.2 Authentication

Unlike HTTP API servers, this server uses **Unix socket file permissions** for authentication. Access to the Podman socket grants full Podman API access. The server does not add any additional authentication layer.

### 2.3 SELinux

When running in a container with the host Podman socket mounted:
- Use `--security-opt label=type:container_runtime_t`
- Mount socket with `:z` relabel flag

## 3. Reporting Security Issues

Report vulnerabilities using [GitHub's private security advisory](https://github.com/crunchtools/mcp-podman/security/advisories/new).

Do NOT open public issues for security vulnerabilities.
