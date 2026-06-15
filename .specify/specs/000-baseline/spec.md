# Specification: Baseline Tool Inventory

> **Spec ID:** 000-baseline
> **Status:** Implemented
> **Version:** 0.1.0
> **Author:** Scott McCarty
> **Date:** 2026-06-14

## Overview

Initial tool inventory for the Podman MCP server. Covers container lifecycle, image management, pod operations, network and volume inspection, and system info. 30 tools across 6 categories.

## Tool Inventory

### Containers (12)
container_list, container_inspect, container_start, container_stop, container_restart, container_kill, container_rm, container_logs, container_top, container_stats, container_create, container_prune

### Images (5)
image_list, image_inspect, image_pull, image_rm, image_prune

### Pods (7)
pod_list, pod_inspect, pod_start, pod_stop, pod_restart, pod_rm, pod_create

### Networks (2)
network_list, network_inspect

### Volumes (2)
volume_list, volume_inspect

### System (2)
system_info, system_df

## Architecture

- **Client:** httpx AsyncHTTPTransport over Unix domain socket
- **Config:** Socket path auto-detection (rootless → rootful)
- **Auth:** Unix socket file permissions (no API tokens)
- **API version:** Podman Libpod v5.0.0
