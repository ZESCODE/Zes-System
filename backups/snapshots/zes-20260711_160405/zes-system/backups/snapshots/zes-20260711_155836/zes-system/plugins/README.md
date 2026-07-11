# ZES Plugins

Plugin integration with the ZES System.

## Available Plugins

| Plugin | Source | Purpose |
|--------|--------|---------|
| **openclaw-config** | `arfaXdev/Termux-Claw` | OpenClaw agent orchestration config |
| **codex-skills** | Built-in | Superpowers, service management, android access |
| **zes-chrome** | Built-in | Chrome extension + MCP server |
| **hermes-cron** | Built-in | Cron job templates for Hermes gateway |

## Integration

The OpenClaw config from `arfaXdev/Termux-Claw` has been adapted for 9Router.
See `services/openclaw.json` for the 9Router-native configuration.

## Adding a Plugin

```bash
# Copy the openclaw config
cp ~/Zes-System/services/openclaw.json ~/.openclaw/

# Start the swarm orchestrator
python3 ~/Zes-System/services/zes_swarm.py --port 5030
```
