"""Shared fixtures for Starlink Blade MCP tests."""

from __future__ import annotations

from typing import Any

import pytest

from starlink_blade_mcp.grpc_client import DishHistory, DishStatus


@pytest.fixture
def sample_general() -> dict[str, Any]:
    return {
        "id": "ut01000000-00000000-00abcdef",
        "hardware_version": "rev4_proto3_prod1",
        "software_version": "2026.04.10.mr12345",
        "state": "CONNECTED",
        "uptime": 345600,
        "is_snr_above_noise_floor": True,
        "gps_valid": True,
        "gps_sats": 12,
    }


@pytest.fixture
def sample_status_dict() -> dict[str, Any]:
    return {
        "pop_ping_drop_rate": 0.0012,
        "pop_ping_latency_ms": 32.5,
        "downlink_throughput_bps": 85_000_000.0,
        "uplink_throughput_bps": 12_500_000.0,
        "snr": 9.2,
        "direction_azimuth": 180.5,
        "direction_elevation": 72.3,
    }


@pytest.fixture
def sample_obstruction() -> dict[str, Any]:
    return {
        "fraction_obstructed": 0.023,
        "currently_obstructed": False,
        "obstruction_duration": 0.5,
        "obstruction_interval": 120.0,
        "valid_s": 3600,
        "wedges_fraction_obstructed": [0.00, 0.01, 0.05, 0.12, 0.08, 0.03, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00],
    }


@pytest.fixture
def sample_alerts_active() -> dict[str, bool]:
    return {
        "motors_stuck": False,
        "thermal_shutdown": False,
        "thermal_throttle": True,
        "unexpected_location": False,
        "slow_ethernet_speeds": True,
        "is_heating": True,
        "roaming": False,
    }


@pytest.fixture
def sample_alerts_none() -> dict[str, bool]:
    return {
        "motors_stuck": False,
        "thermal_shutdown": False,
        "thermal_throttle": False,
    }


@pytest.fixture
def sample_dish_status(
    sample_general: dict[str, Any],
    sample_status_dict: dict[str, Any],
    sample_obstruction: dict[str, Any],
    sample_alerts_active: dict[str, bool],
) -> DishStatus:
    return DishStatus(
        general=sample_general,
        status=sample_status_dict,
        obstruction=sample_obstruction,
        alerts=sample_alerts_active,
    )


@pytest.fixture
def sample_location() -> dict[str, Any]:
    return {
        "latitude": -42.8821,
        "longitude": 147.3272,
        "altitude": 52.4,
    }


@pytest.fixture
def sample_history() -> DishHistory:
    n = 10
    return DishHistory(
        general={"id": "test-dish"},
        bulk={
            "pop_ping_drop_rate": [0.001 * i for i in range(n)],
            "pop_ping_latency_ms": [25.0 + i * 2.5 for i in range(n)],
            "downlink_throughput_bps": [50_000_000.0 + i * 5_000_000 for i in range(n)],
            "uplink_throughput_bps": [8_000_000.0 + i * 1_000_000 for i in range(n)],
            "power_in": [50.0 + i * 0.5 for i in range(n)],
            "snr": [8.0 + i * 0.2 for i in range(n)],
        },
    )
