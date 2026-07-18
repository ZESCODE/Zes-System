---
category: Development

name: zes-mcp-patterns
description: Build and extend MCP servers for ZES — tools, resources, Zod validation, stdio/HTTP transport. Use when working with zeschrome-mcp or adding new MCP capabilities.
---


# ZES MCP Server Patterns

Use when building MCP servers for ZES, extending `zeschrome-mcp`, or adding new tools to the existing ZES MCP layer.

## ZES MCP Context

ZES runs `zeschrome-mcp` on port 5901 — a Chrome DevTools Protocol bridge via CDP. This skill covers adding new tools/resources to that server, or building new standalone MCP servers for ZES services.

## Architecture

```
Claude Code / Codex
    ↕ MCP protocol (stdio)
zeschrome-mcp (:5901)
    ↕ CDP
Headless Chromium (:9222)
    ↕
Chrome DevTools Protocol
```

## When to Use

- Adding a new MCP tool to `zeschrome-mcp`
- Building a new MCP server for a ZES service (9Router, Hermes, Dashboard)
- Debugging MCP tool registration or transport issues
- Choosing between stdio vs HTTP transport for a ZES MCP server

## Core Concepts

- **Tools**: Actions the model can invoke (e.g. `browser_navigate`, `take_screenshot`)
- **Resources**: Read-only data (e.g. service status, logs)
- **Transport**: stdio (local) or HTTP (remote)
- **Validation**: Zod schemas for all tool inputs

## ZES MCP Tool Template

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({
  name: "zes-mcp",
  version: "1.0.0"
});

// Tool example: check ZES service health
server.tool(
  "check_service",
  { service: z.string().describe("Service name (e.g. r9, hermes, codex)") },
  async ({ service }) => {
    const { execSync } = await import("child_process");
    try {
      const out = execSync(`sv status /data/data/com.termux/files/usr/var/service/${service} 2>&1`).toString();
      return { content: [{ type: "text", text: out.trim() }] };
    } catch (e) {
      return { content: [{ type: "text", text: `Service ${service} not found` }], isError: true };
    }
  }
);
```

## ZES MCP Tools Worth Building

| Tool | Description | Implementation |
|------|-------------|----------------|
| `check_service` | Check runsv service status | Runs `sv status` |
| `list_services` | List all ZES services | Reads from dashboard API |
| `get_9router_providers` | List 9Router provider status | Calls 9Router API |
| `get_logs` | Get service logs | Reads from log directories |
| `restart_service` | Restart a runsv service | Runs `sv restart` |
| `rotate_ip` | Rotate Tor exit IP | Sends SIGNAL NEWNYM |

## Transport

For local ZES use, stdio transport is sufficient:

```typescript
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
const transport = new StdioServerTransport();
await server.connect(transport);
```

For remote ZES access (Cloudflare Tunnel), use Streamable HTTP.

## Best Practices

- **Schema first**: Define Zod schemas for every tool
- **Error handling**: Return structured errors, not raw stack traces
- **Idempotency**: Design tools to be safe for retries
- **Versioning**: Pin SDK version in package.json
- **Test**: Verify tools work with both Claude Code and Codex

## Resources

- [MCP Specification](https://modelcontextprotocol.io)
- `@modelcontextprotocol/sdk` on npm
- ZES: `zeschrome-mcp` at `/data/data/com.termux/files/home/Zes-System/zes-chrome/mcp-server/`
