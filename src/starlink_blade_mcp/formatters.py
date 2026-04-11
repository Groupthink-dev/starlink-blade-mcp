"""Token-efficient output formatters for Starlink Blade MCP.

All formatters return compact strings optimised for LLM consumption:
- Pipe-delimited fields
- Null-field omission
- Human-readable units (Mbps, ms, dB, degrees)
- Statistical summaries over raw sample dumps
"""

from __future__ import annotations

from typing import Any

from starlink_blade_mcp.grpc_client import DishHistory, DishStatus
from starlink_blade_mcp.models import ALERT_DESCRIPTIONS, STATE_DESCRIPTIONS


def _bps_to_mbps(bps: float | None) -> str:
    """Convert bits-per-second to compact Mbps string."""
    if bps is None:
        return "—"
    return f"{bps / 1_000_000:.1f}"


def _seconds_to_human(seconds: float | int | None) -> str:
    """Convert seconds to compact human-readable duration."""
    if seconds is None:
        return "—"
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    if s < 86400:
        return f"{s // 3600}h {(s % 3600) // 60}m"
    return f"{s // 86400}d {(s % 86400) // 3600}h"


def _pct(fraction: float | None) -> str:
    """Format a 0–1 fraction as a percentage string."""
    if fraction is None:
        return "—"
    return f"{fraction * 100:.1f}%"


def format_status(status: DishStatus) -> str:
    """Format full dish status as compact multi-line string."""
    g = status.general
    s = status.status
    o = status.obstruction

    dish_id = g.get("id", "unknown")
    hw = g.get("hardware_version", "?")
    sw = g.get("software_version", "?")
    state_raw = g.get("state", "UNKNOWN")
    state_desc = STATE_DESCRIPTIONS.get(state_raw, state_raw)
    uptime = _seconds_to_human(g.get("uptime"))

    ping_drop = s.get("pop_ping_drop_rate")
    latency = s.get("pop_ping_latency_ms")
    down_bps = s.get("downlink_throughput_bps")
    up_bps = s.get("uplink_throughput_bps")
    snr = s.get("snr")
    snr_ok = g.get("is_snr_above_noise_floor")

    azimuth = s.get("direction_azimuth")
    elevation = s.get("direction_elevation")

    frac_obstructed = o.get("fraction_obstructed")

    lines = [
        "Starlink Dish Status",
        f"ID: {dish_id} | HW: {hw} | SW: {sw}",
        f"State: {state_desc} | Uptime: {uptime}",
    ]

    # Connectivity
    parts = []
    if ping_drop is not None:
        parts.append(f"ping_drop={ping_drop:.4f}")
    if latency is not None:
        parts.append(f"latency={latency:.1f}ms")
    if parts:
        lines.append(f"Connectivity: {' | '.join(parts)}")

    # Throughput
    if down_bps is not None or up_bps is not None:
        lines.append(f"Throughput: down={_bps_to_mbps(down_bps)}Mbps | up={_bps_to_mbps(up_bps)}Mbps")

    # Signal
    sig_parts = []
    if snr is not None:
        sig_parts.append(f"SNR={snr:.1f}dB")
    if snr_ok is not None:
        sig_parts.append(f"above_noise={'yes' if snr_ok else 'NO'}")
    if sig_parts:
        lines.append(f"Signal: {' | '.join(sig_parts)}")

    # Orientation
    if azimuth is not None or elevation is not None:
        az_str = f"{azimuth:.1f}°" if azimuth is not None else "—"
        el_str = f"{elevation:.1f}°" if elevation is not None else "—"
        lines.append(f"Orientation: azimuth={az_str} | elevation={el_str}")

    # Obstruction summary
    if frac_obstructed is not None:
        lines.append(f"Obstruction: {_pct(frac_obstructed)}")

    return "\n".join(lines)


def format_alerts(alerts: dict[str, bool]) -> str:
    """Format active alerts with human-readable descriptions."""
    active = {k: v for k, v in alerts.items() if v}
    if not active:
        return "No active alerts."

    lines = [f"Active Alerts ({len(active)}):"]
    for name in sorted(active):
        desc = ALERT_DESCRIPTIONS.get(name, name.replace("_", " "))
        lines.append(f"  - {name}: {desc}")
    return "\n".join(lines)


