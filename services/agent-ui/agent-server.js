#!/usr/bin/env node
/**
 * ZES Agent Server v2 — ZES-aware chat with tool calling, memory, and system management
 * Replaces server.js. Adds: system knowledge, tool execution, persistent memory.
 */
import express from "express";
import { createServer } from "http";
import { readFileSync, existsSync, writeFileSync } from "fs";
import os from "os";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { execSync } from "child_process";
import { memory } from "./memory-store.js";
import { kanban } from "./kanban-store.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = 8084;
const app = express();
const server = createServer(app);

app.use(express.static(__dirname));
app.use(express.json({ limit: "10mb" }));

// ─── Load ZES Knowledge ──────────────────────────────────────────────
const KNOWLEDGE_FILE = join(__dirname, "zes-knowledge.json");
const ZES_KNOWLEDGE = JSON.parse(
  existsSync(KNOWLEDGE_FILE) ? readFileSync(KNOWLEDGE_FILE, "utf8") : "{}"
);

// ─── 9Router Config ──────────────────────────────────────────────────
const ROUTER_URL = "http://127.0.0.1:20128/v1/chat/completions";
const API_KEY = "sk-d25ec2e336a68df0-trhjvq-621c9b41";

// ─── Helper: run shell commands ──────────────────────────────────────
function run(cmd, timeout = 10000) {
  try {
    return execSync(cmd, { encoding: "utf8", timeout, shell: true }).trim();
  } catch (e) {
    return `Error: ${(e.stderr || e.message || "").trim().slice(0, 500)}`;
  }
}

// ─── Kanban Task Routes ────────────────────────────────────────────
app.get("/api/kanban/tasks", (req, res) => {
  res.json(kanban.getAll());
});

app.post("/api/kanban/tasks", (req, res) => {
  const { title, description, source, conversationId } = req.body || {};
  if (!title) return res.status(400).json({ error: "title required" });
  const task = kanban.addTask(title, description, source, conversationId);
  res.json(task);
});

app.post("/api/kanban/tasks/:id/move", (req, res) => {
  const { column } = req.body || {};
  if (!column) return res.status(400).json({ error: "column required" });
  const task = kanban.moveTask(req.params.id, column);
  task ? res.json(task) : res.status(404).json({ error: "Task not found" });
});

// ─── Kanban File Linking (Nimbalyst pattern) ───────────────────
app.get("/api/kanban/tasks/flat", (req, res) => {
  res.json(kanban.getAllFlat());
});

app.post("/api/kanban/tasks/:id/files", (req, res) => {
  const { files } = req.body || {};
  if (!files) return res.status(400).json({ error: "files required" });
  const task = kanban.linkFiles(req.params.id, files);
  task ? res.json(task) : res.status(404).json({ error: "Task not found" });
});

app.delete("/api/kanban/tasks/:id/files/:file", (req, res) => {
  const task = kanban.unlinkFile(req.params.id, decodeURIComponent(req.params.file));
  task ? res.json(task) : res.status(404).json({ error: "Task not found" });
});

app.delete("/api/kanban/tasks/:id", (req, res) => {
  const task = kanban.deleteTask(req.params.id);
  task ? res.json(task) : res.status(404).json({ error: "Task not found" });
});

app.get("/api/kanban/search", (req, res) => {
  const { q } = req.query;
  if (!q) return res.json(kanban.getAllFlat());
  res.json(kanban.search(q));
});

app.get("/api/kanban/stats", (req, res) => {
  res.json(kanban.getStats());
});

app.get("/api/kanban/files", (req, res) => {
  res.json(kanban.getAllFiles());
});

app.get("/api/kanban/files/:file", (req, res) => {
  const tasks = kanban.getTasksByFile(decodeURIComponent(req.params.file));
  res.json(tasks);
});

app.post("/api/kanban/tasks/:id/link", (req, res) => {
  const { conversationId } = req.body || {};
  const task = kanban.linkConversation(req.params.id, conversationId);
  task ? res.json(task) : res.status(404).json({ error: "Task not found" });
});

