"""gRPC client wrapper around starlink-grpc-core.

Provides a thin abstraction over the starlink_grpc module, managing channel
lifecycle and translating exceptions into StarlinkError.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from starlink_blade_mcp.models import Config

logger = logging.getLogger(__name__)


class StarlinkError(Exception):
    """Base error for Starlink gRPC operations."""


@dataclass
class DishStatus:
    """Parsed dish status from status_data()."""

    general: dict[str, Any] = field(default_factory=dict)
    status: dict[str, Any] = field(default_factory=dict)
    obstruction: dict[str, Any] = field(default_factory=dict)
    alerts: dict[str, bool] = field(default_factory=dict)


@dataclass
class DishHistory:
    """Parsed history from history_bulk_data()."""

    general: dict[str, Any] = field(default_factory=dict)
    bulk: dict[str, list[float | None]] = field(default_factory=dict)


class StarlinkClient:
    """Thread-safe wrapper around starlink-grpc-core."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._context: Any = None

    def _ensure_context(self) -> Any:
        """Lazy-create and return a ChannelContext."""
        if self._context is None:
            try:
                import starlink_grpc

                self._context = starlink_grpc.ChannelContext(target=self._config.dish_address)
            except Exception as exc:
                raise StarlinkError(f"Cannot connect to dish at {self._config.dish_address}: {exc}") from exc
        return self._context

    def close(self) -> None:
        """Close the gRPC channel."""
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

    def get_status(self) -> DishStatus:
        """Fetch current dish status."""
        import starlink_grpc

        ctx = self._ensure_context()
        try:
            general, status, obstruction, alerts = starlink_grpc.status_data(context=ctx)
            return DishStatus(
                general=general or {},
                status=status or {},
                obstruction=obstruction or {},
                alerts=alerts or {},
            )
        except starlink_grpc.GrpcError as exc:
            self._context = None
            raise StarlinkError(f"gRPC error fetching status: {exc}") from exc

    def get_location(self) -> dict[str, Any]:
        """Fetch GPS location (requires opt-in via Starlink app)."""
        import starlink_grpc

        ctx = self._ensure_context()
        try:
            return starlink_grpc.location_data(context=ctx) or {}
        except starlink_grpc.GrpcError as exc:
            self._context = None
            raise StarlinkError(f"gRPC error fetching location: {exc}") from exc

    def get_history(self, samples: int = 60) -> DishHistory:
        """Fetch recent history bulk data."""
        import starlink_grpc

        ctx = self._ensure_context()
        try:
            general, bulk = starlink_grpc.history_bulk_data(parse_samples=samples, verbose=True, context=ctx)
            return DishHistory(general=general or {}, bulk=bulk or {})
        except starlink_grpc.GrpcError as exc:
            self._context = None
            raise StarlinkError(f"gRPC error fetching history: {exc}") from exc

    def get_history_stats(self, samples: int = 900) -> dict[str, Any]:
        """Fetch computed statistics over recent history. Token-efficient alternative to raw history."""
        import starlink_grpc

        ctx = self._ensure_context()
        try:
            general, stats = starlink_grpc.history_stats(parse_samples=samples, verbose=True, context=ctx)
            return {"general": general or {}, "stats": stats or {}}
        except starlink_grpc.GrpcError as exc:
            self._context = None
            raise StarlinkError(f"gRPC error fetching history stats: {exc}") from exc

    def get_obstruction_map(self) -> dict[str, Any]:
        """Fetch obstruction map (SNR per direction)."""
        import starlink_grpc

        ctx = self._ensure_context()
        try:
            return starlink_grpc.get_obstruction_map(context=ctx) or {}
        except starlink_grpc.GrpcError as exc:
            self._context = None
            raise StarlinkError(f"gRPC error fetching obstruction map: {exc}") from exc

    def reboot(self) -> None:
        """Reboot the dish."""
        import starlink_grpc

        ctx = self._ensure_context()
        try:
            starlink_grpc.reboot(context=ctx)
        except starlink_grpc.GrpcError as exc:
            self._context = None
            raise StarlinkError(f"gRPC error rebooting dish: {exc}") from exc

    def stow(self) -> None:
        """Stow the dish (point face-down for storage/transport)."""
        import starlink_grpc

        ctx = self._ensure_context()
        try:
            starlink_grpc.set_stow_state(unstow=False, context=ctx)
        except starlink_grpc.GrpcError as exc:
            self._context = None
            raise StarlinkError(f"gRPC error stowing dish: {exc}") from exc

    def unstow(self) -> None:
        """Unstow the dish (resume normal operation)."""
        import starlink_grpc

        ctx = self._ensure_context()
        try:
            starlink_grpc.set_stow_state(unstow=True, context=ctx)
        except starlink_grpc.GrpcError as exc:
            self._context = None
            raise StarlinkError(f"gRPC error unstowing dish: {exc}") from exc
