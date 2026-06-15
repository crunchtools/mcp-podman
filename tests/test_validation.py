"""Pydantic model validation tests."""

import pytest
from pydantic import ValidationError

from mcp_podman_crunchtools.models import ContainerCreateInput, PodCreateInput


class TestContainerCreateInput:
    """Tests for ContainerCreateInput validation."""

    def test_valid_minimal(self) -> None:
        model = ContainerCreateInput(image="ubi9:latest")
        assert model.image == "ubi9:latest"
        assert model.name is None

    def test_valid_full(self) -> None:
        model = ContainerCreateInput(
            image="quay.io/crunchtools/rotv:latest",
            name="mycontainer",
            command=["/bin/sh", "-c", "echo hello"],
            env={"FOO": "bar"},
            labels={"app": "test"},
            volumes=["/data:/data:Z"],
        )
        assert model.name == "mycontainer"
        assert model.env == {"FOO": "bar"}

    def test_empty_image_rejected(self) -> None:
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            ContainerCreateInput(image="")

    def test_image_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError, match="String should have at most 500 characters"):
            ContainerCreateInput(image="a" * 501)

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            ContainerCreateInput(image="ubi9:latest", bogus="nope")  # type: ignore[call-arg]


class TestPodCreateInput:
    """Tests for PodCreateInput validation."""

    def test_valid_minimal(self) -> None:
        model = PodCreateInput(name="mypod")
        assert model.name == "mypod"
        assert model.infra is True

    def test_valid_full(self) -> None:
        model = PodCreateInput(
            name="mypod",
            labels={"app": "test"},
            infra=False,
            share=["ipc", "net"],
        )
        assert model.infra is False
        assert model.share == ["ipc", "net"]

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            PodCreateInput(name="")

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            PodCreateInput(name="mypod", bogus="nope")  # type: ignore[call-arg]