// ─── ZES System Tools ─────────────────────────────────────────────────
const ZES_TOOLS = {
  get_system_status: {
    description: "Get full ZES system status — all services, health, MCP, providers",
    execute: () => {
      try {
        const res = execSync(
          "curl -s http://127.0.0.1:8083/api/status 2>/dev/null || echo '{}'",
          { encoding: "utf8", timeout: 5000 }
        );
        const data = JSON.parse(res);
        const services = (data.services || []).map(s =>
          `${s.status === "running" ? "✅" : "❌"} ${s.name}${s.port ? ` (:${s.port})` : ""}`
        ).join("\n");
        return `## System Status\n\n**Services** (${data.services?.length || 0} total):\n${services}\n\n**MCP:** ${data.mcp?.length || 0} servers\n**Providers:** ${data.providers?.length || 0}`;
      } catch (e) {
        return `Status unavailable: ${e.message}`;
      }
    },
  },
  get_service_status: {
    description: "Check status of a specific service",
    params: { service: "Service name (e.g. dashboard8083, hermes-gateway, tor)" },
    execute: (args) => {
      const name = args?.service || "dashboard8083";
      const out = run(`sv status /data/data/com.termux/files/usr/var/service/${name} 2>/dev/null || echo "not found"`);
      return `Service "${name}": ${out}`;
    },
  },
  restart_service: {
    description: "Restart a ZES runsv service",
    params: { service: "Service name (e.g. dashboard8083, hermes-gateway, tor)" },
    execute: (args) => {
      const name = args?.service || "dashboard8083";
      const out = run(`sv restart /data/data/com.termux/files/usr/var/service/${name} 2>/dev/null`);
      return `Restart ${name}: ${out}`;
    },
  },
  get_service_logs: {
    description: "Get recent logs from a service",
    params: { service: "Service name", lines: "Number of lines (default 15)" },
    execute: (args) => {
      const name = args?.service || "dashboard8083";
      const lines = args?.lines || 15;
      const out = run(`tail -${lines} /data/data/com.termux/files/home/.svlog/${name}/current 2>/dev/null || echo "No log for ${name}"`);
      return `## Logs: ${name}\n\n${out}`;
    },
  },
  run_health_evals: {
    description: "Run 8 health evaluations against all core services",
    execute: () => {
      const out = run("python3 ~/Zes-System/scripts/run-evals.py 2>&1");
      return `## Health Evals\n\n${out}`;
    },
  },
  run_test_suite: {
    description: "Run the full 20-test regression suite",
    execute: () => {
      const out = run("python3 ~/Zes-System/scripts/run-tests.py 2>&1");
      return `## Test Suite\n\n${out.slice(-1000)}`;
    },
  },
  run_backup: {
    description: "Trigger a ZES system config backup snapshot",
    execute: () => {
      const out = run("bash ~/Zes-System/backups/scripts/zes-backup.sh snapshot 2>&1");
      return `## Backup\n\n${out.slice(-800)}`;
    },
  },
  rotate_tor_ip: {
    description: "Request a new Tor exit node (rotate SOCKS5 IP)",
    execute: () => {
      const out = run(`echo -e "AUTHENTICATE \\"\\"\\r\\nSIGNAL NEWNYM\\r\\nQUIT\\r\\n" | nc -w 2 127.0.0.1 9051 2>/dev/null || echo "Tor control unreachable"`);
      return `## Tor Rotation\n\n${out}`;
    },
  },
  get_providers: {
    description: "List all 9Router AI providers with status",
    execute: () => {
      const out = run(`
        TOKEN=\$(python3 -c "import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])")
        curl -s -H "x-9r-cli-token: \$TOKEN" http://localhost:20128/api/providers 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
conns=d.get('connections',[])
for c in conns:
    s=c.get('testStatus','?')
    name=c.get('name','?')
    auth=c.get('authType','?')
    icon='✅' if s=='active' else '❌'
    print(f'{icon} {name} [{auth}] → {s}')
" 2>/dev/null
      `, 10000);
      return `## 9Router Providers\n\n${out || "No provider data"}`;
    },
  },
  get_claude_info: {
    description: "Check Claude Code version and availability",
    execute: () => {
      const ver = run("claude --version 2>/dev/null");
      return `Claude Code: ${ver || "not available"}`;
    },
  },
  list_mcp_bridge_tools: {
    description: "List all tools available in the ZES Bridge MCP",
    execute: () => {
      const out = run(`echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | timeout 3 node ~/Zes-System/zes-chrome/zes-bridge-mcp/server.js 2>/dev/null`);
      try {
        const data = JSON.parse(out);
        const tools = data?.result?.tools || [];
        return `## ZES Bridge MCP Tools (${tools.length})\n\n${tools.map(t => `- **${t.name}**: ${(t.description || "").slice(0, 80)}`).join("\n")}`;
      } catch {
        return `Bridge MCP: ${out.slice(0, 200)}`;
      }
    },
  },
  security_scan: {
    description: "Run the ZES security hardening scan",
    execute: () => {
      const out = run("bash ~/Zes-System/scripts/security-scan.sh 2>&1");
      return `## Security Scan\n\n${out.slice(-1000)}`;
    },
  },
};

