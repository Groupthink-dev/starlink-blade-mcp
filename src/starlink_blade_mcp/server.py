"""Starlink Blade MCP Server — local gRPC dish monitoring, alerts, and control.

Wraps the Starlink dish's local gRPC interface (192.168.100.1:9200) via
starlink-grpc-core as MCP tools. No cloud credentials required — all data
comes directly from the dish on the local network.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from starlink_blade_mcp.formatters import (
    format_alerts,
    format_diagnostics,
    format_history,
    format_location,
    format_obstruction,
    format_status,
)
from starlink_blade_mcp.grpc_client import StarlinkClient, StarlinkError
from starlink_blade_mcp.models import (
    DEFAULT_HISTORY_SAMPLES,
    Config,
    check_confirm_gate,
    check_write_gate,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Transport configuration
# ---------------------------------------------------------------------------

TRANSPORT = os.environ.get("STARLINK_MCP_TRANSPORT", "stdio")
HTTP_HOST = os.environ.get("STARLINK_MCP_HOST", "127.0.0.1")
HTTP_PORT = int(os.environ.get("STARLINK_MCP_PORT", "8770"))

# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "StarlinkBlade",
    instructions=(
        "Starlink dish operations via local gRPC. "
        "Read dish status, alerts, obstruction map, throughput history, GPS location, and diagnostics. "
        "Control operations (reboot, stow, sleep) require STARLINK_WRITE_ENABLED=true."
    ),
)

# Lazy-initialized client
_client: StarlinkClient | None = None


def _get_client() -> StarlinkClient:
    global _client  # noqa: PLW0603
    if _client is None:
        config = Config.from_env()
        _client = StarlinkClient(config)
    return _client


def _error(e: StarlinkError) -> str:
    return f"Error: {e}"


async def _run(fn, *args, **kwargs):  # type: ignore[no-untyped-def]
    """Run a blocking gRPC call in a thread."""
    return await asyncio.to_thread(fn, *args, **kwargs)


# ===========================================================================
# READ TOOLS
# ===========================================================================


@mcp.tool()
async def starlink_status() -> str:
    """Get current dish status: identity, connectivity, signal quality, orientation, uptime.

    Returns compact summary with dish ID, hardware/software version, state,
    ping drop rate, latency, throughput, SNR, and antenna orientation.
    """
    try:
        client = _get_client()
        status = await _run(client.get_status)
        return format_status(status)
    except StarlinkError as e:
        return _error(e)


@mcp.tool()
async def starlink_alerts() -> str:
    """Get active dish alerts with human-readable descriptions.

    Checks 22 alert flags covering hardware (motors, thermal), connectivity
    (ethernet speed, signal), environment (water, obstruction), and policy
    (roaming, movement). Only active alerts are shown.
    """
    try:
        client = _get_client()
        status = await _run(client.get_status)
        return format_alerts(status.alerts)
    except StarlinkError as e:
        return _error(e)


@mcp.tool()
async def starlink_obstruction() -> str:
    """Get obstruction data: fraction obstructed, 12-wedge directional map, and timing.

    Shows overall obstruction percentage, whether currently obstructed,
    average obstruction duration and interval, and per-wedge fractions
    (12 directions around the dish).
    """
    try:
        client = _get_client()
        status = await _run(client.get_status)
        return format_obstruction(status.obstruction)
    except StarlinkError as e:
        return _error(e)


@mcp.tool()
async def starlink_history(
    samples: Annotated[
        int, Field(description="Number of 1-second samples (max ~900)", ge=1, le=900)
    ] = DEFAULT_HISTORY_SAMPLES,
) -> str:
    """Get recent throughput/latency/power history as statistical summary (min/avg/max).

    Returns aggregated stats over the requested sample window — much more
    token-efficient than raw per-second data. Covers ping drop rate, latency,
    download/upload throughput, power consumption, and SNR.
    """
    try:
        client = _get_client()
        history = await _run(client.get_history, samples)
        return format_history(history, samples)
    except StarlinkError as e:
        return _error(e)


@mcp.tool()
async def starlink_location() -> str:
    """Get dish GPS location (latitude, longitude, altitude).

    Requires opt-in: Starlink app → Settings → Advanced → Debug Data.
    Returns 'unavailable' if GPS sharing is not enabled.
    """
    try:
        client = _get_client()
        location = await _run(client.get_location)
        return format_location(location)
    except StarlinkError as e:
        return _error(e)


@mcp.tool()
async def starlink_diagnostics() -> str:
    """Get hardware diagnostics: firmware, GPS status, active alert count.

    Useful for troubleshooting — shows hardware version, software version,
    dish state with description, uptime, GPS satellite count, and total
    active alerts.
    """
    try:
        client = _get_client()
        status = await _run(client.get_status)
        return format_diagnostics(status)
    except StarlinkError as e:
        return _error(e)


# ===========================================================================
# WRITE TOOLS (gated)
# ===========================================================================


@mcp.tool()
async def starlink_reboot(
    confirm: Annotated[bool, Field(description="Must be true to execute reboot")] = False,
) -> str:
    """Reboot the Starlink dish. Requires STARLINK_WRITE_ENABLED=true AND confirm=true.

    The dish will lose connectivity for 2-5 minutes during restart. Use this
    to recover from stuck states or apply pending firmware updates.
    """
    config = Config.from_env()
    gate = check_write_gate(config)
    if gate:
        return gate
    conf = check_confirm_gate(confirm, "Dish reboot")
    if conf:
        return conf
    try:
        client = _get_client()
        await _run(client.reboot)
        return "Reboot command sent. Dish will restart — expect 2-5 minutes of downtime."
    except StarlinkError as e:
        return _error(e)


@mcp.tool()
async def starlink_stow(
    confirm: Annotated[bool, Field(description="Must be true to stow the dish")] = False,
) -> str:
    """Stow the dish (point face-down for storage or transport).

    Requires STARLINK_WRITE_ENABLED=true AND confirm=true. The dish will lose
    connectivity while stowed. Use starlink_unstow to resume.
    """
    config = Config.from_env()
    gate = check_write_gate(config)
    if gate:
        return gate
    conf = check_confirm_gate(confirm, "Dish stow")
    if conf:
        return conf
    try:
        client = _get_client()
        await _run(client.stow)
        return "Stow command sent. Dish will point face-down — connectivity will be lost."
    except StarlinkError as e:
        return _error(e)


@mcp.tool()
async def starlink_unstow(
    confirm: Annotated[bool, Field(description="Must be true to unstow the dish")] = False,
) -> str:
    """Unstow the dish (resume normal satellite tracking).

    Requires STARLINK_WRITE_ENABLED=true AND confirm=true.
    """
    config = Config.from_env()
    gate = check_write_gate(config)
    if gate:
        return gate
    conf = check_confirm_gate(confirm, "Dish unstow")
    if conf:
        return conf
    try:
        client = _get_client()
        await _run(client.unstow)
        return "Unstow command sent. Dish will resume normal operation."
    except StarlinkError as e:
        return _error(e)


# ===========================================================================
# Entrypoint
# ===========================================================================


def main() -> None:
    """Run the Starlink Blade MCP server."""
    if TRANSPORT == "http":
        mcp.run(transport="http", host=HTTP_HOST, port=HTTP_PORT)
    else:
        mcp.run(transport="stdio")
