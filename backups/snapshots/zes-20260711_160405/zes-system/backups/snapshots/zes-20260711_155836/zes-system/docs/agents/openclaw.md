# OpenClaw SDK — Agent Orchestration Plugin

**Version:** 2026.3.20 | **Status:** Installed (limited Android support)

## Overview

OpenClaw is an open-source agent orchestration plugin that wraps the CMDOP Python SDK. It provides fleet management, machine scheduling, tunnel creation, and skill deployment across a CMDOP-connected fleet.

## Current State

| Component | Status | Notes |
|-----------|--------|-------|
| Python SDK | ✅ Installed | `openclaw` v2026.3.20 at site-packages |
| Import | ✅ Fixed | Patched `CMDOPClient` → `Client` for current cmdop SDK |
| Go binary | ⚠️ Missing | `cmdop-core` has no Android/aarch64 prebuilt binary |
| CMDOP Agent | ✅ Running | Inside proot at `/usr/local/bin/cmdop`, v1.1.106 |
| 9Router Node | ✅ Configured | `oc` prefix → `http://127.0.0.1:4040/v1` (via Tor) |

## Architecture

```
Python (your code)
  └─ openclaw.OpenClaw (extends cmdop.Client)
       └─ cmdop-core (Go binary — wraps CMDOP agent)
            └─ CMDOP relay (zes.cmdop.dev)
                 └─ Fleet machines
```

The Python SDK requires a `cmdop-core` Go binary to communicate with the CMDOP relay. This binary is not available for Android/aarch64. However, the CMDOP agent runs inside the Debian proot container where it has full glibc support.

## Usage (inside proot)

```bash
# Check agent status
proot-distro login debian -- cmdop agent status

# List fleet machines
proot-distro login debian -- cmdop machines

# Health check
proot-distro login debian -- cmdop doctor
```

## 9Router Integration

A node `oc` is configured in 9router for OpenClaw proxy:
- **Prefix:** `oc`
- **Endpoint:** `http://127.0.0.1:4040/v1`
- **Proxy:** Tor SOCKS5
- **Used by:** Hermes agent for routing through OpenClaw

To start the proxy server, run inside proot:
```bash
proot-distro login debian -- cmdop proxy --port 4040
```

## API Reference

```python
from openclaw import OpenClaw

# Initialize (if cmdop-core is available)
client = OpenClaw(
    token="your-token",
    base_url="https://zes.cmdop.dev"
)

# Fleet management
fleets = client.fleets.list()
machines = client.machines.list()

# Schedules
schedules = client.schedules.list()

# Tunnels
tunnels = client.tunnels.list()
```

## Limitations on Android

The `cmdop-core` Go binary has no prebuilt release for `android/aarch64`. To use the Python SDK natively on Android:
1. Cross-compile `cmdop-core` for Android: `GOOS=android GOARCH=arm64 go build -o cmdop-core ./cmd/cmdop-core`
2. Set `CMDOP_CORE_BINARY=/path/to/cmdop-core`
3. Or use the CMDOP agent inside proot for all orchestration commands
