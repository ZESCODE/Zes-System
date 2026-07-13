# Quick Reference

## Service Commands

```bash
sv restart dashboard8083       # Restart dashboard
sv restart hermes-gateway      # Restart Hermes
claude --version              # Check Claude Code
claude -p "task"               # Run Claude Code prompt
sv restart claude-proxy        # Restart Claude proxy
sv restart cmdop-agent         # Restart CMDOP agent
sv restart chromium-cdp        # Restart browser
sv restart sshd                # Restart SSH
sv restart tor                 # Restart Tor
```

## Ports Quick Reference

| Port | Service | URL |
|------|---------|-----|
| 5900 | Codex Server | http://localhost:5900 |
| 7173 | Web Terminal | http://localhost:7173 |
| 8022 | SSH Server | ssh -p 8022 localhost |
| 8083 | Dashboard | http://localhost:8083 |
| 8090 | Socat Bridge | — |
| 8787 | Hermes WebUI | http://localhost:8787 |
| 9050 | Tor SOCKS5 | socks5://127.0.0.1:9050 |
| 9222 | Browser CDP | http://localhost:9222 |
| 5905 | Claude Code Proxy | http://localhost:5905 |
| 20128 | 9Router | http://localhost:20128 |

## Key Files

| File | Purpose |
|------|---------|
| `~/.9router/` | 9router config, DB, auth tokens |
| `~/.9router/db/data.sqlite` | 9router provider DB |
| `~/.hermes/config.yaml` | Hermes AI configuration |
| `~/.hermes/.env` | Hermes API keys |
| `/usr/local/bin/claude` | Claude Code 2.1.207 binary (proot) |
| `~/.config/composio/env.sh` | Composio API key |
| `~/.config/composio/gmail.json` | Gmail connection details |
| `~/dashboard_v2.py` | Dashboard source code |
| `~/.local/bin/gmail-tool` | IMAP/SMTP Gmail client |
| `~/.local/bin/composio-gmail` | Composio Gmail CLI wrapper |
| `~/.local/bin/composio-setup` | Composio setup helper |
| `~/.local/bin/web-login-helper` | Browser automation helper |
| `~/.local/bin/composio-helper` | Composio CLI helper |
| `~/composio-test/` | @composio/client SDK workspace |

## 9Router API

```bash
# Get auth token
TOKEN=$(python3 -c "
import hashlib
mid = open('/data/data/com.termux/files/home/.9router/machine-id').read().strip()
sec = open('/data/data/com.termux/files/home/.9router/auth/cli-secret').read().strip()
print(hashlib.sha256((mid + '9r-cli-auth' + sec).encode()).hexdigest()[:16])
")

# List all providers
curl -H "x-9r-cli-token: $TOKEN" http://localhost:20128/api/providers | python3 -m json.tool

# List OpenAI-compatible nodes
curl -H "x-9r-cli-token: $TOKEN" http://localhost:20128/api/provider-nodes | python3 -m json.tool
```

## Proot Access

```bash
proot-distro login debian                              # Interactive shell
proot-distro login debian -- cmdop agent status        # CMDOP check
proot-distro login debian -- ps aux | grep cmdop       # Agent process
```

## System Health Check

```bash
# All services
sv status /data/data/com.termux/files/usr/var/service/*

# Port check
python3 -c "
import socket
for name,port in [('Codex',5900),('Hermes',8787),('9Router',20128),('Claude Code',5905),('Tor',9050)]:
    s=socket.socket(); s.settimeout(0.5)
    r=s.connect_ex(('127.0.0.1',port))
    print(f\"{'UP' if r==0 else 'DOWN'}: {name} :{port}\"); s.close()
"

# Gmail check
gmail-tool status
composio-gmail list 3
```


## Orchestrator Commands

```bash
# System start/stop
./start.sh              # Start all 25 services
./stop.sh               # Stop all services gracefully
./stop.sh --force       # Force stop all services

# ZES CLI
zes menu                # Interactive TUI menu
zes start               # Start all services
zes stop                # Stop all services
zes status              # Show all services + health
zes health              # Run test suite
zes mcp list            # List MCP tools
zes restart <svc>       # Restart a service
zes logs <svc> [lines]  # Tail service logs
zes backup              # Snapshot configs

# Claude Code delegation
claude-code-exec.sh "task" [model]           # Delegate to Claude Code
claude-session-reader.sh status              # Check Claude Code session
claude-session-reader.sh ask "question"      # Ask Claude Code

# Model switching
9router-switch-model.sh list                 # All models from 18 providers
9router-switch-model.sh providers            # Active providers
9router-switch-model.sh switch <model>       # Change Claude Code model
9router-switch-model.sh switch <model> --restart  # Change + restart Claude
9router-switch-model.sh smart <task-type>    # Best model for task

# Cron management
hermes-cron-manager.sh list                  # List cron jobs
hermes-cron-manager.sh create <name> <prompt> <schedule>  # Create job
hermes-cron-notify.sh status                 # Show cron status
hermes-cron-notify.sh failed                 # Show failed jobs only
hermes-cron-notify.sh telegram               # Send via Telegram
```

## Dashboard API

```bash
curl localhost:8083/api/status      # All services + MCP + providers
curl localhost:8083/api/cron        # Cron jobs with recent results
curl localhost:8083/api/cron/notify # Trigger notification broadcast
```
