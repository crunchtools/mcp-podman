"""Pydantic validation models for write operations."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_NAME_LENGTH = 255
MAX_IMAGE_LENGTH = 500
MAX_COMMAND_LENGTH = 2000
MAX_ENV_LENGTH = 1000
MAX_SIGNAL_LENGTH = 20
MAX_FILTER_VALUE_LENGTH = 255
MAX_FILTER_VALUES = 20

PruneFilterKey = Literal["until", "label", "label!", "dangling"]
PruneFilterValues = Annotated[
    list[Annotated[str, Field(min_length=1, max_length=MAX_FILTER_VALUE_LENGTH)]],
    Field(min_length=1, max_length=MAX_FILTER_VALUES),
]


class ContainerCreateInput(BaseModel):
    """Validated input for container creation."""

    model_config = ConfigDict(extra="forbid")

    image: str = Field(
        ..., min_length=1, max_length=MAX_IMAGE_LENGTH, description="Container image"
    )
    name: str | None = Field(default=None, max_length=MAX_NAME_LENGTH, description="Container name")
    command: list[str] | None = Field(default=None, description="Command to run")
    env: dict[str, str] | None = Field(default=None, description="Environment variables")
    ports: dict[str, str] | None = Field(
        default=None, description="Port mappings (container_port: host_port)"
    )
    volumes: list[str] | None = Field(
        default=None, description="Volume mounts (host:container[:options])"
    )
    labels: dict[str, str] | None = Field(default=None, description="Container labels")
    detach: bool = Field(default=True, description="Run in background")


class PodCreateInput(BaseModel):
    """Validated input for pod creation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH, description="Pod name")
    labels: dict[str, str] | None = Field(default=None, description="Pod labels")
    infra: bool = Field(default=True, description="Create an infra container")
    share: list[str] | None = Field(
        default=None, description="Namespaces to share (ipc, net, uts, pid)"
    )


class ImagePruneInput(BaseModel):
    """Validated input for image pruning."""

    model_config = ConfigDict(extra="forbid", strict=True)

    all: bool = Field(default=False, description="Remove all unused images, not just dangling")
    external: bool = Field(default=False, description="Remove images used by external containers")
    build_cache: bool = Field(default=False, description="Remove the persistent build cache")
    filters: dict[PruneFilterKey, PruneFilterValues] | None = Field(
        default=None, description="Prune filters (until, label, label!, dangling)"
    )
