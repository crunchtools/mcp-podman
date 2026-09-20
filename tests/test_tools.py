"""Mocked API tests for all Podman tools."""

import httpx
import pytest

from tests.conftest import (
    _mock_config,
    _mock_response,
    _patch_client,
    _patch_client_raising,
)


def _setup_config() -> None:
    """Patch config to avoid needing a real socket."""
    import mcp_podman_crunchtools.config as config_mod

    config_mod._config = _mock_config()


class TestContainerTools:
    """Tests for container management tools."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        _setup_config()

    async def test_container_list(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_list

        response = _mock_response(json_data=[{"Id": "abc123", "Names": ["test"]}])
        with _patch_client(response):
            result = await container_list()
        assert "items" in result
        assert result["count"] == 1

    async def test_container_inspect(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_inspect

        response = _mock_response(json_data={"Id": "abc123", "Name": "test"})
        with _patch_client(response):
            result = await container_inspect("test")
        assert result["Id"] == "abc123"

    async def test_container_start(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_start

        response = _mock_response(status_code=204)
        with _patch_client(response):
            result = await container_start("test")
        assert result["status"] == "success"

    async def test_container_stop(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_stop

        response = _mock_response(status_code=204)
        with _patch_client(response):
            result = await container_stop("test")
        assert result["status"] == "success"

    async def test_container_restart(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_restart

        response = _mock_response(status_code=204)
        with _patch_client(response):
            result = await container_restart("test")
        assert result["status"] == "success"

    async def test_container_kill(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_kill

        response = _mock_response(status_code=204)
        with _patch_client(response):
            result = await container_kill("test")
        assert result["status"] == "success"

    async def test_container_rm(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_rm

        response = _mock_response(json_data=[{"Id": "abc123"}])
        with _patch_client(response):
            result = await container_rm("test")
        assert "items" in result

    async def test_container_logs(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_logs

        response = _mock_response(text="line1\nline2\n")
        with _patch_client(response):
            result = await container_logs("test")
        assert result["logs"] == "line1\nline2\n"

    async def test_container_top(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_top

        response = _mock_response(
            json_data={"Titles": ["PID", "CMD"], "Processes": [["1", "/bin/sh"]]},
        )
        with _patch_client(response):
            result = await container_top("test")
        assert "Titles" in result

    async def test_container_stats(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_stats

        response = _mock_response(
            json_data={"CPU": 1.5, "MemUsage": 1024000},
        )
        with _patch_client(response):
            result = await container_stats("test")
        assert "CPU" in result

    async def test_container_create(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_create

        response = _mock_response(
            status_code=201,
            json_data={"Id": "abc123", "Warnings": []},
        )
        with _patch_client(response):
            result = await container_create(image="ubi9:latest", name="newcontainer")
        assert result["Id"] == "abc123"

    async def test_container_prune(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_prune

        response = _mock_response(json_data=[{"Id": "old123", "Size": 1024}])
        with _patch_client(response):
            result = await container_prune()
        assert "items" in result


class TestImageTools:
    """Tests for image management tools."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        _setup_config()

    async def test_image_list(self) -> None:
        from mcp_podman_crunchtools.tools.images import image_list

        response = _mock_response(json_data=[{"Id": "img123", "RepoTags": ["ubi9:latest"]}])
        with _patch_client(response):
            result = await image_list()
        assert result["count"] == 1

    async def test_image_inspect(self) -> None:
        from mcp_podman_crunchtools.tools.images import image_inspect

        response = _mock_response(json_data={"Id": "img123", "Size": 100000})
        with _patch_client(response):
            result = await image_inspect("ubi9:latest")
        assert result["Id"] == "img123"

    async def test_image_pull(self) -> None:
        from mcp_podman_crunchtools.tools.images import image_pull

        response = _mock_response(json_data={"id": "img123", "images": ["ubi9:latest"]})
        with _patch_client(response):
            result = await image_pull("ubi9:latest")
        assert "id" in result

    async def test_image_rm(self) -> None:
        from mcp_podman_crunchtools.tools.images import image_rm

        response = _mock_response(json_data=[{"Untagged": ["ubi9:latest"], "Deleted": "img123"}])
        with _patch_client(response):
            result = await image_rm("ubi9:latest")
        assert "items" in result

    async def test_image_prune(self) -> None:
        from mcp_podman_crunchtools.tools.images import image_prune

        response = _mock_response(json_data=[{"Id": "old123", "Size": 2048}])
        with _patch_client(response):
            result = await image_prune()
        assert "items" in result


