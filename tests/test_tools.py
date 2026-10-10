"""Mocked API tests for all Podman tools."""

from unittest.mock import AsyncMock, patch

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

    async def test_container_inspect_redacts_environment_values(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_inspect

        response = _mock_response(
            json_data={
                "Id": "abc123",
                "State": {"OOMKilled": False},
                "Config": {
                    "Env": ["API_KEY=sk-live-1", "DATABASE_URL=postgres://u:pw@db/app", "TERM"],
                    "CreateCommand": [
                        "podman",
                        "run",
                        "-e",
                        "API_KEY=sk-live-1",
                        "--env=TOKEN=tok-2",
                        "-ePASS=pw-3",
                        "--env",
                        "HOME",
                        "--env-file",
                        "/srv/app/app.env",
                        "--entrypoint=/bin/app",
                        "-v",
                        "/srv/app:/data:Z",
                        "quay.io/example/app",
                    ],
                },
            }
        )
        with _patch_client(response):
            result = await container_inspect("test")
        assert result["Config"]["Env"] == [
            "API_KEY=<redacted>",
            "DATABASE_URL=<redacted>",
            "TERM",
        ]
        assert result["Config"]["CreateCommand"] == [
            "podman",
            "run",
            "-e",
            "API_KEY=<redacted>",
            "--env=TOKEN=<redacted>",
            "-ePASS=<redacted>",
            "--env",
            "HOME",
            "--env-file",
            "/srv/app/app.env",
            "--entrypoint=/bin/app",
            "-v",
            "/srv/app:/data:Z",
            "quay.io/example/app",
        ]
        assert result["State"] == {"OOMKilled": False}
        for value in ("sk-live-1", "pw@db", "tok-2", "pw-3"):
            assert value not in str(result)

    async def test_container_name_is_encoded_as_one_path_segment(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_inspect

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=_mock_response(json_data={"Id": "abc123"}))

        async def mock_get_client(_self: object) -> AsyncMock:
            return mock_client

        with patch("mcp_podman_crunchtools.client.PodmanClient._get_client", mock_get_client):
            await container_inspect("../images/x")
        assert mock_client.request.call_args.kwargs["url"] == "/containers/..%2Fimages%2Fx/json"

    async def test_container_inspect_without_config_is_unchanged(self) -> None:
        from mcp_podman_crunchtools.tools.containers import container_inspect

        response = _mock_response(json_data={"Id": "abc123", "Config": None})
        with _patch_client(response):
            result = await container_inspect("test")
        assert result == {"Id": "abc123", "Config": None}

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

    async def test_image_pull_streamed_report(self) -> None:
        """libpod streams one JSON object per line; the last one is the result."""
        from mcp_podman_crunchtools.tools.images import image_pull

        body = '{"stream":"Copying blob 1a2b\\n"}\n{"id":"img123","images":["img123"]}\n'
        response = _mock_response(text=body, headers={"content-type": "application/json"})
        with _patch_client(response):
            result = await image_pull("ubi9:latest")
        assert result == {"id": "img123", "images": ["img123"]}

    async def test_image_pull_streamed_error_raises(self) -> None:
        """A pull that fails mid-stream still answers 200; the error is in-band."""
        from mcp_podman_crunchtools.errors import PodmanApiError
        from mcp_podman_crunchtools.tools.images import image_pull

        body = '{"stream":"Trying to pull...\\n"}\n{"error":"manifest unknown"}\n'
        response = _mock_response(text=body, headers={"content-type": "application/json"})
        with _patch_client(response), pytest.raises(PodmanApiError, match="manifest unknown"):
            await image_pull("ubi9:nope")

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

    async def test_image_prune_defaults_to_dangling_only(self) -> None:
        from mcp_podman_crunchtools.tools.images import image_prune

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=_mock_response(json_data=[]))

        async def mock_get_client(_self: object) -> AsyncMock:
            return mock_client

        with patch("mcp_podman_crunchtools.client.PodmanClient._get_client", mock_get_client):
            await image_prune()
        kwargs = mock_client.request.call_args.kwargs
        assert kwargs["url"] == "/images/prune"
        assert kwargs["params"] == {}

    async def test_image_prune_maps_cli_options_to_query_params(self) -> None:
        from mcp_podman_crunchtools.tools.images import PRUNE_TIMEOUT_SECONDS, image_prune

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=_mock_response(json_data=[]))

        async def mock_get_client(_self: object) -> AsyncMock:
            return mock_client

        with patch("mcp_podman_crunchtools.client.PodmanClient._get_client", mock_get_client):
            await image_prune(
                all=True, external=True, build_cache=True, filters={"until": ["168h"]}
            )
        kwargs = mock_client.request.call_args.kwargs
        assert kwargs["params"] == {
            "all": "true",
            "external": "true",
            "buildcache": "true",
            "filters": '{"until": ["168h"]}',
        }
        assert kwargs["timeout"] == PRUNE_TIMEOUT_SECONDS

    async def test_image_prune_rejects_unknown_filter_key(self) -> None:
        from mcp_podman_crunchtools.errors import InvalidInputError
        from mcp_podman_crunchtools.tools.images import image_prune

        with pytest.raises(InvalidInputError, match="filters"):
            await image_prune(filters={"reference": ["ubi9"]})

    async def test_image_prune_rejects_oversized_filter_value(self) -> None:
        from mcp_podman_crunchtools.errors import InvalidInputError
        from mcp_podman_crunchtools.tools.images import image_prune

        with pytest.raises(InvalidInputError, match="at most 255 characters"):
            await image_prune(filters={"label": ["a" * 256]})

    async def test_image_prune_tool_forwards_its_options(self) -> None:
        from mcp_podman_crunchtools import server

        tools = {tool.name: tool for tool in await server.mcp.list_tools()}
        assert set(tools["image_prune_tool"].parameters["properties"]) == {
            "all",
            "external",
            "build_cache",
            "filters",
        }

        with patch.object(server, "image_prune", AsyncMock(return_value={})) as prune:
            await server.image_prune_tool(all=True, filters={"until": ["168h"]})
        prune.assert_awaited_once_with(
            all=True, external=False, build_cache=False, filters={"until": ["168h"]}
        )

    async def test_requests_keep_the_configured_timeout_by_default(self) -> None:
        from mcp_podman_crunchtools.tools.images import image_list

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=_mock_response(json_data=[]))

        async def mock_get_client(_self: object) -> AsyncMock:
            return mock_client

        with patch("mcp_podman_crunchtools.client.PodmanClient._get_client", mock_get_client):
            await image_list()
        assert mock_client.request.call_args.kwargs["timeout"] is httpx.USE_CLIENT_DEFAULT


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