// ─── Slash Commands (ECC-inspired) ──────────────────────────────────
const SLASH_COMMANDS = {
  plan: {
    prompt: "Restate requirements, assess risks, and write a step-by-step implementation plan. Break the work into phases. Wait for user confirmation before touching any code.",
    description: "Create an implementation plan",
    icon: "📋"
  },
  tdd: {
    prompt: "Follow test-driven development: scaffold interface -> write failing test -> implement to pass -> verify 80%+ coverage.",
    description: "Test-driven development workflow",
    icon: "🧪"
  },
  "code-review": {
    prompt: "Perform a thorough code review. Check: code quality, security patterns, error handling, edge cases, performance, and maintainability.",
    description: "Review code for quality and security",
    icon: "🔍"
  },
  "build-fix": {
    prompt: "Detect and fix build/service errors. Check service status, read logs, identify root cause, provide fix.",
    description: "Fix build/service errors",
    icon: "🔧"
  },
  e2e: {
    prompt: "Run end-to-end integration tests across ZES services: dashboard :8083, agent UI :8084, Claude Code, 9Router :20128.",
    description: "Run integration tests",
    icon: "🌐"
  },
  verify: {
    prompt: "Run verification loop: service status check -> dashboard API check -> Claude Code test -> run evals -> run security scan.",
    description: "Full verification suite",
    icon: "✅"
  },
  "security-review": {
    prompt: "Run a security audit. Check for: hardcoded secrets, open ports, dependency vulnerabilities, config file permissions.",
    description: "Security audit",
    icon: "🛡️"
  },
  "quality-gate": {
    prompt: "Run all quality gates: tests passing, all services running, security hardening check, documentation completeness.",
    description: "Quality gate checklist",
    icon: "🏆"
  },
  help: {
    prompt: "",
    description: "Show all available commands",
    icon: "❓"
  }
};

function handleSlashCommand(message) {
  const match = message.toLowerCase().match(/^\/(\w+)/);
  if (!match) return null;
  const cmdName = match[1];
  const cmd = SLASH_COMMANDS[cmdName];
  if (!cmd) {
    const names = Object.keys(SLASH_COMMANDS).join(", ");
    return { handled: true, reply: "Unknown: /" + cmdName + ". Available: /" + names };
  }
  if (cmdName === "help") {
    const names = Object.keys(SLASH_COMMANDS)
      .map(function(k) { return "/" + k + " - " + SLASH_COMMANDS[k].description; })
      .join("\n");
    return { handled: true, reply: "Available slash commands:\n\n" + names };
  }
  return {
    handled: true,
    reply: cmd.prompt,
    command: cmdName,
    prompt: cmd.prompt
  };
}

