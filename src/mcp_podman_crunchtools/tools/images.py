"""Image management tools."""

import json
from typing import Any

from pydantic import ValidationError

from ..client import get_client, path_segment
from ..errors import InvalidInputError
from ..models import ImagePruneInput

# Removing many gigabytes of layers outlasts the default request timeout.
PRUNE_TIMEOUT_SECONDS = 600.0


async def image_list(
    filters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """List images."""
    client = get_client()
    params: dict[str, Any] = {}
    if filters:
        params["filters"] = json.dumps(filters)
    return await client.get("/images/json", params=params)


async def image_inspect(name: str) -> dict[str, Any]:
    """Get detailed information about an image."""
    client = get_client()
    return await client.get(f"/images/{path_segment(name)}/json")


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
    return await client.delete(f"/images/{path_segment(name)}", params=params)


async def image_prune(
    all: bool = False,
    external: bool = False,
    build_cache: bool = False,
    filters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Remove unused images, with the options of `podman image prune`."""
    try:
        validated = ImagePruneInput.model_validate(
            {"all": all, "external": external, "build_cache": build_cache, "filters": filters}
        )
    except ValidationError as e:
        raise InvalidInputError(str(e)) from e

    client = get_client()
    params: dict[str, Any] = {}
    if validated.all:
        params["all"] = "true"
    if validated.external:
        params["external"] = "true"
    if validated.build_cache:
        params["buildcache"] = "true"
    if validated.filters:
        params["filters"] = json.dumps(validated.filters)
    return await client.post("/images/prune", params=params, timeout=PRUNE_TIMEOUT_SECONDS)
