"""Tests for the gRPC client wrapper (mocked — no live dish required)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from starlink_blade_mcp.grpc_client import StarlinkClient, StarlinkError
from starlink_blade_mcp.models import Config


@pytest.fixture
def config() -> Config:
    return Config(dish_address="192.168.100.1:9200", timeout=10, write_enabled=True)


@pytest.fixture
def mock_starlink_grpc() -> MagicMock:
    """Patch the starlink_grpc module."""
    mock = MagicMock()
    mock.ChannelContext.return_value = MagicMock()
    mock.GrpcError = type("GrpcError", (Exception,), {})
    return mock


class TestGetStatus:
    def test_returns_dish_status(self, config: Config, mock_starlink_grpc: MagicMock) -> None:
        mock_starlink_grpc.status_data.return_value = (
            {"id": "test", "state": "CONNECTED"},
            {"pop_ping_drop_rate": 0.001},
            {"fraction_obstructed": 0.02},
            {"thermal_throttle": False},
        )
        with patch.dict("sys.modules", {"starlink_grpc": mock_starlink_grpc}):
            client = StarlinkClient(config)
            status = client.get_status()

        assert status.general["id"] == "test"
        assert status.status["pop_ping_drop_rate"] == 0.001
        assert status.obstruction["fraction_obstructed"] == 0.02
        assert status.alerts["thermal_throttle"] is False

    def test_grpc_error_raises_starlink_error(self, config: Config, mock_starlink_grpc: MagicMock) -> None:
        mock_starlink_grpc.status_data.side_effect = mock_starlink_grpc.GrpcError("timeout")
        with patch.dict("sys.modules", {"starlink_grpc": mock_starlink_grpc}):
            client = StarlinkClient(config)
            with pytest.raises(StarlinkError, match="gRPC error"):
                client.get_status()


class TestGetLocation:
    def test_returns_coordinates(self, config: Config, mock_starlink_grpc: MagicMock) -> None:
        mock_starlink_grpc.location_data.return_value = {
            "latitude": -42.88,
            "longitude": 147.33,
            "altitude": 52.0,
        }
        with patch.dict("sys.modules", {"starlink_grpc": mock_starlink_grpc}):
            client = StarlinkClient(config)
            loc = client.get_location()
        assert loc["latitude"] == -42.88


class TestGetHistory:
    def test_returns_bulk_data(self, config: Config, mock_starlink_grpc: MagicMock) -> None:
        mock_starlink_grpc.history_bulk_data.return_value = (
            {"id": "test"},
            {"pop_ping_drop_rate": [0.001, 0.002]},
        )
        with patch.dict("sys.modules", {"starlink_grpc": mock_starlink_grpc}):
            client = StarlinkClient(config)
            history = client.get_history(samples=2)
        assert len(history.bulk["pop_ping_drop_rate"]) == 2


class TestControlOperations:
    def test_reboot(self, config: Config, mock_starlink_grpc: MagicMock) -> None:
        with patch.dict("sys.modules", {"starlink_grpc": mock_starlink_grpc}):
            client = StarlinkClient(config)
            client.reboot()
        mock_starlink_grpc.reboot.assert_called_once()

    def test_stow(self, config: Config, mock_starlink_grpc: MagicMock) -> None:
        with patch.dict("sys.modules", {"starlink_grpc": mock_starlink_grpc}):
            client = StarlinkClient(config)
            client.stow()
        ctx = mock_starlink_grpc.ChannelContext.return_value
        mock_starlink_grpc.set_stow_state.assert_called_once_with(unstow=False, context=ctx)

    def test_unstow(self, config: Config, mock_starlink_grpc: MagicMock) -> None:
        with patch.dict("sys.modules", {"starlink_grpc": mock_starlink_grpc}):
            client = StarlinkClient(config)
            client.unstow()
        ctx = mock_starlink_grpc.ChannelContext.return_value
        mock_starlink_grpc.set_stow_state.assert_called_once_with(unstow=True, context=ctx)