// ─── Build System Prompt from knowledge ─────────────────────────────
function buildSystemPrompt(userMessage) {
  const k = ZES_KNOWLEDGE;
  const mem = memory.getMemorySummary();
  const serviceList = Object.entries(k.services || {})
    .map(([id, desc]) => `- **${id}**: ${desc}`).join("\n");
  const portList = Object.entries(k.port_map || {})
    .map(([port, name]) => `- :${port} — ${name}`).join("\n");
  const toolList = Object.entries(ZES_TOOLS)
    .map(([id, t]) => `- **${id}**${t.params ? ` (params: ${Object.keys(t.params).join(", ")})` : ""}: ${t.description}`)
    .join("\n");

  return `You are the ZES (Zettlr Execution System) AI Agent — a system management assistant.

## ZES System Knowledge

### Architecture
${k.architecture || "Codex/Claude Code → 9Router → AI Providers"}

### Services (${Object.keys(k.services || {}).length} tracked):
${serviceList}

### Port Map:
${portList}

### MCP Servers (${(k.mcp_servers || []).length}):
${(k.mcp_servers || []).map(m => `- ${m.name}: ${m.tools} tools (${m.type})`).join("\n")}

### Skills: ${k.skills?.count || 31} | Agents: ${k.agents?.count || 16}
### Test Suite: ${k.test_suite?.status || "20/20 passing"}
### Health Evals: ${k.health_evals?.status || "8/8 passing"}

## Tools Available
You can manage the system by using these tools. When the user asks you to do something, call the appropriate tool and report the result back.

${toolList}

## Memory (from previous sessions)
${mem || "No prior knowledge yet."}

## Guidelines
1. Answer questions about the ZES system using your knowledge base
2. When asked to manage the system (restart, backup, check, etc.), use the available tools
3. After completing a task, learn from it by storing important facts
4. Keep responses concise but informative
5. The dashboard is at http://localhost:8083/ — you can reference it
6. The ZES CLI is available via the 'zes' command

## Security & Guardrails (ECC-compatible)
- Never expose API keys, tokens, or credentials in responses
- Validate commands before execution — block anything with '--no-verify' or git hook bypass
- When making edits, prefer small, focused changes over large rewrites
- After shell execution, log the result summary to memory for audit trail
- Never modify .claude.json, agent-server.js, or dashboard_v4.py without user confirmation
- Track costs: prefer free-tier models when possible, log expensive model usage

## Current time: ${new Date().toISOString()}`;
}

// ─── Execute a tool ──────────────────────────────────────────────────
function executeTool(toolName, args) {
  const tool = ZES_TOOLS[toolName];
  if (!tool) return { success: false, output: `Unknown tool: ${toolName}` };
  try {
    const output = tool.execute(args || {});
    // Learn from tool execution
    memory.addFact(`Ran ${toolName}: ${output.slice(0, 100)}...`, "system_action");
    return { success: true, output };
  } catch (e) {
    return { success: false, output: `Error: ${e.message}` };
  }
}

// ─── Tool detection in user message ─────────────────────────────────
function detectToolIntent(message) {
  const msg = message.toLowerCase();
  const tools = {
    get_system_status: ["status", "what's running", "show services", "system health", "all services", "service status"],
    run_health_evals: ["health eval", "run eval", "check health"],
    run_test_suite: ["run test", "test suite", "run tests"],
    run_backup: ["backup", "snapshot", "save config"],
    rotate_tor_ip: ["rotate tor", "new ip", "change ip", "tor rotate"],
    restart_service: ["restart", "stop service", "start service"],
    get_service_logs: ["logs", "log for", "error log", "recent log"],
    get_providers: ["providers", "ai models", "9router", "available model"],
    get_claude_info: ["claude", "claude code"],
    list_mcp_bridge_tools: ["mcp tools", "bridge tools", "mcp list"],
    security_scan: ["security scan", "hardening", "vulnerability"],
  };

  for (const [toolName, triggers] of Object.entries(tools)) {
    if (triggers.some(t => msg.includes(t))) {
      // Extract service name for restart/logs
      let args = {};
      if (toolName === "restart_service" || toolName === "get_service_logs") {
        const svcMatch = message.match(/(?:restart|logs?\s+(?:for\s+)?)?(\w[\w-]+)/i);
        if (svcMatch) args.service = svcMatch[1];
      }
      return { toolName, args };
    }
  }
  return null;
}

