"""MCP Podman CrunchTools - MCP server for Podman container management.

Manages containers, images, pods, networks, volumes, and system info
via the Podman REST API over Unix sockets. Supports both rootful and
rootless Podman.

Usage:
    mcp-podman-crunchtools
    python -m mcp_podman_crunchtools
    uvx mcp-podman-crunchtools

Environment Variables:
    PODMAN_SOCKET: Optional. Path to Podman Unix socket (auto-detected).
    PODMAN_TIMEOUT: Optional. Request timeout in seconds (default: 30).

Example with Claude Code:
    claude mcp add mcp-podman-crunchtools \\
        --env PODMAN_SOCKET=/run/podman/podman.sock \\
        -- uvx mcp-podman-crunchtools
"""

import argparse

from .server import mcp

__version__ = "0.1.1"
__all__ = ["main", "mcp"]


def main() -> None:
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="MCP server for Podman")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to for HTTP transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8023,
        help="Port to bind to for HTTP transports (default: 8023)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)