class TestPodTools:
    """Tests for pod management tools."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        _setup_config()

    async def test_pod_list(self) -> None:
        from mcp_podman_crunchtools.tools.pods import pod_list

        response = _mock_response(json_data=[{"Id": "pod123", "Name": "mypod"}])
        with _patch_client(response):
            result = await pod_list()
        assert result["count"] == 1

    async def test_pod_inspect(self) -> None:
        from mcp_podman_crunchtools.tools.pods import pod_inspect

        response = _mock_response(json_data={"Id": "pod123", "Name": "mypod"})
        with _patch_client(response):
            result = await pod_inspect("mypod")
        assert result["Name"] == "mypod"

    async def test_pod_start(self) -> None:
        from mcp_podman_crunchtools.tools.pods import pod_start

        response = _mock_response(status_code=204)
        with _patch_client(response):
            result = await pod_start("mypod")
        assert result["status"] == "success"

    async def test_pod_stop(self) -> None:
        from mcp_podman_crunchtools.tools.pods import pod_stop

        response = _mock_response(status_code=204)
        with _patch_client(response):
            result = await pod_stop("mypod")
        assert result["status"] == "success"

    async def test_pod_restart(self) -> None:
        from mcp_podman_crunchtools.tools.pods import pod_restart

        response = _mock_response(status_code=204)
        with _patch_client(response):
            result = await pod_restart("mypod")
        assert result["status"] == "success"

    async def test_pod_rm(self) -> None:
        from mcp_podman_crunchtools.tools.pods import pod_rm

        response = _mock_response(json_data={"Id": "pod123"})
        with _patch_client(response):
            result = await pod_rm("mypod")
        assert result["Id"] == "pod123"

    async def test_pod_create(self) -> None:
        from mcp_podman_crunchtools.tools.pods import pod_create

        response = _mock_response(status_code=201, json_data={"Id": "pod123"})
        with _patch_client(response):
            result = await pod_create(name="mypod")
        assert result["Id"] == "pod123"


class TestNetworkTools:
    """Tests for network management tools."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        _setup_config()

    async def test_network_list(self) -> None:
        from mcp_podman_crunchtools.tools.networks import network_list

        response = _mock_response(json_data=[{"Name": "podman", "Driver": "bridge"}])
        with _patch_client(response):
            result = await network_list()
        assert result["count"] == 1

    async def test_network_inspect(self) -> None:
        from mcp_podman_crunchtools.tools.networks import network_inspect

        response = _mock_response(json_data={"Name": "podman", "Driver": "bridge"})
        with _patch_client(response):
            result = await network_inspect("podman")
        assert result["Name"] == "podman"


class TestVolumeTools:
    """Tests for volume management tools."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        _setup_config()

    async def test_volume_list(self) -> None:
        from mcp_podman_crunchtools.tools.volumes import volume_list

        response = _mock_response(json_data=[{"Name": "data", "Driver": "local"}])
        with _patch_client(response):
            result = await volume_list()
        assert result["count"] == 1

    async def test_volume_inspect(self) -> None:
        from mcp_podman_crunchtools.tools.volumes import volume_inspect

        response = _mock_response(json_data={"Name": "data", "Mountpoint": "/var/lib/volumes/data"})
        with _patch_client(response):
            result = await volume_inspect("data")
        assert result["Name"] == "data"


class TestSystemTools:
    """Tests for system tools."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        _setup_config()

    async def test_system_info(self) -> None:
        from mcp_podman_crunchtools.tools.system import system_info

        info = {"host": {"os": "linux"}, "version": {"Version": "5.0"}}
        response = _mock_response(json_data=info)
        with _patch_client(response):
            result = await system_info()
        assert "host" in result

    async def test_system_df(self) -> None:
        from mcp_podman_crunchtools.tools.system import system_df

        response = _mock_response(json_data={"Images": [], "Containers": [], "Volumes": []})
        with _patch_client(response):
            result = await system_df()
        assert "Images" in result


