"""Configuration, write-gates, and alert descriptions for Starlink Blade MCP."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_DISH_ADDRESS = "192.168.100.1:9200"
DEFAULT_TIMEOUT = 10
DEFAULT_HISTORY_SAMPLES = 60


@dataclass
class Config:
    """Runtime configuration resolved from environment."""

    dish_address: str
    timeout: int
    write_enabled: bool

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            dish_address=os.environ.get("STARLINK_DISH_ADDRESS", DEFAULT_DISH_ADDRESS),
            timeout=int(os.environ.get("STARLINK_TIMEOUT", str(DEFAULT_TIMEOUT))),
            write_enabled=os.environ.get("STARLINK_WRITE_ENABLED", "").lower() == "true",
        )


def check_write_gate(config: Config) -> str | None:
    """Return error string if writes are disabled, else None."""
    if not config.write_enabled:
        return "Error: Write operations disabled. Set STARLINK_WRITE_ENABLED=true to enable."
    return None


def check_confirm_gate(confirm: bool, action: str) -> str | None:
    """Return error string if confirm is False, else None."""
    if not confirm:
        return f"Error: {action} requires explicit confirmation. Set confirm=true to proceed."
    return None


# Human-readable alert descriptions keyed by proto field name.
ALERT_DESCRIPTIONS: dict[str, str] = {
    "motors_stuck": "Dish motors are stuck — may need physical inspection",
    "thermal_shutdown": "Dish shut down due to overheating",
    "thermal_throttle": "Performance reduced due to high temperature",
    "unexpected_location": "Dish location does not match registered service address",
    "mast_not_near_vertical": "Mounting mast is not vertical — check installation",
    "slow_ethernet_speeds": "Ethernet negotiated below 1 Gbps — check cable/adapter",
    "roaming": "Dish is in roaming mode (away from registered address)",
    "install_pending": "Installation is not yet complete",
    "is_heating": "Dish heater active (snow/ice melt mode)",
    "power_supply_thermal_throttle": "Power supply is thermal throttling",
    "is_power_save_idle": "Dish is in power-save sleep mode",
    "moving_while_not_mobile": "Dish is moving but no mobility plan active",
    "moving_fast_while_not_aviation": "Moving too fast for non-aviation plan",
    "dbf_telem_stale": "Digital beamforming telemetry is stale",
    "moving_too_fast_for_policy": "Movement speed exceeds plan policy limit",
    "low_motor_current": "Motor current below expected — potential motor issue",
    "lower_signal_than_predicted": "Signal weaker than predicted — check obstructions",
    "slow_ethernet_speeds_100": "Ethernet at 100 Mbps — need Cat5e or better cable",
    "obstruction_map_reset": "Obstruction map was recently reset",
    "dish_water_detected": "Water detected on dish surface",
    "router_water_detected": "Water detected on Starlink router",
    "upsu_router_port_slow": "Router Ethernet port negotiated at low speed",
}

# Dishy state descriptions
STATE_DESCRIPTIONS: dict[str, str] = {
    "CONNECTED": "Online — connected to satellite network",
    "BOOTING": "Dish is booting up",
    "SEARCHING": "Searching for satellites",
    "STOWED": "Dish is physically stowed",
    "THERMAL_SHUTDOWN": "Shut down due to overheating",
    "SLEEPING": "In power-save sleep mode",
    "MOVING": "Dish is physically moving",
    "NO_SATS": "No satellites in view",
    "OBSTRUCTED": "View is obstructed",
    "NO_DOWNLINK": "No downlink from satellite",
    "NO_PINGS": "Connected but no pings reaching PoP",
    "DISABLED": "Dish is disabled",
    "UNKNOWN": "Unknown state",
}
