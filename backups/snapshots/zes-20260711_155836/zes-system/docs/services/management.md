# Service Management

## Overview

All services run under **runit** supervision via `runsv`. The service directory is at `/data/data/com.termux/files/usr/var/service/`.

## Service Commands

```bash
# Status
sv status dashboard8083
sv status /data/data/com.termux/files/usr/var/service/*

# Control
sv restart dashboard8083    # Restart
sv start dashboard8083      # Start
sv stop dashboard8083       # Stop
```

## Individual Services

### Dashboard (port 8083)
- **Source:** `~/dashboard_v2.py`
- **Restart:** `sv restart dashboard8083`
- **Features:** Mobile-responsive, drawer nav, sparkline history, provider table, auto-refresh

### 9Router (port 20128)
- **Binary:** `/data/data/com.termux/files/usr/bin/9router`
- **Start:** `9router -p 20128 --no-browser -l`
- **Config:** `~/.9router/`
- **DB:** `~/.9router/db/data.sqlite`
- **No runsv service** — started manually

### Hermes Gateway (port 8787)
- **Config:** `~/.hermes/config.yaml`
- **Cron jobs:**
  - `daily-health-check` — Every 6 hours
  - `log-cleanup` — Every 24 hours (no-agent script)
- **Commands:**
  ```bash
  hermes cron list           # List scheduled jobs
  hermes gateway run         # Start gateway
  ```

### OpenCode Server (port 9876)
- **Runs inside proot** via `lildax`
- **Config:** `~/.config/opencode/opencode.json`
- **Model:** `9router/cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- **Wrapper:** `/data/data/com.termux/files/usr/bin/opencode`

### CMDOP Agent
- **Enrolled at:** `zes.cmdop.dev`
- **Status check inside proot:**
  ```bash
  proot-distro login debian -- cmdop agent status
  ```
- **Config (proot):** `/root/.config/cmdop/config.yaml`

### Tor SOCKS5 (port 9050)
- Provides anonymizing proxy for 9router
- Proxy pool: `socks5://127.0.0.1:9050`

### Headless Chromium (port 9222)
- **Runs inside proot**
- Used for browser automation and web auth
- **CDP endpoint:** `http://127.0.0.1:9222`

## Proot Access

```bash
# Login to Debian proot container
proot-distro login debian

# Run single command inside proot
proot-distro login debian -- <command>
```
