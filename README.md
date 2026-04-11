# starlink-blade-mcp

Local-first Starlink dish monitoring and control via the [Model Context Protocol](https://modelcontextprotocol.io).

Talks directly to your dish over the local gRPC interface (`192.168.100.1:9200`) — no cloud API, no enterprise credentials, no internet dependency. Built on [`starlink-grpc-core`](https://pypi.org/project/starlink-grpc-core/), the same library that powers the Home Assistant Starlink integration.

## Why this MCP?

| | starlink-blade-mcp | [starlink-enterprise-mcp](https://github.com/ry-ops/starlink-enterprise-mcp-server) | [mcp-spacex](https://github.com/pipeworx-io/mcp-spacex) |
|---|---|---|---|
| **Interface** | Local gRPC (dish hardware) | Enterprise cloud API | Public SpaceX API |
| **Auth required** | None (LAN access only) | OAuth2 enterprise credentials | None |
| **Works offline** | Yes | No | No |
| **Residential dish** | Yes | Enterprise fleet only | N/A (satellite tracking) |
| **Dish control** | Reboot, stow, unstow | Read-only telemetry | None |
| **Obstruction map** | 12-wedge directional data | Aggregate only | None |
| **Alert detail** | 22 flags with descriptions | Basic status | None |
| **Token efficiency** | Statistical summaries | Raw JSON | Raw JSON |

## Tools

### Read (no authentication required)

| Tool | Description |
|------|-------------|
| `starlink_status` | Dish identity, state, connectivity, throughput, SNR, orientation |
| `starlink_alerts` | Active alert flags (22 types) with human-readable descriptions |
| `starlink_obstruction` | Obstruction fraction, 12-wedge directional map, timing |
| `starlink_history` | Throughput/latency/power as min/avg/max summary (configurable window) |
| `starlink_location` | GPS coordinates (requires opt-in in Starlink app) |
| `starlink_diagnostics` | Hardware version, firmware, GPS satellites, alert count |

### Write (gated)

| Tool | Description |
|------|-------------|
| `starlink_reboot` | Restart the dish (2-5 min downtime) |
| `starlink_stow` | Stow dish face-down for storage/transport |
| `starlink_unstow` | Resume normal satellite tracking |

Write operations require **dual gating**:
1. `STARLINK_WRITE_ENABLED=true` environment variable
2. `confirm=true` parameter on each call

## Quick Start

```bash
# Install
uv pip install starlink-blade-mcp

# Run (dish must be reachable at 192.168.100.1)
starlink-blade-mcp

# Or with uv
uvx starlink-blade-mcp
```

### Claude Code

```json
{
  "mcpServers": {
    "starlink": {
      "command": "uvx",
      "args": ["starlink-blade-mcp"],
      "env": {
        "STARLINK_WRITE_ENABLED": "false"
      }
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "starlink": {
      "command": "uvx",
      "args": ["starlink-blade-mcp"],
      "env": {
        "STARLINK_DISH_ADDRESS": "192.168.100.1:9200",
        "STARLINK_WRITE_ENABLED": "false"
      }
    }
  }
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `STARLINK_DISH_ADDRESS` | `192.168.100.1:9200` | Dish gRPC endpoint |
| `STARLINK_TIMEOUT` | `10` | gRPC timeout in seconds |
| `STARLINK_WRITE_ENABLED` | `false` | Enable reboot/stow/unstow |
| `STARLINK_MCP_TRANSPORT` | `stdio` | `stdio` or `http` |
| `STARLINK_MCP_HOST` | `127.0.0.1` | HTTP transport bind address |
| `STARLINK_MCP_PORT` | `8770` | HTTP transport port |

## Network Requirements

The Starlink dish exposes an **unauthenticated** gRPC server at `192.168.100.1:9200` on the local network. Requirements:

- Device running the MCP must be on the Starlink LAN (or have a route to `192.168.100.1`)
- No credentials or API keys needed
- GPS location requires opt-in: Starlink app > Settings > Advanced > Debug Data
- The dish's 192.168.100.1 address is not configurable

If you're behind a third-party router, ensure the WAN interface is connected to the Starlink Ethernet Adapter and that routing to `192.168.100.1/32` is configured.

## Security Model

- **No credentials stored or transmitted** — the dish gRPC endpoint is unauthenticated by design
- **LAN-only access** — the gRPC interface is not exposed to the internet
- **Write operations double-gated** — environment variable + per-call confirmation
- **No telemetry or phone-home** — all data stays local between the MCP server and the dish
- **No cloud API dependency** — works during internet outages (ideal for monitoring them)

## Token Efficiency

The `starlink_history` tool returns statistical summaries (min/avg/max per metric) rather than raw per-second samples. A 900-second window produces ~8 lines of output vs ~5,400 lines of raw data.

```
History Summary (last 60 samples, 1s intervals)

metric          min      avg      max   unit
--------------------------------------------
ping_drop     0.0000   0.0021   0.0150
latency         22.1     34.5     89.2     ms
down             0.5     45.2    120.3   Mbps
up               0.1      8.4     25.1   Mbps
power           48.2     52.1     58.9      W
snr              7.8      9.2     10.1     dB
```

## Development

```bash
git clone https://github.com/groupthink-dev/starlink-blade-mcp
cd starlink-blade-mcp

# Install with dev dependencies
make install-dev

# Run quality checks
make check

# Run tests (mocked — no dish required)
make test

# Run e2e tests (requires live dish on LAN)
make test-e2e

# Run with coverage
make test-cov
```

## Sidereal Marketplace

This MCP is available as a certified plugin in the [Sidereal Marketplace](https://sidereal.cc/marketplace). Install directly from Settings > MCPs in the Sidereal app.

The plugin manifest provides:
- Credential-free setup (auto-discovers dish on LAN)
- Write operation toggle in Settings UI
- Connection test validation
- Custom dish address for non-standard networks

## Roadmap

- [ ] Power save / sleep schedule control (read + set via `dish_power_save` proto)
- [ ] Hardware self-test results (extended diagnostics from proto)
- [ ] Webhook triggers for alert state changes (Sidereal event dispatch)
- [ ] Firmware update tracking and notification
- [ ] Multi-dish support (mesh network with multiple terminals)
- [ ] Obstruction map visualization (SVG/image generation)

## License

MIT
