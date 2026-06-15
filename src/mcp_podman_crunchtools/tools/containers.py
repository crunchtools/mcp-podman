"""Container management tools."""

from typing import Any

from ..client import get_client


async def container_list(
    all_containers: bool = False,
    filters: dict[str, list[str]] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """List containers."""
    client = get_client()
    params: dict[str, Any] = {}
    if all_containers:
        params["all"] = "true"
    if filters:
        import json
        params["filters"] = json.dumps(filters)
    if limit is not None:
        params["limit"] = limit
    return await client.get("/containers/json", params=params)


async def container_inspect(name: str) -> dict[str, Any]:
    """Get detailed information about a container."""
    client = get_client()
    return await client.get(f"/containers/{name}/json")


async def container_start(name: str) -> dict[str, Any]:
    """Start a stopped container."""
    client = get_client()
    return await client.post(f"/containers/{name}/start")


async def container_stop(name: str, timeout: int = 10) -> dict[str, Any]:
    """Stop a running container."""
    client = get_client()
    return await client.post(f"/containers/{name}/stop", params={"t": timeout})


async def container_restart(name: str, timeout: int = 10) -> dict[str, Any]:
    """Restart a container."""
    client = get_client()
    return await client.post(f"/containers/{name}/restart", params={"t": timeout})


async def container_kill(name: str, signal: str = "SIGTERM") -> dict[str, Any]:
    """Send a signal to a container."""
    client = get_client()
    return await client.post(f"/containers/{name}/kill", params={"signal": signal})


async def container_rm(name: str, force: bool = False, volumes: bool = False) -> dict[str, Any]:
    """Remove a container."""
    client = get_client()
    params: dict[str, Any] = {}
    if force:
        params["force"] = "true"
    if volumes:
        params["v"] = "true"
    return await client.delete(f"/containers/{name}", params=params)


async def container_logs(
    name: str, tail: int | None = None, since: str | None = None, timestamps: bool = False,
) -> dict[str, Any]:
    """Get container logs."""
    client = get_client()
    params: dict[str, Any] = {"stdout": "true", "stderr": "true"}
    if tail is not None:
        params["tail"] = str(tail)
    if since:
        params["since"] = since
    if timestamps:
        params["timestamps"] = "true"
    text = await client.get_text(f"/containers/{name}/logs", params=params)
    return {"logs": text}


async def container_top(name: str, ps_args: str | None = None) -> dict[str, Any]:
    """List processes running inside a container."""
    client = get_client()
    params: dict[str, Any] = {}
    if ps_args:
        params["ps_args"] = ps_args
    return await client.get(f"/containers/{name}/top", params=params)


async def container_stats(name: str, stream: bool = False) -> dict[str, Any]:
    """Get container resource usage statistics."""
    client = get_client()
    return await client.get(f"/containers/{name}/stats", params={"stream": str(stream).lower()})


async def container_create(
    image: str,
    name: str | None = None,
    command: list[str] | None = None,
    env: dict[str, str] | None = None,
    labels: dict[str, str] | None = None,
    volumes: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new container."""
    client = get_client()
    spec: dict[str, Any] = {"image": image}
    if name:
        spec["name"] = name
    if command:
        spec["command"] = command
    if env:
        spec["env"] = env
    if labels:
        spec["labels"] = labels
    if volumes:
        mounts = []
        for vol in volumes:
            parts = vol.split(":")
            mount: dict[str, Any] = {"Type": "bind", "Source": parts[0], "Destination": parts[1]}
            if len(parts) > 2:
                mount["Options"] = parts[2].split(",")
            mounts.append(mount)
        spec["mounts"] = mounts
    return await client.post("/containers/create", json_data=spec)


async def container_prune() -> dict[str, Any]:
    """Remove all stopped containers."""
    client = get_client()
    return await client.post("/containers/prune")
