"""Network management tools."""

from typing import Any

from ..client import get_client


async def network_list(
    filters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """List networks."""
    client = get_client()
    params: dict[str, Any] = {}
    if filters:
        import json
        params["filters"] = json.dumps(filters)
    return await client.get("/networks/json", params=params)


async def network_inspect(name: str) -> dict[str, Any]:
    """Get detailed information about a network."""
    client = get_client()
    return await client.get(f"/networks/{name}/json")