// ─── API: Chat with ZES awareness + tool calling ────────────────────
app.post("/api/chat", async (req, res) => {
  try {
    const { model, messages } = req.body;
    const userMsg = messages?.[messages.length - 1]?.content || "";

    // Check for slash commands (/plan, /tdd, /code-review, etc)
    const slashResult = handleSlashCommand(userMsg);
    if (slashResult) {
      if (slashResult.command) {
        // Inject the command prompt template before the message
        const restOfMessage = userMsg.replace(/^\/\w+\s*/, "").trim();
        const commandMessage = slashResult.prompt + (restOfMessage ? "\n\nAdditional context: " + restOfMessage : "");
        messages[messages.length - 1].content = commandMessage;
      } else {
        // Help/unknown command - return immediately
        return res.json({
          id: "slash-response",
          object: "chat.completion",
          created: Math.floor(Date.now() / 1000),
          model: model || "zes-agent",
          choices: [{ index: 0, message: { role: "assistant", content: slashResult.reply }, finish_reason: "stop" }],
          usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
        });
      }
    }

    // Detect tool intent
    const toolIntent = detectToolIntent(userMsg);
    if (toolIntent) {
      // Execute tool and format response
      const result = executeTool(toolIntent.toolName, toolIntent.args);
      const toolInfo = ZES_TOOLS[toolIntent.toolName];
      
      // Store conversation
      memory.addConversation(`Used ${toolIntent.toolName}: ${result.output.slice(0, 100)}`, messages);

      return res.json({
        id: "tool-response",
        object: "chat.completion",
        created: Math.floor(Date.now() / 1000),
        model: model || "zes-agent",
        choices: [{
          index: 0,
          message: {
            role: "assistant",
            content: `${result.output}\n\n_Used tool: **${toolIntent.toolName}**_`,
          },
          finish_reason: "stop",
        }],
        usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
      });
    }

    // Build system prompt with knowledge + memory
    const systemPrompt = buildSystemPrompt(userMsg);
    const fullMessages = [
      { role: "system", content: systemPrompt },
      ...messages.filter(m => m.role !== "system"),
    ];

    // Send to 9Router
    const response = await fetch(ROUTER_URL, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: model || "gh/gpt-4o-mini",
        messages: fullMessages,
        max_tokens: 4096,
        stream: false,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }

    const data = await response.json();
    const text = typeof data === "string" ? data.split("data:")[0] : JSON.stringify(data);
    const parsed = JSON.parse(text);

    // Store conversation summary
    const reply = parsed?.choices?.[0]?.message?.content || "";
    memory.addConversation(`Q: ${userMsg.slice(0, 100)}... A: ${reply.slice(0, 100)}...`, messages);

    res.json(parsed);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
});

// ─── API: Streaming chat ─────────────────────────────────────────────
app.post("/api/chat/stream", async (req, res) => {
  try {
    const { model, messages } = req.body;
    const userMsg = messages?.[messages.length - 1]?.content || "";

    // Check tool intent first
    const toolIntent = detectToolIntent(userMsg);
    if (toolIntent) {
      const result = executeTool(toolIntent.toolName, toolIntent.args);
      memory.addConversation(`Used ${toolIntent.toolName}`, messages);
      const responseText = `${result.output}\n\n_Used tool: **${toolIntent.toolName}**_`;
      res.writeHead(200, {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
      });
      res.write(`data: {"choices":[{"delta":{"role":"assistant","content":${JSON.stringify(responseText)}}}]}\n\n`);
      res.write(`data: {"choices":[{"delta":{"content":""},"finish_reason":"stop"}]}\n\n`);
      return res.end();
    }

    const systemPrompt = buildSystemPrompt(userMsg);
    const fullMessages = [
      { role: "system", content: systemPrompt },
      ...messages.filter(m => m.role !== "system"),
    ];

    const response = await fetch(ROUTER_URL, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: model || "gh/gpt-4o-mini",
        messages: fullMessages,
        max_tokens: 4096,
        stream: true,
      }),
    });

    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    });

    let fullReply = "";
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      res.write(chunk);
      // Accumulate for memory
      const match = chunk.match(/"content":"([^"]+)"/);
      if (match) fullReply += match[1];
    }
    res.end();

    // Store conversation
    memory.addConversation(`Q: ${userMsg.slice(0, 100)}... A: ${fullReply.slice(0, 100)}...`, messages);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
});