class TestClientErrorHandling:
    """Transport and HTTP failures must surface as clean ToolError subclasses."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        _setup_config()

    async def test_connect_error_gives_socket_remediation(self) -> None:
        from mcp_podman_crunchtools.errors import SocketConnectionError
        from mcp_podman_crunchtools.tools.containers import container_list

        with (
            _patch_client_raising(httpx.ConnectError("no such file")),
            pytest.raises(SocketConnectionError, match="Cannot connect to Podman socket"),
        ):
            await container_list()

    async def test_connect_timeout_gives_socket_remediation(self) -> None:
        """ConnectTimeout subclasses TimeoutException, so it needs its own handling."""
        from mcp_podman_crunchtools.errors import SocketConnectionError
        from mcp_podman_crunchtools.tools.containers import container_list

        with (
            _patch_client_raising(httpx.ConnectTimeout("handshake timed out")),
            pytest.raises(SocketConnectionError, match="systemctl"),
        ):
            await container_list()

    async def test_read_timeout_is_a_timeout_not_a_socket_error(self) -> None:
        from mcp_podman_crunchtools.errors import PodmanApiError
        from mcp_podman_crunchtools.tools.containers import container_list

        with (
            _patch_client_raising(httpx.ReadTimeout("read timed out")),
            pytest.raises(PodmanApiError, match="Request timeout"),
        ):
            await container_list()

    async def test_logs_mid_stream_error_is_clean(self) -> None:
        """Regression: get_text lacked the RequestError clause that _send has."""
        from mcp_podman_crunchtools.errors import PodmanApiError
        from mcp_podman_crunchtools.tools.containers import container_logs

        with (
            _patch_client_raising(httpx.RemoteProtocolError("server disconnected")),
            pytest.raises(PodmanApiError, match="Request failed"),
        ):
            await container_logs("test")

    async def test_logs_connect_error_gives_socket_remediation(self) -> None:
        from mcp_podman_crunchtools.errors import SocketConnectionError
        from mcp_podman_crunchtools.tools.containers import container_logs

        with (
            _patch_client_raising(httpx.ConnectError("no such file")),
            pytest.raises(SocketConnectionError, match="Cannot connect to Podman socket"),
        ):
            await container_logs("test")

    async def test_logs_respects_response_size_limit(self) -> None:
        """Regression: get_text bypassed _check_response, so logs had no size cap."""
        from mcp_podman_crunchtools.errors import PodmanApiError
        from mcp_podman_crunchtools.tools.containers import container_logs

        response = _mock_response(text="x")
        response.headers["content-length"] = str(11 * 1024 * 1024)
        with (
            _patch_client(response),
            pytest.raises(PodmanApiError, match="Response too large"),
        ):
            await container_logs("test")

    async def test_404_on_container_path(self) -> None:
        from mcp_podman_crunchtools.errors import ContainerNotFoundError
        from mcp_podman_crunchtools.tools.containers import container_inspect

        response = _mock_response(status_code=404, json_data={"cause": "no such container"})
        with (
            _patch_client(response),
            pytest.raises(ContainerNotFoundError, match="no such container"),
        ):
            await container_inspect("missing")

    async def test_404_on_image_path(self) -> None:
        from mcp_podman_crunchtools.errors import ImageNotFoundError
        from mcp_podman_crunchtools.tools.images import image_inspect

        response = _mock_response(status_code=404, json_data={"cause": "no such image"})
        with (
            _patch_client(response),
            pytest.raises(ImageNotFoundError, match="no such image"),
        ):
            await image_inspect("missing")

    async def test_409_is_reported_as_a_conflict(self) -> None:
        from mcp_podman_crunchtools.errors import PodmanApiError
        from mcp_podman_crunchtools.tools.containers import container_rm

        response = _mock_response(status_code=409, json_data={"cause": "container is running"})
        with (
            _patch_client(response),
            pytest.raises(PodmanApiError, match="Conflict: container is running"),
        ):
            await container_rm("busy")

    async def test_500_falls_through_to_a_generic_api_error(self) -> None:
        from mcp_podman_crunchtools.errors import PodmanApiError
        from mcp_podman_crunchtools.tools.containers import container_list

        response = _mock_response(status_code=500, json_data={"message": "boom"})
        with (
            _patch_client(response),
            pytest.raises(PodmanApiError, match="500"),
        ):
            await container_list()

    async def test_non_json_error_body_is_truncated(self) -> None:
        from mcp_podman_crunchtools.errors import PodmanApiError
        from mcp_podman_crunchtools.tools.containers import container_list

        response = _mock_response(status_code=502, text="<html>bad gateway</html>")
        with (
            _patch_client(response),
            pytest.raises(PodmanApiError, match="bad gateway"),
        ):
            await container_list()


class TestToolCount:
    """Verify tool count matches expected total."""

    async def test_tool_count(self) -> None:
        from mcp_podman_crunchtools.server import mcp as server

        tools = await server.list_tools()
        assert len(tools) == 30, f"Expected 30 tools, found {len(tools)}"
