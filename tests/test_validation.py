"""Pydantic model validation tests."""

import pytest
from pydantic import ValidationError

from mcp_podman_crunchtools.models import (
    MAX_FILTER_VALUE_LENGTH,
    MAX_FILTER_VALUES,
    ContainerCreateInput,
    ImagePruneInput,
    PodCreateInput,
)


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


class TestImagePruneInput:
    """Tests for ImagePruneInput validation."""

    def test_valid_minimal(self) -> None:
        model = ImagePruneInput()
        assert model.all is False
        assert model.external is False
        assert model.build_cache is False
        assert model.filters is None

    def test_valid_full(self) -> None:
        model = ImagePruneInput(
            all=True,
            external=True,
            build_cache=True,
            filters={
                "until": ["168h"],
                "label": ["stage=ci"],
                "label!": ["keep"],
                "dangling": ["false"],
            },
        )
        assert model.all is True
        assert model.filters is not None
        assert model.filters["until"] == ["168h"]

    def test_filter_limits_are_inclusive(self) -> None:
        values = ["a" * MAX_FILTER_VALUE_LENGTH] * MAX_FILTER_VALUES
        model = ImagePruneInput(filters={"label": values})
        assert model.filters == {"label": values}

    def test_unknown_filter_key_rejected(self) -> None:
        with pytest.raises(ValidationError, match="filters"):
            ImagePruneInput(filters={"reference": ["ubi9"]})  # type: ignore[dict-item]

    def test_filter_value_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError, match="String should have at most 255 characters"):
            ImagePruneInput(filters={"label": ["a" * (MAX_FILTER_VALUE_LENGTH + 1)]})

    def test_empty_filter_value_rejected(self) -> None:
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            ImagePruneInput(filters={"until": [""]})

    def test_empty_filter_list_rejected(self) -> None:
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            ImagePruneInput(filters={"until": []})

    def test_too_many_filter_values_rejected(self) -> None:
        with pytest.raises(ValidationError, match="List should have at most 20 items"):
            ImagePruneInput(filters={"label": ["a"] * (MAX_FILTER_VALUES + 1)})

    def test_coerced_bool_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Input should be a valid boolean"):
            ImagePruneInput(all="true")  # type: ignore[arg-type]

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            ImagePruneInput(force=True)  # type: ignore[call-arg]
