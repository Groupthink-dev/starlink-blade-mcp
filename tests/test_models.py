"""Tests for configuration and gate logic."""

from __future__ import annotations

import os
from unittest.mock import patch

from starlink_blade_mcp.models import (
    ALERT_DESCRIPTIONS,
    Config,
    check_confirm_gate,
    check_write_gate,
)


class TestConfig:
    def test_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            cfg = Config.from_env()
        assert cfg.dish_address == "192.168.100.1:9200"
        assert cfg.timeout == 10
        assert cfg.write_enabled is False

    def test_custom_env(self) -> None:
        env = {
            "STARLINK_DISH_ADDRESS": "10.0.0.1:9200",
            "STARLINK_TIMEOUT": "30",
            "STARLINK_WRITE_ENABLED": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = Config.from_env()
        assert cfg.dish_address == "10.0.0.1:9200"
        assert cfg.timeout == 30
        assert cfg.write_enabled is True

    def test_write_enabled_case_insensitive(self) -> None:
        with patch.dict(os.environ, {"STARLINK_WRITE_ENABLED": "True"}, clear=True):
            cfg = Config.from_env()
        assert cfg.write_enabled is True


class TestWriteGate:
    def test_blocked_when_disabled(self) -> None:
        cfg = Config(dish_address="x", timeout=10, write_enabled=False)
        result = check_write_gate(cfg)
        assert result is not None
        assert "disabled" in result.lower()

    def test_passes_when_enabled(self) -> None:
        cfg = Config(dish_address="x", timeout=10, write_enabled=True)
        assert check_write_gate(cfg) is None


class TestConfirmGate:
    def test_blocked_without_confirm(self) -> None:
        result = check_confirm_gate(False, "Reboot")
        assert result is not None
        assert "confirm" in result.lower()

    def test_passes_with_confirm(self) -> None:
        assert check_confirm_gate(True, "Reboot") is None


class TestAlertDescriptions:
    def test_all_descriptions_are_strings(self) -> None:
        for key, desc in ALERT_DESCRIPTIONS.items():
            assert isinstance(key, str)
            assert isinstance(desc, str)
            assert len(desc) > 10

    def test_known_alerts_present(self) -> None:
        expected = ["motors_stuck", "thermal_throttle", "slow_ethernet_speeds", "is_heating"]
        for alert in expected:
            assert alert in ALERT_DESCRIPTIONS
