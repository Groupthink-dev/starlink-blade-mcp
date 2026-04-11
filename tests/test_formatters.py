"""Tests for output formatters."""

from __future__ import annotations

from typing import Any

from starlink_blade_mcp.formatters import (
    format_alerts,
    format_diagnostics,
    format_history,
    format_location,
    format_obstruction,
    format_status,
)
from starlink_blade_mcp.grpc_client import DishHistory, DishStatus


class TestFormatStatus:
    def test_contains_identity(self, sample_dish_status: DishStatus) -> None:
        out = format_status(sample_dish_status)
        assert "ut01000000" in out
        assert "rev4_proto3_prod1" in out

    def test_contains_throughput(self, sample_dish_status: DishStatus) -> None:
        out = format_status(sample_dish_status)
        assert "85.0" in out  # 85 Mbps down
        assert "12.5" in out  # 12.5 Mbps up

    def test_contains_state(self, sample_dish_status: DishStatus) -> None:
        out = format_status(sample_dish_status)
        assert "Online" in out or "CONNECTED" in out

    def test_contains_orientation(self, sample_dish_status: DishStatus) -> None:
        out = format_status(sample_dish_status)
        assert "180.5" in out
        assert "72.3" in out


class TestFormatAlerts:
    def test_active_alerts(self, sample_alerts_active: dict[str, bool]) -> None:
        out = format_alerts(sample_alerts_active)
        assert "Active Alerts (3)" in out
        assert "thermal_throttle" in out
        assert "slow_ethernet_speeds" in out
        assert "is_heating" in out

    def test_no_alerts(self, sample_alerts_none: dict[str, bool]) -> None:
        out = format_alerts(sample_alerts_none)
        assert "No active alerts" in out

    def test_empty_dict(self) -> None:
        assert "No active alerts" in format_alerts({})


class TestFormatObstruction:
    def test_contains_fraction(self, sample_obstruction: dict[str, Any]) -> None:
        out = format_obstruction(sample_obstruction)
        assert "2.3%" in out

    def test_contains_wedges(self, sample_obstruction: dict[str, Any]) -> None:
        out = format_obstruction(sample_obstruction)
        assert "Wedges (12)" in out
        assert "0.120" in out  # highest wedge

    def test_currently_not_obstructed(self, sample_obstruction: dict[str, Any]) -> None:
        out = format_obstruction(sample_obstruction)
        assert "currently=no" in out


class TestFormatLocation:
    def test_with_coords(self, sample_location: dict[str, Any]) -> None:
        out = format_location(sample_location)
        assert "-42.882100" in out
        assert "147.327200" in out
        assert "52.4m" in out

    def test_empty_location(self) -> None:
        out = format_location({})
        assert "unavailable" in out


class TestFormatHistory:
    def test_summary_table(self, sample_history: DishHistory) -> None:
        out = format_history(sample_history, 10)
        assert "History Summary" in out
        assert "ping_drop" in out
        assert "latency" in out
        assert "down" in out
        assert "up" in out

    def test_empty_history(self) -> None:
        h = DishHistory(general={}, bulk={})
        out = format_history(h, 10)
        assert "No history data" in out


class TestFormatDiagnostics:
    def test_contains_hw_info(self, sample_dish_status: DishStatus) -> None:
        out = format_diagnostics(sample_dish_status)
        assert "rev4_proto3_prod1" in out
        assert "2026.04.10" in out

    def test_contains_gps(self, sample_dish_status: DishStatus) -> None:
        out = format_diagnostics(sample_dish_status)
        assert "GPS" in out
        assert "sats=12" in out

    def test_contains_alert_count(self, sample_dish_status: DishStatus) -> None:
        out = format_diagnostics(sample_dish_status)
        assert "Active alerts: 3" in out
