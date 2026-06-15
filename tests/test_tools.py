"""Mocked API tests for all Podman tools."""

from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import _mock_config, _mock_response, _patch_client


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

        with patch(
            "mcp_podman_crunchtools.client.PodmanClient.get_text",
            return_value="line1\nline2\n",
        ):
            result = await container_logs("test")
        assert "logs" in result

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
            status_code=201, json_data={"Id": "abc123", "Warnings": []},
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


def _mock_dbus(is_podman: bool = True):
    """Create mock patches for D-Bus service tests."""
    from typing import Any
    from unittest.mock import MagicMock

    from dbus_fast import MessageType

    def _reply(body: list[Any]) -> MagicMock:
        r = MagicMock()
        r.message_type = MessageType.METHOD_RETURN
        r.body = body
        return r

    async def mock_call(
        _bus: Any, _interface: str, member: str,
        _signature: str = "", _body: Any = None, _path: str = "",
    ) -> MagicMock:
        responses = {
            "GetUnit": ["/org/freedesktop/systemd1/unit/test"],
            "RestartUnit": ["/job/123"],
            "StartUnit": ["/job/123"],
            "StopUnit": ["/job/123"],
            "ListUnits": [[
                ("test.service", "Test", "loaded", "active", "running",
                 "", "/test/path", 0, "", "/"),
                ("test2.service", "Test2", "loaded", "active", "running",
                 "", "/test/path2", 0, "", "/"),
            ]],
        }
        if member == "Get":
            return _reply(["test-value"])
        return _reply(responses.get(member, []))

    async def mock_is_podman(_bus: Any, _path: str) -> bool:
        return is_podman

    async def mock_get_prop(
        _bus: Any, _path: str, _iface: str, _prop: str,
    ) -> str:
        return "active"

    return mock_call, mock_is_podman, mock_get_prop


class TestServiceTools:
    """Tests for systemd service management tools."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        _setup_config()

    def _patches(self, is_podman: bool = True):
        """Create standard D-Bus mock patches."""
        mock_call, mock_is_podman, mock_get_prop = _mock_dbus(is_podman)
        return (
            patch("mcp_podman_crunchtools.dbus_client._get_bus",
                  return_value=AsyncMock(disconnect=lambda: None)),
            patch("mcp_podman_crunchtools.dbus_client._call", side_effect=mock_call),
            patch("mcp_podman_crunchtools.dbus_client._is_podman_unit",
                  side_effect=mock_is_podman),
            patch("mcp_podman_crunchtools.dbus_client._get_property",
                  side_effect=mock_get_prop),
        )

    async def test_service_list(self) -> None:
        from mcp_podman_crunchtools.tools.services import service_list

        p1, p2, p3, p4 = self._patches()
        with p1, p2, p3, p4:
            result = await service_list()
        assert result["count"] == 2

    async def test_service_status(self) -> None:
        from mcp_podman_crunchtools.tools.services import service_status

        p1, p2, p3, p4 = self._patches()
        with p1, p2, p3, p4:
            result = await service_status("test.service")
        assert result["unit"] == "test.service"

    async def test_service_restart(self) -> None:
        from mcp_podman_crunchtools.tools.services import service_restart

        p1, p2, p3, p4 = self._patches()
        with p1, p2, p3, p4:
            result = await service_restart("test.service")
        assert result["status"] == "restarted"

    async def test_service_start(self) -> None:
        from mcp_podman_crunchtools.tools.services import service_start

        p1, p2, p3, p4 = self._patches()
        with p1, p2, p3, p4:
            result = await service_start("test.service")
        assert result["status"] == "started"

    async def test_service_stop(self) -> None:
        from mcp_podman_crunchtools.tools.services import service_stop

        p1, p2, p3, p4 = self._patches()
        with p1, p2, p3, p4:
            result = await service_stop("test.service")
        assert result["status"] == "stopped"

    async def test_service_logs(self) -> None:
        from mcp_podman_crunchtools.tools.services import service_logs

        p1, p2, p3, p4 = self._patches()
        with p1, p2, p3, p4, patch(
            "mcp_podman_crunchtools.dbus_client.asyncio.create_subprocess_exec",
            return_value=AsyncMock(
                communicate=AsyncMock(return_value=(b"log line 1\nlog line 2\n", b"")),
                returncode=0,
            ),
        ):
            result = await service_logs("test.service")
        assert "logs" in result

    async def test_rejects_non_podman_unit(self) -> None:
        from mcp_podman_crunchtools.errors import ServiceNotPodmanError
        from mcp_podman_crunchtools.tools.services import service_restart

        p1, p2, p3, p4 = self._patches(is_podman=False)
        with p1, p2, p3, p4, pytest.raises(ServiceNotPodmanError):
            await service_restart("sshd.service")


class TestToolCount:
    """Verify tool count matches expected total."""

    async def test_tool_count(self) -> None:
        from mcp_podman_crunchtools.server import mcp as server

        tools = await server.list_tools()
        assert len(tools) == 36, f"Expected 36 tools, found {len(tools)}"
