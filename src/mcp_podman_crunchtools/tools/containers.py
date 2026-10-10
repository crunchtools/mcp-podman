"""Container management tools."""

import json
from typing import Any

from pydantic import ValidationError

from ..client import get_client, path_segment
from ..errors import InvalidInputError
from ..models import ContainerCreateInput

# "host:container[:options]" — a mount spec with an options segment has 3 parts.
VOLUME_SPEC_WITH_OPTIONS_PARTS = 2

REDACTED = "<redacted>"
ENV_FLAGS = ("-e", "--env")
ENV_FLAG_PREFIXES = ("--env=", "-e")


def _redact_assignment(assignment: str) -> str:
    """Turn ``NAME=value`` into ``NAME=<redacted>``; a bare ``NAME`` has no value to hide."""
    name, separator, _ = assignment.partition("=")
    return f"{name}={REDACTED}" if separator else assignment


def _redact_create_command(command: list[Any]) -> list[str]:
    """Redact the values ``podman run`` was given with ``-e`` / ``--env``."""
    redacted: list[str] = []
    value_follows = False
    for raw in command:
        arg = str(raw)
        if value_follows:
            redacted.append(_redact_assignment(arg))
            value_follows = False
            continue
        if arg in ENV_FLAGS:
            value_follows = True
        elif not arg.startswith("--env-"):
            for prefix in ENV_FLAG_PREFIXES:
                if arg.startswith(prefix) and "=" in arg[len(prefix) :]:
                    arg = prefix + _redact_assignment(arg[len(prefix) :])
                    break
        redacted.append(arg)
    return redacted


def _redact_environment(detail: dict[str, Any]) -> dict[str, Any]:
    """Remove environment values from an inspect document, keeping the names.

    libpod returns every variable with its value in ``Config.Env``, and the
    full ``podman run`` command, inline ``-e NAME=value`` included, in
    ``Config.CreateCommand``. A container's environment is where its
    credentials live, and the caller of this tool is a model. Every value is
    redacted rather than the secret-looking ones: ``DATABASE_URL`` does not
    look like a secret by name.
    """
    config = detail.get("Config")
    if not isinstance(config, dict):
        return detail
    env = config.get("Env")
    if isinstance(env, list):
        config["Env"] = [_redact_assignment(str(entry)) for entry in env]
    command = config.get("CreateCommand")
    if isinstance(command, list):
        config["CreateCommand"] = _redact_create_command(command)
    return detail


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
        params["filters"] = json.dumps(filters)
    if limit is not None:
        params["limit"] = limit
    return await client.get("/containers/json", params=params)


async def container_inspect(name: str) -> dict[str, Any]:
    """Get detailed information about a container, with environment values redacted."""
    client = get_client()
    return _redact_environment(await client.get(f"/containers/{path_segment(name)}/json"))


async def container_start(name: str) -> dict[str, Any]:
    """Start a stopped container."""
    client = get_client()
    return await client.post(f"/containers/{path_segment(name)}/start")


async def container_stop(name: str, timeout: int = 10) -> dict[str, Any]:
    """Stop a running container."""
    client = get_client()
    return await client.post(f"/containers/{path_segment(name)}/stop", params={"t": timeout})


async def container_restart(name: str, timeout: int = 10) -> dict[str, Any]:
    """Restart a container."""
    client = get_client()
    return await client.post(f"/containers/{path_segment(name)}/restart", params={"t": timeout})


async def container_kill(name: str, signal: str = "SIGTERM") -> dict[str, Any]:
    """Send a signal to a container."""
    client = get_client()
    return await client.post(f"/containers/{path_segment(name)}/kill", params={"signal": signal})


async def container_rm(name: str, force: bool = False, volumes: bool = False) -> dict[str, Any]:
    """Remove a container."""
    client = get_client()
    params: dict[str, Any] = {}
    if force:
        params["force"] = "true"
    if volumes:
        params["v"] = "true"
    return await client.delete(f"/containers/{path_segment(name)}", params=params)


async def container_logs(
    name: str,
    tail: int | None = None,
    since: str | None = None,
    timestamps: bool = False,
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
    text = await client.get_text(f"/containers/{path_segment(name)}/logs", params=params)
    return {"logs": text}


async def container_top(name: str, ps_args: str | None = None) -> dict[str, Any]:
    """List processes running inside a container."""
    client = get_client()
    params: dict[str, Any] = {}
    if ps_args:
        params["ps_args"] = ps_args
    return await client.get(f"/containers/{path_segment(name)}/top", params=params)


async def container_stats(name: str, stream: bool = False) -> dict[str, Any]:
    """Get container resource usage statistics."""
    client = get_client()
    return await client.get(
        f"/containers/{path_segment(name)}/stats", params={"stream": str(stream).lower()}
    )


async def container_create(
    image: str,
    name: str | None = None,
    command: list[str] | None = None,
    env: dict[str, str] | None = None,
    labels: dict[str, str] | None = None,
    volumes: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new container."""
    try:
        validated = ContainerCreateInput(
            image=image,
            name=name,
            command=command,
            env=env,
            labels=labels,
            volumes=volumes,
        )
    except ValidationError as e:
        raise InvalidInputError(str(e)) from e

    client = get_client()
    spec: dict[str, Any] = {"image": validated.image}
    if validated.name:
        spec["name"] = validated.name
    if validated.command:
        spec["command"] = validated.command
    if validated.env:
        spec["env"] = validated.env
    if validated.labels:
        spec["labels"] = validated.labels
    if validated.volumes:
        mounts = []
        for vol in validated.volumes:
            parts = vol.split(":")
            mount: dict[str, Any] = {"Type": "bind", "Source": parts[0], "Destination": parts[1]}
            if len(parts) > VOLUME_SPEC_WITH_OPTIONS_PARTS:
                mount["Options"] = parts[2].split(",")
            mounts.append(mount)
        spec["mounts"] = mounts
    return await client.post("/containers/create", json_data=spec)


async def container_prune() -> dict[str, Any]:
    """Remove all stopped containers."""
    client = get_client()
    return await client.post("/containers/prune")
