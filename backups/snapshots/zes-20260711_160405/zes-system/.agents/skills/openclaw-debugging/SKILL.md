# ZES System Debugging

> Adapted from OpenClaw's debugging skill for ZES/9Router infrastructure.

## When to Use

Use when debugging ZES system services: 9Router, MCP server, Chrome CDP, 
Dashboard, Hermes Gateway, or any runsv-managed service.

## Debug Loop

1. **Check service status first**
   ```bash
   sv status /data/data/com.termux/files/usr/var/service/*
   ```
   
2. **Check logs**
   ```bash
   # MCP server logs
   cat /data/data/com.termux/files/home/.9router/services/zeschrome-mcp/log/current
   
   # Dashboard logs
   cat /data/data/com.termux/files/home/.9router/services/dashboard8083/log/current
   
   # 9Router provider check
   python3 ~/.codex/skills/9router-provider-check/SKILL.md  # uses skill
   ```

3. **Check 9Router connectivity**
   ```bash
   TOKEN=$(python3 -c "import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])")
   curl -H "x-9r-cli-token: $TOKEN" http://localhost:20128/api/providers
   curl http://localhost:20128/v1/models | head
   ```

4. **Check Chrome CDP**
   ```bash
   curl http://localhost:9222/json/version
   curl http://localhost:9222/json | python3 -m json.tool
   ```

5. **Check MCP server**
   ```bash
   curl http://localhost:5901/health
   curl -X POST http://localhost:5901/mcp -d '{"method":"mcp.ping","params":{}}'
   ```

## Common Issues

| Symptom | Check |
|---------|-------|
| "Upstream request failed" from 9Router | Provider token expired, re-auth needed |
| MCP server not responding (:5901) | `sv restart zeschrome-mcp` |
| Chrome CDP disconnected | `sv restart chromium-cdp` |
| Sidepanel shows no AI response | Check background.js service worker loaded |
| Gemini key prompt | gemini-proxy.js should intercept — check console for errors |