// ─── API: List ZES tools ─────────────────────────────────────────────
app.get("/api/zes/tools", (req, res) => {
  res.json(Object.entries(ZES_TOOLS).map(([id, t]) => ({
    id,
    description: t.description,
    params: t.params || null,
  })));
});

// ─── API: Execute a ZES tool directly ────────────────────────────────
app.post("/api/zes/execute", (req, res) => {
  const { tool, args } = req.body;
  const result = executeTool(tool, args);
  res.json(result);
});

// ─── API: Get ZES system knowledge ───────────────────────────────────
app.get("/api/zes/knowledge", (req, res) => {
  const q = (req.query.q || "").toLowerCase();
  if (q) {
    const results = {};
    for (const [key, val] of Object.entries(ZES_KNOWLEDGE)) {
      if (JSON.stringify(val).toLowerCase().includes(q)) results[key] = val;
    }
    return res.json(results);
  }
  res.json(ZES_KNOWLEDGE);
});

// ─── API: Memory operations ──────────────────────────────────────────
app.get("/api/zes/memory", (req, res) => {
  const type = req.query.type || "all";
  if (type === "facts") return res.json(memory.data.facts);
  if (type === "conversations") return res.json(memory.data.conversations);
  if (type === "preferences") return res.json(memory.data.preferences);
  res.json(memory.data);
});

app.post("/api/zes/memory/fact", (req, res) => {
  const { fact, category } = req.body;
  if (fact) {
    memory.addFact(fact, category || "user_said");
    res.json({ success: true });
  } else {
    res.status(400).json({ error: "fact required" });
  }
});

app.delete("/api/zes/memory", (req, res) => {
  memory.clear();
  res.json({ success: true, message: "Memory cleared" });
});

app.get("/api/zes/memory/stats", (req, res) => {
  res.json(memory.getStats());
});

app.get("/api/zes/memory/forget/:type/:id", (req, res) => {
  const ok = memory.forget(req.params.type, req.params.id);
  res.json({ success: ok });
});

// ─── API: List slash commands ────────────────────────────────────────
app.get("/api/slash-commands", function(req, res) {
  var result = Object.keys(SLASH_COMMANDS).map(function(k) {
    return { command: k, description: SLASH_COMMANDS[k].description, icon: SLASH_COMMANDS[k].icon };
  });
  res.json(result);
});

// ─── API: System summary ─────────────────────────────────────────────
app.get("/api/zes/summary", (req, res) => {
  res.json({
    services: Object.keys(ZES_KNOWLEDGE.services || {}).length,
    mcp_servers: (ZES_KNOWLEDGE.mcp_servers || []).length,
    skills: ZES_KNOWLEDGE.skills?.count || 31,
    agents: ZES_KNOWLEDGE.agents?.count || 16,
    hooks: ZES_KNOWLEDGE.security_hooks?.count || 6,
    tools: Object.keys(ZES_TOOLS).length,
    memories: {
      ...memory.getStats(),
    },
    port: PORT,
  });
});

