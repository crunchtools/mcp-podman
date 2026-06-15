"""Volume management tools."""

from typing import Any

from ..client import get_client


async def volume_list(
    filters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """List volumes."""
    client = get_client()
    params: dict[str, Any] = {}
    if filters:
        import json
        params["filters"] = json.dumps(filters)
    return await client.get("/volumes/json", params=params)


async def volume_inspect(name: str) -> dict[str, Any]:
    """Get detailed information about a volume."""
    client = get_client()
    return await client.get(f"/volumes/{name}/json")
