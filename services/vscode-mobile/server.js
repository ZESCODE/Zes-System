#!/usr/bin/env node
/**
 * ZES Remote Agent Control — Port 8001
 * Chat interface to remotely control Cline/Continue agents in VS Code.
 * Features: AI chat via 9Router, VS Code bridge, pairing code, system tools.
 */
import express from "express";
import { createServer } from "http";
import { readFileSync, existsSync, writeFileSync } from "fs";
import { randomBytes } from "crypto";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { execSync, spawn } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = 8001;
const app = express();
const server = createServer(app);

app.use(express.static(__dirname));
app.use(express.json({ limit: "10mb" }));

// ─── Configuration ──────────────────────────────────────────────────
const ROUTER_URL = "http://127.0.0.1:20128/v1/chat/completions";
const API_KEY = "sk-d25ec2e336a68df0-trhjvq-621c9b41";
const VSCODE_URL = "http://127.0.0.1:8000";
const PAIRING_FILE = join(__dirname, ".pairing-code.json");

// ─── Pairing Code System ───────────────────────────────────────────
function generatePairingCode() {
  const code = randomBytes(4).toString("hex").toUpperCase();
  const expiresAt = Date.now() + 300000; // 5 min expiry
  const pairData = { code, expiresAt, createdAt: Date.now() };
  writeFileSync(PAIRING_FILE, JSON.stringify(pairData, null, 2));
  return pairData;
}

function getPairingCode() {
  try {
    if (existsSync(PAIRING_FILE)) {
      const data = JSON.parse(readFileSync(PAIRING_FILE, "utf8"));
      if (data.expiresAt > Date.now()) return data;
    }
  } catch {}
  return generatePairingCode();
}

function verifyPairingCode(code) {
  try {
    if (existsSync(PAIRING_FILE)) {
      const data = JSON.parse(readFileSync(PAIRING_FILE, "utf8"));
      if (data.code === code && data.expiresAt > Date.now()) return true;
    }
  } catch {}
  return false;
}

// ─── Helper: run shell commands ──────────────────────────────────────
function run(cmd, timeout = 15000) {
  try {
    return execSync(cmd, { encoding: "utf8", timeout, shell: true }).trim();
  } catch (e) {
    return `Error: ${(e.stderr || e.message || "").trim().slice(0, 500)}`;
  }
}

