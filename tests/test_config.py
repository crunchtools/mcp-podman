"""Tests for socket path resolution and validation."""

import os
import socket
import stat
from pathlib import Path
from typing import Any

import pytest

from mcp_podman_crunchtools.config import Config
from mcp_podman_crunchtools.errors import ConfigurationError

SOCKET_ENV_VARS = ("PODMAN_SOCKET_FILE", "PODMAN_SOCKET", "XDG_RUNTIME_DIR", "PODMAN_TIMEOUT")


@pytest.fixture(autouse=True)
def _clear_socket_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in SOCKET_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def _resolve() -> str:
    """Call the resolver without running the rest of Config.__init__."""
    return Config._resolve_socket_path(Config.__new__(Config))


def _listening_socket(path: Path) -> socket.socket:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(path))
    return sock


class TestResolveSocketPath:
    """PODMAN_SOCKET_FILE > PODMAN_SOCKET > XDG > per-uid > rootful."""

    def test_socket_file_contents_win(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pointer = tmp_path / "socket-path"
        pointer.write_text("  /run/from-file.sock\n")
        pointer.chmod(0o600)
        monkeypatch.setenv("PODMAN_SOCKET_FILE", str(pointer))
        monkeypatch.setenv("PODMAN_SOCKET", "/run/ignored.sock")

        assert _resolve() == "/run/from-file.sock"

    def test_missing_socket_file_is_an_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PODMAN_SOCKET_FILE", str(tmp_path / "absent"))

        with pytest.raises(ConfigurationError, match="does not exist"):
            _resolve()

    def test_group_readable_socket_file_warns(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        pointer = tmp_path / "socket-path"
        pointer.write_text("/run/loose.sock")
        pointer.chmod(0o640)
        monkeypatch.setenv("PODMAN_SOCKET_FILE", str(pointer))

        assert _resolve() == "/run/loose.sock"
        assert "more permissive than 0600" in caplog.text

    def test_owner_only_socket_file_is_quiet(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        pointer = tmp_path / "socket-path"
        pointer.write_text("/run/tight.sock")
        pointer.chmod(stat.S_IRUSR | stat.S_IWUSR)
        monkeypatch.setenv("PODMAN_SOCKET_FILE", str(pointer))

        assert _resolve() == "/run/tight.sock"
        assert "more permissive" not in caplog.text

    def test_explicit_socket_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PODMAN_SOCKET", "/run/explicit.sock")

        assert _resolve() == "/run/explicit.sock"

    def test_xdg_runtime_dir_is_probed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        podman_dir = tmp_path / "podman"
        podman_dir.mkdir()
        (podman_dir / "podman.sock").touch()
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))

        assert _resolve() == f"{tmp_path}/podman/podman.sock"

    def test_xdg_is_skipped_when_the_socket_is_absent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
        monkeypatch.setattr(Path, "exists", lambda _: False)

        with pytest.raises(ConfigurationError, match="No Podman socket found"):
            _resolve()

    def test_per_uid_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        expected = f"/run/user/{os.getuid()}/podman/podman.sock"
        monkeypatch.setattr(Path, "exists", lambda p: str(p) == expected)

        assert _resolve() == expected

    def test_rootful_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            Path, "exists", lambda p: str(p) == "/run/podman/podman.sock"
        )

        assert _resolve() == "/run/podman/podman.sock"

    def test_nothing_found_names_the_remedies(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Path, "exists", lambda _: False)

        with pytest.raises(ConfigurationError, match="PODMAN_SOCKET"):
            _resolve()


class TestConfig:
    """End-to-end construction against a real Unix socket."""

    def test_accepts_a_real_socket(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "podman.sock"
        with _listening_socket(path):
            monkeypatch.setenv("PODMAN_SOCKET", str(path))

            config = Config()

            assert config.socket_path == str(path)
            assert config.timeout == 30
            assert str(path) in repr(config)

    def test_timeout_comes_from_the_environment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "podman.sock"
        with _listening_socket(path):
            monkeypatch.setenv("PODMAN_SOCKET", str(path))
            monkeypatch.setenv("PODMAN_TIMEOUT", "5")

            assert Config().timeout == 5

    def test_rejects_a_path_that_is_not_a_socket(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        regular = tmp_path / "not-a-socket"
        regular.touch()
        monkeypatch.setenv("PODMAN_SOCKET", str(regular))

        with pytest.raises(ConfigurationError, match="not a Unix socket"):
            Config()

    def test_rejects_a_missing_socket(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PODMAN_SOCKET", str(tmp_path / "absent.sock"))

        with pytest.raises(ConfigurationError, match="does not exist"):
            Config()


def test_get_config_is_a_singleton(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp_podman_crunchtools import config as config_mod

    path = tmp_path / "podman.sock"
    with _listening_socket(path):
        monkeypatch.setenv("PODMAN_SOCKET", str(path))

        first: Any = config_mod.get_config()
        assert config_mod.get_config() is first