READ_ONLY = frozenset(
    {
        "container_list_tool",
        "container_inspect_tool",
        "container_logs_tool",
        "container_stats_tool",
        "image_list_tool",
        "image_inspect_tool",
        "pod_list_tool",
        "pod_inspect_tool",
        "network_list_tool",
        "network_inspect_tool",
        "volume_list_tool",
        "volume_inspect_tool",
        "system_info_tool",
        "system_df_tool",
    }
)
WRITES = frozenset(
    {
        "container_start_tool",
        "container_stop_tool",
        "container_restart_tool",
        "container_kill_tool",
        "container_rm_tool",
        "container_create_tool",
        "container_prune_tool",
        # A GET, but libpod runs ps(1) with the caller's ps_args, from the host or
        # through an exec session inside the container. Not a plain read.
        "container_top_tool",
        "image_pull_tool",
        "image_rm_tool",
        "image_prune_tool",
        "pod_start_tool",
        "pod_stop_tool",
        "pod_restart_tool",
        "pod_rm_tool",
        "pod_create_tool",
    }
)

# Arguments for each read-only tool, every optional parameter set so the
# request each one can build is the one checked.
READ_ONLY_CALLS: dict[str, dict[str, object]] = {
    "container_list_tool": {
        "all_containers": True,
        "filters": {"name": ["app"]},
        "limit": 5,
    },
    "container_inspect_tool": {"name": "app"},
    "container_logs_tool": {
        "name": "app",
        "tail": 10,
        "since": "2026-10-01T00:00:00Z",
        "timestamps": True,
    },
    "container_stats_tool": {"name": "app"},
    "image_list_tool": {"filters": {"reference": ["ubi9"]}},
    "image_inspect_tool": {"name": "quay.io/crunchtools/app:latest"},
    "pod_list_tool": {"filters": {"name": ["web"]}},
    "pod_inspect_tool": {"name": "web"},
    "network_list_tool": {"filters": {"name": ["podman"]}},
    "network_inspect_tool": {"name": "podman"},
    "volume_list_tool": {"filters": {"name": ["data"]}},
    "volume_inspect_tool": {"name": "data"},
    "system_info_tool": {},
    "system_df_tool": {},
}

