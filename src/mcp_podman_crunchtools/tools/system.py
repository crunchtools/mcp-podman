"""System information tools."""

from typing import Any

from ..client import get_client


async def system_info() -> dict[str, Any]:
    """Get Podman system information."""
    client = get_client()
    return await client.get("/info")


async def system_df() -> dict[str, Any]:
    """Get Podman disk usage."""
    client = get_client()
    return await client.get("/system/df")