// ─── API: Models (unchanged from original) ───────────────────────────
app.get("/api/models", (req, res) => {
  res.json([
    { id: "gh/gpt-4o-mini", name: "Qwen 2.5 Coder 32B", provider: "Cloudflare", speed: "fast" },
    { id: "cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast", name: "Llama 3.3 70B", provider: "Cloudflare", speed: "fast" },
    { id: "cf/@cf/meta/llama-3.2-3b-instruct", name: "Llama 3.2 3B", provider: "Cloudflare", speed: "instant" },
    { id: "cf/@cf/qwen/qwq-32b", name: "QwQ 32B (Reasoning)", provider: "Cloudflare", speed: "medium" },
    { id: "cf/@cf/deepseek-ai/deepseek-r1-distill-qwen-32b", name: "DeepSeek R1 32B", provider: "Cloudflare", speed: "medium" },
    { id: "ds/deepseek-v4-flash", name: "DeepSeek V4 Flash", provider: "9Router", speed: "fast" },
    { id: "ds/deepseek-v4-pro", name: "DeepSeek V4 Pro", provider: "9Router", speed: "medium" },
    { id: "cl/anthropic/claude-sonnet-4.6", name: "Claude Sonnet 4.6", provider: "9Router", speed: "medium" },
    { id: "oz/big-pickle", name: "Zen OpenCode", provider: "9Router", speed: "medium" },
    { id: "gh/gpt-4o-mini-2024-07-18", name: "GPT-4o Mini", provider: "Copilot", speed: "fast" },
  ]);
});

// ─── Website (kept from original) ────────────────────────────────────
app.get("/health", (req, res) => {
  res.json({ status: "ok", port: PORT, agent: "zes-v2", tools: Object.keys(ZES_TOOLS).length });
});


// ─── Agent Orchestrator ──────────────────────────────────────────────
// Codebuff-style subagent dispatch with agent chaining and TypeScript definitions

const AGENTS_DIR = join(os.homedir(), ".zes", "agents");

function loadAgentDef(id) {
  const file = join(AGENTS_DIR, `${id}.json`);
  try { return JSON.parse(readFileSync(file, "utf8")); } catch { return null; }
}

function listAgents() {
  const agents = [];
  try {
    const files = execSync(`ls ${AGENTS_DIR}/*.json 2>/dev/null || true`, { encoding: "utf8", shell: true }).trim().split("\n").filter(Boolean);
    for (const f of files) {
      try { agents.push(JSON.parse(readFileSync(f, "utf8"))); } catch {}
    }
  } catch {}
  return agents;
}

// Track active agent chains: sessionId -> { chain: agentId[], context: string }
const activeChains = new Map();

// GET /api/agents — list all defined agents
app.get("/api/agents", (req, res) => {
  res.json({ agents: listAgents() });
});

// GET /api/agents/:id — get specific agent definition
app.get("/api/agents/:id", (req, res) => {
  const agent = loadAgentDef(req.params.id);
  if (!agent) return res.status(404).json({ error: "Agent not found" });
  res.json(agent);
});