SAFE_METHODS = frozenset({"GET", "HEAD"})

# Every read-only tool that puts a caller-supplied name into the request path.
NAMED_READS = sorted(name for name, args in READ_ONLY_CALLS.items() if "name" in args)

# `?` would end the path and `..` would climb out of the resource, which turns
# an inspect into GET /containers/x/healthcheck: a GET that runs the health check.
HOSTILE_NAME = "../containers/x/healthcheck?"

# "/resource/name/action": the name adds no separator of its own.
PATH_SEPARATORS = 3


async def _requests_sent(name: str, args: dict[str, object]) -> list[dict[str, object]]:
    """Call a registered tool against a mocked socket and return its requests."""
    from mcp_podman_crunchtools.server import mcp as server

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=_mock_response(json_data={"Id": "abc123"}))

    async def mock_get_client(_self: object) -> AsyncMock:
        return mock_client

    with patch("mcp_podman_crunchtools.client.PodmanClient._get_client", mock_get_client):
        await server.call_tool(name, args)
    return [call.kwargs for call in mock_client.request.await_args_list]


class TestReadOnlyAnnotation:
    """Every registered tool is classified, and the reads really only read."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        _setup_config()

    async def test_every_tool_is_classified(self) -> None:
        from mcp_podman_crunchtools.server import mcp as server

        tools = await server.list_tools()
        assert READ_ONLY.isdisjoint(WRITES)
        assert {tool.name for tool in tools} == READ_ONLY | WRITES
        annotated = {
            tool.name
            for tool in tools
            if tool.annotations is not None
            and tool.annotations.model_dump(by_alias=True).get("readOnlyHint") is True
        }
        assert annotated == READ_ONLY

    def test_every_read_only_tool_has_a_call(self) -> None:
        assert set(READ_ONLY_CALLS) == READ_ONLY

    @pytest.mark.parametrize("name", sorted(READ_ONLY))
    async def test_read_only_tool_sends_only_safe_methods(self, name: str) -> None:
        requests = await _requests_sent(name, READ_ONLY_CALLS[name])
        assert requests, f"{name} sent nothing"
        assert {request["method"] for request in requests} <= SAFE_METHODS
        assert all(request["json"] is None for request in requests)

    @pytest.mark.parametrize(
        ("name", "args", "method"),
        [
            ("container_stop_tool", {"name": "app"}, "POST"),
            ("image_rm_tool", {"name": "app"}, "DELETE"),
        ],
    )
    async def test_method_check_sees_a_write(
        self, name: str, args: dict[str, object], method: str
    ) -> None:
        """Control: the same probe reports the unsafe method of a write tool."""
        requests = await _requests_sent(name, args)
        assert {request["method"] for request in requests} == {method}
        assert not {request["method"] for request in requests} <= SAFE_METHODS

    @pytest.mark.parametrize("name", NAMED_READS)
    async def test_read_only_tool_keeps_a_name_in_one_path_segment(self, name: str) -> None:
        """A name cannot re-address the GET to another endpoint or add a query."""
        resource = name.partition("_")[0] + "s"
        requests = await _requests_sent(name, {"name": HOSTILE_NAME})
        assert len(requests) == 1
        url = str(requests[0]["url"])
        assert url.startswith(f"/{resource}/..%2Fcontainers%2Fx%2Fhealthcheck%3F/")
        assert "?" not in url
        assert url.count("/") == PATH_SEPARATORS

    async def test_image_name_with_registry_path_is_one_segment(self) -> None:
        requests = await _requests_sent(
            "image_inspect_tool", {"name": "quay.io/crunchtools/app:latest"}
        )
        assert requests[0]["url"] == "/images/quay.io%2Fcrunchtools%2Fapp%3Alatest/json"
