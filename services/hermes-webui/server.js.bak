#!/usr/bin/env node
/**
 * Hermes Agent Web UI v2 — Mobile-optimized dashboard with daisyUI drawer navigation
 * Replaces the built-in Hermes React dashboard. Talks to 9Router + Hermes gateway.
 * Port 8787
 */
import express from "express";
import { createServer } from "http";
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { execSync } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = 8787;
const app = express();
const server = createServer(app);
const HOME = process.env.HOME || "/data/data/com.termux/files/home";

app.use(express.json({ limit: "10mb" }));
app.use(express.static(__dirname));

// ─── Helper ──────────────────────────────────────────────────────
function run(cmd, timeout = 10000) {
  try {
    return execSync(cmd, { encoding: "utf8", timeout, shell: true }).trim();
  } catch (e) {
    return `Error: ${(e.stderr || e.message || "").trim().slice(0, 500)}`;
  }
}

// ─── API: Chat with 9Router (streaming) ──────────────────────────
app.post("/api/chat", async (req, res) => {
  const { messages, model } = req.body || {};
  if (!messages || !Array.isArray(messages)) {
    return res.status(400).json({ error: "messages array required" });
  }
  const modelId = model || "gh/gpt-4o-mini";
  const body = {
    model: modelId,
    messages: [
      { role: "system", content: "You are Hermes AI Agent, part of ZES Control Center. You help manage AI infrastructure on Android/Termux." },
      ...messages
    ],
    stream: true,
    max_tokens: 4096
  };
  try {
    const resp = await fetch("http://127.0.0.1:20128/v1/chat/completions", {
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
    res.end();
  } catch (err) {
    res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
    res.end();
  }
});

// ─── API: Models ──────────────────────────────────────────────────
app.get("/api/models", async (req, res) => {
  try {
    const resp = await fetch("http://127.0.0.1:20128/v1/models");
    const data = await resp.json();
    const models = (data.data || []).map(m => ({
      id: m.id, name: m.id.split("/").pop(), provider: m.id.split("/")[0] || "unknown"
    }));
    res.json(models);
  } catch {
    res.json([
      { id: "gh/gpt-4o-mini", name: "Qwen 2.5 Coder 32B", provider: "Cloudflare" },
      { id: "groq/llama-3.3-70b-versatile", name: "Llama 3.3 70B", provider: "Groq" },
      { id: "gh/gpt-5.4-mini-free-auto", name: "GPT-5.4 Mini Free", provider: "GitHub" }
    ]);
  }
});

// ─── API: Hermes status ──────────────────────────────────────────
app.get("/api/hermes/status", (req, res) => {

  const stateFile = join(HOME, ".hermes/gateway_state.json");
  const state = existsSync(stateFile) ? JSON.parse(readFileSync(stateFile, "utf8")) : {};
  res.json({
    version: run("hermes --version 2>&1 | head -1").split("\n")[0] || "unknown",
    gateway: state.gateway_state || "unknown",
    pid: state.pid || null,
    active_agents: state.active_agents || 0,
    sessions: run("ls ~/.hermes/webui/sessions/*.json 2>/dev/null | wc -l") || "0",
    config: existsSync(join(HOME, ".hermes/config.yaml"))
  });
});

// ─── API: Hermes Providers ──────────────────────────────────────────
app.get("/api/hermes/providers", async (req, res) => {
  try {
    const resp = await fetch("http://127.0.0.1:20128/api/providers", {
      headers: { "x-9r-cli-token": "6071e0697af17e38" }
    });
    const data = await resp.json();
    const providers = (data.connections || []).map(c => ({
      name: c.provider || "unknown",
      status: c.testStatus || "unknown",
      error: c.lastError || null,
      active: c.isActive || false
    }));
    res.json({ primary: { base_url: "http://127.0.0.1:20128/v1", default_model: "gh/gpt-4o-mini", provider: "9Router" }, providers });
  } catch (e) {
    res.json({ primary: { base_url: "http://127.0.0.1:20128/v1", default_model: "gh/gpt-4o-mini", provider: "9Router" }, providers: [], error: e.message });
  }
});

// ─── API: Hermes sessions ─────────────────────────────────────────
app.get("/api/hermes/sessions", (req, res) => {
  try {
    const files = run("ls -t ~/.hermes/webui/sessions/*.json 2>/dev/null || true").split("\n").filter(Boolean);
    const sessions = files.slice(0, 50).map(f => {
      try {
        const data = JSON.parse(readFileSync(f.trim(), "utf8"));
        return { id: data.id || "", title: data.title || `Session ${f.split("/").pop()?.slice(0,12)}`, created: data.created_at || null };
      } catch { return null; }
    }).filter(Boolean);
    res.json(sessions);
  } catch { res.json([]); }
});

// ─── API: System status ───────────────────────────────────────────
app.get("/api/system/status", (req, res) => {
  const checks = [
    { id: "r9", name: "9Router", port: 20128 },
    { id: "dashboard8083", name: "Dashboard", port: 8083 },
    { id: "hermes-gateway", name: "Hermes Gateway", port: null },
    { id: "hermes-webui", name: "Hermes Web UI", port: 8787 },
    { id: "zeschrome-mcp", name: "zesChrome MCP", port: 5901 },
    { id: "tor", name: "Tor", port: 9050 },
    { id: "ttyd", name: "ttyd", port: 7173 },
    { id: "chromium-cdp", name: "Headless Chrome", port: 9222 },
    { id: "vscode-server", name: "VS Code", port: 8000 },
    { id: "vscode-mobile", name: "VS Code Mobile", port: 8001 },
    { id: "agent-dash", name: "Agent Dashboard API", port: 8002 },
    { id: "agent-dash-web", name: "Agent Dashboard Web", port: 8003 }
  ];
  const results = checks.map(svc => {
    const status = run(`sv status /data/data/com.termux/files/usr/var/service/${svc.id} 2>&1 | head -1`);
    const running = status.includes("run:");
    const portOpen = svc.port ? run(`ss -tlnp 2>/dev/null | grep -q ":${svc.port} " && echo ok`).includes("ok") : false;
    return { ...svc, running, portOpen };
  });
  res.json({
    timestamp: new Date().toISOString(),
    services: results,
    env: { node: process.version, hermes: run("hermes --version 2>&1 | head -1").split("\n")[0] }
  });
});

// ─── API: Run eval ────────────────────────────────────────────────
app.get("/api/system/evals", (req, res) => {
  try {
    const out = execSync("python3 ~/Zes-System/scripts/run-evals.py 2>&1 || true", { encoding: "utf8", timeout: 30000, shell: true });
    res.json({ output: out.slice(0, 5000) });
  } catch (e) { res.json({ output: `Error: ${e.message}` }); }
});

// ─── API: Security scan ───────────────────────────────────────────
app.get("/api/system/security", (req, res) => {
  try {
    const out = execSync("bash ~/Zes-System/scripts/security-scan.sh 2>&1 || true", { encoding: "utf8", timeout: 30000, shell: true });
    res.json({ output: out.slice(0, 5000) });
  } catch (e) { res.json({ output: `Error: ${e.message}` }); }
});

// ─── API: Backup ──────────────────────────────────────────────────
app.post("/api/system/backup", (req, res) => {
  try {
    const out = execSync("bash ~/Zes-System/backups/scripts/zes-backup.sh 2>&1 || true", { encoding: "utf8", timeout: 60000, shell: true });
    res.json({ output: out.slice(0, 2000) });
  } catch (e) { res.json({ output: `Error: ${e.message}` }); }
});

// ─── API: Service restart ─────────────────────────────────────────
app.post("/api/system/restart/:service", (req, res) => {
  const allowed = ["r9","dashboard8083","hermes-gateway","hermes-webui","tor","ttyd","chromium-cdp","zeschrome-mcp","codex"];
  if (!allowed.includes(req.params.service)) return res.status(400).json({ error: "Service not allowed" });
  try {
    const out = run(`sv restart /data/data/com.termux/files/usr/var/service/${req.params.service} 2>&1`);
    res.json({ output: out });
  } catch (e) { res.json({ output: `Error: ${e.message}` }); }
});

// ─── API: System exec ─────────────────────────────────────────────
app.post("/api/system/exec", (req, res) => {
  const { cmd } = req.body || {};
  if (!cmd || typeof cmd !== "string") return res.status(400).json({ error: "cmd required" });
  const blocked = ["rm -rf", "mkfs", "dd if="];
  if (blocked.some(b => cmd.toLowerCase().includes(b))) return res.status(403).json({ error: "Blocked" });
  res.json({ output: run(cmd, 15000).slice(0, 10000) });
});

// ─── Start ────────────────────────────────────────────────────────
server.listen(PORT, "127.0.0.1", () => {
  console.log(`Hermes Agent Web UI v2 on http://127.0.0.1:${PORT}`);
});