// ─── AI Chat via 9Router ──────────────────────────────────────────
app.post("/api/chat", async (req, res) => {
  const { messages, model } = req.body || {};
  if (!messages || !Array.isArray(messages)) {
    return res.status(400).json({ error: "messages array required" });
  }
  const modelId = model || "gh/gpt-4o-mini";
  const body = {
    model: modelId,
    messages: [
      { role: "system", content: "You are ZES Remote Agent Controller. You help users manage AI coding agents (Cline, Continue) in VS Code Server on Android/Termux. You can run commands, read/write files, and control agents." },
      ...messages
    ],
    stream: true,
    max_tokens: 8192
  };
  try {
    const resp = await fetch(ROUTER_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${API_KEY}` },
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
            if (content) res.write(`data: ${JSON.stringify({ content })}\n\n`);
          } catch {}
        }
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

// ─── Non-streaming chat for tools ──────────────────────────────────
app.post("/api/chat/direct", async (req, res) => {
  const { messages, model } = req.body || {};
  if (!messages?.length) return res.status(400).json({ error: "messages required" });
  try {
    const resp = await fetch(ROUTER_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${API_KEY}` },
      body: JSON.stringify({ model: model || "gh/gpt-4o-mini", messages, stream: false, max_tokens: 4096 })
    });
    const data = await resp.json();
    res.json({ content: data.choices?.[0]?.message?.content || "", model: data.model });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ─── Pairing Code API ───────────────────────────────────────────────
app.get("/api/pairing/code", (req, res) => {
  res.json(getPairingCode());
});

app.post("/api/pairing/verify", (req, res) => {
  const { code } = req.body || {};
  if (!code) return res.status(400).json({ error: "code required" });
  res.json({ valid: verifyPairingCode(code) });
});

app.post("/api/pairing/renew", (req, res) => {
  res.json(generatePairingCode());
});

// ─── VS Code Bridge API ─────────────────────────────────────────────
app.get("/api/vscode/status", async (req, res) => {
  try {
    const resp = await fetch(`${VSCODE_URL}/?check=` + Date.now(), { method: "GET", timeout: 3000, headers: { "User-Agent": "ZES-HealthCheck" } });
    res.json({ online: resp.ok, status: resp.status });
  } catch (e) {
    res.json({ online: false, error: e.message });
  }
});

app.get("/api/vscode/extensions", (req, res) => {
  try {
    const out = run('find /data/data/com.termux/files/usr/var/lib/proot-distro/containers/debian/rootfs/root/.config/Code-Server/extensions -maxdepth 1 -name "*.json" -o -name "*continue*" -o -name "*cline*" -o -name "*codeium*" 2>/dev/null | head -20');
    const extensions = run('ls /data/data/com.termux/files/usr/var/lib/proot-distro/containers/debian/rootfs/root/.config/Code-Server/extensions/ 2>/dev/null');
    res.json({ extensions: extensions.split("\n").filter(Boolean) });
  } catch (e) {
    res.json({ error: e.message, extensions: [] });
  }
});

// ─── System Tools API ───────────────────────────────────────────────
app.post("/api/tools/execute", async (req, res) => {
  const { tool, args } = req.body || {};
  switch (tool) {
    case "run_command": {
      const output = run(args?.command || "echo no command");
      res.json({ output });
      break;
    }
    case "read_file": {
      try {
        const content = readFileSync(args?.path || "", "utf8");
        res.json({ content, path: args?.path });
      } catch (e) {
        res.status(404).json({ error: e.message });
      }
      break;
    }
    case "write_file": {
      try {
        writeFileSync(args?.path || "", args?.content || "", "utf8");
        res.json({ written: true, path: args?.path });
      } catch (e) {
        res.status(500).json({ error: e.message });
      }
      break;
    }
    case "get_models": {
      // Get available models from 9Router
      try {
        const resp = await fetch("http://127.0.0.1:20128/v1/models", {
          headers: { "Authorization": `Bearer ${API_KEY}` }
        });
        const data = await resp.json();
        res.json({ models: data.data || [] });
      } catch (e) {
        res.json({ error: e.message, models: [] });
      }
      break;
    }
    case "get_agents": {
      // Check which agents are available
      const agents = {};
      try {
        const clineConfig = run('cat /data/data/com.termux/files/usr/var/lib/proot-distro/containers/debian/rootfs/root/.config/Code-Server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json 2>/dev/null || echo "{}"');
        agents.cline = { configured: clineConfig !== "{}", mcp: JSON.parse(clineConfig) };
      } catch { agents.cline = { configured: false }; }
      try {
        const continueExists = existsSync("/data/data/com.termux/files/usr/var/lib/proot-distro/containers/debian/rootfs/root/.config/Code-Server/extensions/continue.continue-2.0.0-linux-arm64");
        agents.continue = { installed: continueExists };
      } catch { agents.continue = { installed: false }; }
      try {
        const codeiumExists = existsSync("/data/data/com.termux/files/usr/var/lib/proot-distro/containers/debian/rootfs/root/.config/Code-Server/extensions/codeium.codeium-1.48.2");
        agents.codeium = { installed: codeiumExists };
      } catch { agents.codeium = { installed: false }; }
      res.json({ agents });
      break;
    }
    default:
      res.status(400).json({ error: `Unknown tool: ${tool}` });
  }
});

// ─── Agent Command API: Send commands to agents in VS Code ──────────
app.post("/api/agent/command", async (req, res) => {
  const { agent, command, args } = req.body || {};
  if (!agent || !command) return res.status(400).json({ error: "agent and command required" });
  
  // For now, execute the command via VS Code Server's remote capabilities
  // Or via the cline-core if available
  try {
    let result = { agent, command, args };
    switch (agent) {
      case "cline": {
        // Cline commands execute via the MCP bridge or directly
        if (command === "ask" || command === "task") {
          // Use Cline's API (would need gRPC bridge in production)
          result.output = `Cline command '${command}' queued. Args: ${JSON.stringify(args)}`;
        } else {
          result.output = `Cline: Unknown command '${command}'`;
        }
        break;
      }
      case "continue": {
        result.output = `Continue command '${command}' queued. Args: ${JSON.stringify(args)}`;
        break;
      }
      case "codeium": {
        result.output = `Codeium command '${command}' not yet supported`;
        break;
      }
      default:
        result.output = `Unknown agent: ${agent}`;
    }
    res.json(result);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ─── Provider list for model selector ───────────────────────────────
app.get("/api/providers", (req, res) => {
  const models = [
    { id: "gh/gpt-4o-mini", name: "GitHub GPT-4o-mini", provider: "github" },
    { id: "gh/gpt-4o", name: "GitHub GPT-4o", provider: "github" },
    { id: "gh/o3-mini", name: "GitHub o3-mini", provider: "github" },
    { id: "gh/claude-sonnet-4.6", name: "GitHub Claude Sonnet 4.6", provider: "github" },
    { id: "gh/gemini-2.5-flash", name: "GitHub Gemini 2.5 Flash", provider: "github" },
    { id: "groq/llama-3.3-70b-versatile", name: "Groq Llama 3.3 70B", provider: "groq" },
    { id: "groq/deepseek-v4", name: "Groq DeepSeek V4", provider: "groq" },
    { id: "groq/qwen-2.5-coder-32b", name: "Groq Qwen 2.5 Coder 32B", provider: "groq" },
    { id: "mistral/mistral-small-3.1", name: "Mistral Small 3.1", provider: "mistral" },
    { id: "cerebras/llama-3.3-70b", name: "Cerebras Llama 3.3 70B", provider: "cerebras" },
    { id: "ds/deepseek-v4-flash", name: "DeepSeek V4 Flash", provider: "deepseek" },
    { id: "cl/gemini-2.5-flash", name: "Gemini 2.5 Flash (CL)", provider: "gemini-cli" },
    { id: "qoder/qwen-2.5-coder-32b", name: "Qoder Qwen 2.5 Coder 32B", provider: "qoder" },
  ];
  res.json(models);
});

// ─── Start Server ────────────────────────────────────────────────────
server.listen(PORT, "0.0.0.0", () => {
  console.log(`🔌 ZES Remote Agent Control listening on :${PORT}`);
  const code = getPairingCode();
  console.log(`🔑 Pairing code: ${code.code} (expires in 5 min)`);
});
