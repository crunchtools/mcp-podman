"""Image management tools."""

from typing import Any

from ..client import get_client


async def image_list(
    filters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """List images."""
    client = get_client()
    params: dict[str, Any] = {}
    if filters:
        import json
        params["filters"] = json.dumps(filters)
    return await client.get("/images/json", params=params)


async def image_inspect(name: str) -> dict[str, Any]:
    """Get detailed information about an image."""
    client = get_client()
    return await client.get(f"/images/{name}/json")


async def image_pull(reference: str) -> dict[str, Any]:
    """Pull an image from a registry."""
    client = get_client()
    return await client.post("/images/pull", params={"reference": reference})


async def image_rm(name: str, force: bool = False) -> dict[str, Any]:
    """Remove an image."""
    client = get_client()
    params: dict[str, Any] = {}
    if force:
        params["force"] = "true"
    return await client.delete(f"/images/{name}", params=params)


async def image_prune() -> dict[str, Any]:
    """Remove unused images."""
    client = get_client()
    return await client.post("/images/prune")
