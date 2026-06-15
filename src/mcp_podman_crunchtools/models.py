"""Pydantic validation models for write operations."""

from pydantic import BaseModel, ConfigDict, Field

MAX_NAME_LENGTH = 255
MAX_IMAGE_LENGTH = 500
MAX_COMMAND_LENGTH = 2000
MAX_ENV_LENGTH = 1000
MAX_SIGNAL_LENGTH = 20


class ContainerCreateInput(BaseModel):
    """Validated input for container creation."""

    model_config = ConfigDict(extra="forbid")

    image: str = Field(
        ..., min_length=1, max_length=MAX_IMAGE_LENGTH, description="Container image"
    )
    name: str | None = Field(
        default=None, max_length=MAX_NAME_LENGTH, description="Container name"
    )
    command: list[str] | None = Field(
        default=None, description="Command to run"
    )
    env: dict[str, str] | None = Field(
        default=None, description="Environment variables"
    )
    ports: dict[str, str] | None = Field(
        default=None, description="Port mappings (container_port: host_port)"
    )
    volumes: list[str] | None = Field(
        default=None, description="Volume mounts (host:container[:options])"
    )
    labels: dict[str, str] | None = Field(
        default=None, description="Container labels"
    )
    detach: bool = Field(
        default=True, description="Run in background"
    )


class PodCreateInput(BaseModel):
    """Validated input for pod creation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ..., min_length=1, max_length=MAX_NAME_LENGTH, description="Pod name"
    )
    labels: dict[str, str] | None = Field(
        default=None, description="Pod labels"
    )
    infra: bool = Field(
        default=True, description="Create an infra container"
    )
    share: list[str] | None = Field(
        default=None, description="Namespaces to share (ipc, net, uts, pid)"
    )
