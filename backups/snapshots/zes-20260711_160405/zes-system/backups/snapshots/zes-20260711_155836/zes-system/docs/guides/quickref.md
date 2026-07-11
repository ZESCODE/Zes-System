# Quick Reference

## Service Commands

```bash
sv restart dashboard8083       # Restart dashboard
sv restart hermes-gateway      # Restart Hermes
sv restart opencode            # Restart OpenCode
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
| 9876 | OpenCode Server | http://localhost:9876 |
| 20128 | 9Router | http://localhost:20128 |

## Key Files

| File | Purpose |
|------|---------|
| `~/.9router/` | 9router config, DB, auth tokens |
| `~/.9router/db/data.sqlite` | 9router provider DB |
| `~/.hermes/config.yaml` | Hermes AI configuration |
| `~/.hermes/.env` | Hermes API keys |
| `~/.config/opencode/opencode.json` | OpenCode configuration |
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
for name,port in [('Codex',5900),('Hermes',8787),('9Router',20128),('OpenCode',9876),('Tor',9050)]:
    s=socket.socket(); s.settimeout(0.5)
    r=s.connect_ex(('127.0.0.1',port))
    print(f\"{'UP' if r==0 else 'DOWN'}: {name} :{port}\"); s.close()
"

# Gmail check
gmail-tool status
composio-gmail list 3
```
