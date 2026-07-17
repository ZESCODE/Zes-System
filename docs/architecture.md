# ZES System Architecture (v4.0)

*Generated: 2026-07-14T10:03:51.839206*

## Overview

- **27 services** across 3 repos
- **6 data flows** between services

## Services

| Service | Type | Language | Entry Point |
|---------|------|----------|-------------|
| 9router-proxy | runsv | unknown | N/A |
| agent-dash | runsv | unknown | N/A |
| agent-dash-web | service | javascript | server.js |
| agent-ui | service | html | index.html |
| chromium-cdp | runsv | unknown | N/A |
| claude-bridge-http | runsv | unknown | N/A |
| claude-bridge-ws | runsv | unknown | N/A |
| claude-dashboard | runsv | unknown | N/A |
| claude-proxy | runsv | unknown | N/A |
| claude-ui | runsv | unknown | N/A |
| claude-ui-backend | runsv | unknown | N/A |
| claude-ui-frontend | runsv | unknown | N/A |
| cloudflare-tunnel | runsv | unknown | N/A |
| dashboard8083 | runsv | unknown | N/A |
| hermes-gateway | runsv | unknown | N/A |
| hermes-webui | service | javascript | server.js |
| r9 | runsv | unknown | N/A |
| socat | runsv | unknown | N/A |
| tor | runsv | unknown | N/A |
| ttyd | runsv | unknown | N/A |
| vscode-mobile | service | javascript | server.js |
| vscode-server | runsv | unknown | N/A |
| zes-9router-tunnel | runsv | unknown | N/A |
| zes-affiliate | runsv | unknown | N/A |
| zes-downloader | runsv | unknown | N/A |
| zes-router-proxy | runsv | unknown | N/A |
| zeschrome-mcp | runsv | unknown | N/A |

## Data Flow

- **dashboard8083** → **r9** (http): API calls to 9Router for provider status
- **hermes-webui** → **r9** (http): Chat completion requests via 9Router
- **agent-ui** → **r9** (http): AI chat via 9Router
- **claude-proxy** → **r9** (http): Claude Code proxy to 9Router
- **claude-dashboard** → **r9** (http): Team dashboard data via 9Router
- **zes-router-proxy** → **r9** (http): Provider-specific proxy routing