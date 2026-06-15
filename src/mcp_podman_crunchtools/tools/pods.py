"""Pod management tools."""

from typing import Any

from ..client import get_client


async def pod_list(
    filters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """List pods."""
    client = get_client()
    params: dict[str, Any] = {}
    if filters:
        import json
        params["filters"] = json.dumps(filters)
    return await client.get("/pods/json", params=params)


async def pod_inspect(name: str) -> dict[str, Any]:
    """Get detailed information about a pod."""
    client = get_client()
    return await client.get(f"/pods/{name}/json")


async def pod_start(name: str) -> dict[str, Any]:
    """Start a pod."""
    client = get_client()
    return await client.post(f"/pods/{name}/start")


async def pod_stop(name: str, timeout: int = 10) -> dict[str, Any]:
    """Stop a pod."""
    client = get_client()
    return await client.post(f"/pods/{name}/stop", params={"t": timeout})


async def pod_restart(name: str) -> dict[str, Any]:
    """Restart a pod."""
    client = get_client()
    return await client.post(f"/pods/{name}/restart")


async def pod_rm(name: str, force: bool = False) -> dict[str, Any]:
    """Remove a pod."""
    client = get_client()
    params: dict[str, Any] = {}
    if force:
        params["force"] = "true"
    return await client.delete(f"/pods/{name}", params=params)


async def pod_create(
    name: str,
    labels: dict[str, str] | None = None,
    infra: bool = True,
    share: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new pod."""
    client = get_client()
    spec: dict[str, Any] = {"name": name, "infra": infra}
    if labels:
        spec["labels"] = labels
    if share:
        spec["share"] = share
    return await client.post("/pods/create", json_data=spec)
