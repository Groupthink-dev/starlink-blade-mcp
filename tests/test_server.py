"""Tests for MCP tool registration."""

from __future__ import annotations

from starlink_blade_mcp.server import mcp


class TestToolRegistration:
    @staticmethod
    async def _get_tool_names() -> list[str]:
        tools = await mcp.list_tools()
        return [t.name for t in tools]

    async def test_read_tools_registered(self) -> None:
        names = await self._get_tool_names()
        expected = [
            "starlink_status",
            "starlink_alerts",
            "starlink_obstruction",
            "starlink_history",
            "starlink_location",
            "starlink_diagnostics",
        ]
        for tool in expected:
            assert tool in names, f"Read tool '{tool}' not registered"

    async def test_write_tools_registered(self) -> None:
        names = await self._get_tool_names()
        expected = [
            "starlink_reboot",
            "starlink_stow",
            "starlink_unstow",
        ]
        for tool in expected:
            assert tool in names, f"Write tool '{tool}' not registered"

    async def test_total_tool_count(self) -> None:
        names = await self._get_tool_names()
        assert len(names) == 9
