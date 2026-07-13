#!/usr/bin/env node
/**
 * ZES Bridge MCP Server
 * Wraps ZES system APIs — dashboard, 9Router, services, Tor — as MCP tools.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { execSync } from "child_process";
import http from "http";

const server = new McpServer({
  name: "zes-bridge",
  version: "1.0.0",
});

// ─── Helpers ──────────────────────────────────────────────────────────────

function run(cmd, timeout = 10000) {
  try {
    return execSync(cmd, { encoding: "utf8", timeout, shell: true }).trim();
  } catch (e) {
    return `Error: ${e.stderr?.trim() || e.message}`;
  }
}

function httpGet(url, timeout = 5000, headers = {}) {
  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const opts = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: "GET",
      timeout: typeof timeout === "number" ? timeout : 5000,
      headers: headers || {},
    };
    const req = http.request(opts, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => resolve({ status: res.statusCode, data }));
    });
    req.on("error", (e) => resolve({ status: 0, error: e.message }));
    req.on("timeout", () => { req.destroy(); resolve({ status: 0, error: "timeout" }); });
    req.end();
  });
}

// ─── Tools ─────────────────────────────────────────────────────────────────

server.tool(
  "get_dashboard_status",
  "Fetch the ZES dashboard API status — all service health checks",
  {},
  async () => {
    const res = await httpGet("http://localhost:8083/api/status");
    if (res.status === 200) {
      return { content: [{ type: "text", text: res.data }] };
    }
    return { content: [{ type: "text", text: `Dashboard error: ${res.error || res.status}` }] };
  }
);

server.tool(
  "get_9router_providers",
  "List all 18 AI providers registered in 9Router with their auth status",
  {},
  async () => {
    try {
      const mid = run("cat $HOME/.9router/machine-id").trim();
      const sec = run("cat $HOME/.9router/auth/cli-secret").trim();
      const crypto = await import("crypto");
      const token = crypto.createHash("sha256").update(mid + "9r-cli-auth" + sec).digest("hex").slice(0, 16);
      const res = await httpGet("http://localhost:20128/api/providers", 5000, {
        "x-9r-cli-token": token
      });
      if (res.status === 200) {
        return { content: [{ type: "text", text: res.data }] };
      }
      return { content: [{ type: "text", text: `9Router error: ${res.error || res.status}` }] };
    } catch (e) {
      return { content: [{ type: "text", text: `9Router error: ${e.message}` }] };
    }
  }
);

server.tool(
  "check_service",
  "Check the status of a ZES runsv service by name",
  { name: z.string().describe("Service name (e.g. zeschrome-mcp, dashboard8083, hermes-gateway, tor)") },
  async ({ name }) => {
    const out = run(`sv status /data/data/com.termux/files/usr/var/service/${name} 2>/dev/null || echo "not found"`);
    return { content: [{ type: "text", text: out }] };
  }
);

server.tool(
  "list_services",
  "List all runsv services and their current status",
  {},
  async () => {
    const out = run("sv status /data/data/com.termux/files/usr/var/service/* 2>/dev/null");
    return { content: [{ type: "text", text: out }] };
  }
);

server.tool(
  "restart_service",
  "Restart a ZES runsv service by name",
  { name: z.string().describe("Service name") },
  async ({ name }) => {
    const out = run(`sv restart /data/data/com.termux/files/usr/var/service/${name} 2>/dev/null`);
    return { content: [{ type: "text", text: `Restarted ${name}: ${out}` }] };
  }
);

server.tool(
  "get_service_logs",
  "Get recent log output from a runsv service",
  { 
    name: z.string().describe("Service name"),
    lines: z.number().optional().default(20).describe("Number of log lines")
  },
  async ({ name, lines }) => {
    const logDir = `/data/data/com.termux/files/usr/var/service/${name}/log`;
    const out = run(`tail -${lines} ${logDir}/current 2>/dev/null || echo "No log found"`);
    return { content: [{ type: "text", text: out }] };
  }
);

server.tool(
  "rotate_tor_ip",
  "Request a new Tor exit node (SOCKS5 IP rotation)",
  {},
  async () => {
    const out = run('echo -e "AUTHENTICATE \\"\\"\\r\\nSIGNAL NEWNYM\\r\\nQUIT\\r\\n" | nc -w 2 127.0.0.1 9051 2>/dev/null || echo "Tor control port not reachable"');
    return { content: [{ type: "text", text: `Tor IP rotation requested: ${out}` }] };
  }
);

server.tool(
  "get_hermes_cron",
  "List all Hermes cron jobs with their schedules and scripts",
  {},
  async () => {
    const out = run("hermes cron list 2>/dev/null || echo 'hermes command not available'");
    return { content: [{ type: "text", text: out }] };
  }
);

server.tool(
  "run_health_evals",
  "Run the ZES system health evaluation script against all core services",
  {},
  async () => {
    const out = run("python3 ~/Zes-System/scripts/run-evals.py service-health 2>&1 || echo 'eval script not found'");
    return { content: [{ type: "text", text: out }] };
  }
);

server.tool(
  "get_claude_code_info",
  "Check Claude Code version and installation status",
  {},
  async () => {
    const out = run("claude --version 2>/dev/null || echo 'Claude Code CLI not in PATH'");
    return { content: [{ type: "text", text: `Claude Code: ${out}` }] };
  }
);

// ─── Start ─────────────────────────────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