// POST /api/orchestrator/run — run an agent with a prompt
app.post("/api/orchestrator/run", async (req, res) => {
  const { agent: agentId, prompt, context, sessionId, chain } = req.body || {};
  const agentDef = loadAgentDef(agentId || "help");
  if (!agentDef) return res.status(404).json({ error: `Agent '${agentId}' not found` });

  // Build system prompt
  let systemPrompt = agentDef.systemPrompt;
  if (context) systemPrompt += `\n\n## Context\n${context}`;

  // If chaining, tell the agent about the chain
  if (chain && chain.length > 1) {
    const chainIdx = chain.indexOf(agentId);
    const prevAgents = chain.slice(0, chainIdx);
    const nextAgents = chain.slice(chainIdx + 1);
    if (prevAgents.length) systemPrompt += `\n\n## Previous Steps\nCompleted by: ${prevAgents.join(" -> ")}\nBuild on that work.`;
    if (nextAgents.length) systemPrompt += `\n\n## Next Steps\nWill be handled by: ${nextAgents.join(" -> ")}\nPrepare your output for the next agent in the chain.`;
  }

  // Track chain state
  if (sessionId) {
    if (!activeChains.has(sessionId)) activeChains.set(sessionId, { chain: [], context: "" });
    const state = activeChains.get(sessionId);
    if (chain && Array.isArray(chain)) state.chain = chain;
    if (!state.chain.includes(agentId)) state.chain.push(agentId);
  }

  // Call 9Router
  try {
    const body = {
      model: agentDef.model || "gh/gpt-4o",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: prompt || "Execute your role." }
      ],
      stream: true,
      max_tokens: 8192,
      temperature: agentDef.temperature || 0.3
    };

    const resp = await fetch(ROUTER_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer sk-d25ec2e336a68df0-trhjvq-621c9b41" },
      body: JSON.stringify(body)
    });

    if (!resp.ok) {
      const errText = await resp.text().catch(() => "");
      return res.status(resp.status).json({ error: `9Router error: ${resp.status}`, detail: errText.slice(0, 500) });
    }

    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let fullContent = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim();
          if (data === "[DONE]") { res.write("data: [DONE]\n\n"); continue; }
          try {
            const parsed = JSON.parse(data);
            const content = parsed.choices?.[0]?.delta?.content || "";
            if (content) {
              fullContent += content;
              res.write(`data: ${JSON.stringify({ content })}\n\n`);
            }
          } catch {}
        }
      }
    }

    // Update chain context with result
    if (sessionId && fullContent) {
      const state = activeChains.get(sessionId);
      if (state) state.context = fullContent.slice(0, 2000);
    }

    // Send chain info
    if (chain && Array.isArray(chain)) {
      const currentIdx = chain.indexOf(agentId);
      if (currentIdx >= 0 && currentIdx < chain.length - 1) {
        res.write(`data: ${JSON.stringify({ chainNext: chain[currentIdx + 1] })}\n\n`);
      }
    }

    res.write("data: [DONE]\n\n");
    res.end();
  } catch (e) {
    res.write(`data: ${JSON.stringify({ error: e.message })}\n\n`);
    res.write("data: [DONE]\n\n");
    res.end();
  }
});

// POST /api/orchestrator/dispatch — parse prompt and dispatch to right agent
app.post("/api/orchestrator/dispatch", async (req, res) => {
  const { prompt, sessionId } = req.body || {};
  if (!prompt) return res.status(400).json({ error: "prompt required" });

  const agents = listAgents();
  let targetAgent = "help";
  let actualPrompt = prompt;

  // Check for @agent mentions
  for (const a of agents) {
    const mention = `@${a.id}`; const mentionEscaped = mention.replace(/-/g, "\\-");
    if (prompt.includes(mention)) {
      targetAgent = a.id;
      actualPrompt = prompt.replace(new RegExp(mentionEscaped, "g"), "").trim();
      break;
    }
  }

  // Check for /cmd patterns
  const cmdMatch = prompt.match(/^\/([\w-]+)/);
  if (cmdMatch) {
    const cmdAgent = agents.find(a => a.id === cmdMatch[1]);
    if (cmdAgent) {
      targetAgent = cmdAgent.id;
      actualPrompt = prompt.slice(cmdMatch[0].length).trim();
    }
  }

  res.json({ agent: targetAgent, prompt: actualPrompt, sessionId });
});

// ─── SPA fallback ────────────────────────────────────────────────────
app.get("*", (req, res) => {
  res.sendFile(join(__dirname, "index.html"));
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`\n  🤖 ZES Agent UI v2 — ZES-Aware System Manager`);
  console.log(`  ─────────────────────────────────────────`);
  console.log(`  URL:      http://0.0.0.0:${PORT}`);
  console.log(`  AI via:   9Router → ${ROUTER_URL}`);
  console.log(`  Tools:    ${Object.keys(ZES_TOOLS).length} ZES management tools`);
  console.log(`  Memory:   ${memory.data.facts.length} facts, ${memory.data.conversations.length} conversations\n`);
});