def format_obstruction(obstruction: dict[str, Any]) -> str:
    """Format obstruction data as compact summary."""
    frac = obstruction.get("fraction_obstructed")
    currently = obstruction.get("currently_obstructed")
    duration = obstruction.get("obstruction_duration")
    interval = obstruction.get("obstruction_interval")
    valid_s = obstruction.get("valid_s")

    lines = ["Obstruction Summary"]

    parts = []
    if frac is not None:
        parts.append(f"fraction={_pct(frac)}")
    if currently is not None:
        parts.append(f"currently={'YES' if currently else 'no'}")
    if duration is not None:
        parts.append(f"avg_duration={duration:.1f}s")
    if interval is not None:
        parts.append(f"avg_interval={interval:.0f}s")
    if valid_s is not None:
        parts.append(f"valid={_seconds_to_human(valid_s)}")
    if parts:
        lines.append(" | ".join(parts))

    # Wedge data (12 directions)
    wedges = obstruction.get("wedges_fraction_obstructed")
    if wedges and isinstance(wedges, list):
        wedge_str = " ".join(f"{w:.3f}" if w is not None else "—" for w in wedges)
        lines.append(f"Wedges (12): {wedge_str}")

    return "\n".join(lines)


def format_location(location: dict[str, Any]) -> str:
    """Format GPS location."""
    lat = location.get("latitude")
    lon = location.get("longitude")
    alt = location.get("altitude")

    if lat is None and lon is None:
        return "Location: unavailable (enable in Starlink app → Settings → Advanced → Debug Data)"

    parts = []
    if lat is not None:
        parts.append(f"lat={lat:.6f}")
    if lon is not None:
        parts.append(f"lon={lon:.6f}")
    if alt is not None:
        parts.append(f"alt={alt:.1f}m")

    return f"Location: {' | '.join(parts)}"


def format_history(history: DishHistory, samples: int) -> str:
    """Format history as statistical summary (min/avg/max) — much more token-efficient than raw samples."""
    bulk = history.bulk
    if not bulk:
        return "No history data available."

    metrics = [
        ("ping_drop", "pop_ping_drop_rate", "", ".4f"),
        ("latency", "pop_ping_latency_ms", "ms", ".1f"),
        ("down", "downlink_throughput_bps", "Mbps", None),
        ("up", "uplink_throughput_bps", "Mbps", None),
        ("power", "power_in", "W", ".1f"),
        ("snr", "snr", "dB", ".1f"),
    ]

    lines = [f"History Summary (last {samples} samples, 1s intervals)", ""]
    lines.append(f"{'metric':<12} {'min':>8} {'avg':>8} {'max':>8} {'unit':>6}")
    lines.append("-" * 44)

    for label, key, unit, fmt in metrics:
        values = bulk.get(key)
        if not values:
            continue
        clean = [v for v in values if v is not None]
        if not clean:
            continue

        if key in ("downlink_throughput_bps", "uplink_throughput_bps"):
            clean = [v / 1_000_000 for v in clean]

        mn = min(clean)
        avg = sum(clean) / len(clean)
        mx = max(clean)

        if fmt:
            lines.append(f"{label:<12} {mn:>8{fmt}} {avg:>8{fmt}} {mx:>8{fmt}} {unit:>6}")
        else:
            lines.append(f"{label:<12} {mn:>8.1f} {avg:>8.1f} {mx:>8.1f} {unit:>6}")

    return "\n".join(lines)


def format_diagnostics(status: DishStatus) -> str:
    """Format hardware diagnostics from status data."""
    g = status.general

    lines = ["Dish Diagnostics"]
    hw = g.get("hardware_version", "?")
    sw = g.get("software_version", "?")
    lines.append(f"ID: {g.get('id', '?')} | HW: {hw} | SW: {sw}")

    state = g.get("state", "UNKNOWN")
    state_desc = STATE_DESCRIPTIONS.get(state, state)
    lines.append(f"State: {state_desc}")
    lines.append(f"Uptime: {_seconds_to_human(g.get('uptime'))}")

    # GPS readiness
    gps_parts = []
    gps_ready = g.get("gps_valid")
    if gps_ready is not None:
        gps_parts.append(f"ready={'yes' if gps_ready else 'no'}")
    gps_sats = g.get("gps_sats")
    if gps_sats is not None:
        gps_parts.append(f"sats={gps_sats}")
    if gps_parts:
        lines.append(f"GPS: {' | '.join(gps_parts)}")

    # Active alerts count
    active_alerts = sum(1 for v in status.alerts.values() if v)
    lines.append(f"Active alerts: {active_alerts}")

    return "\n".join(lines)
