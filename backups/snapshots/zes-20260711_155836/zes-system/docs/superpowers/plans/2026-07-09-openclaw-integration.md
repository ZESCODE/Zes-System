# OpenClaw Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port OpenClaw's best patterns (CDP helpers, agent loop, provider auth, skills) into ZES System's zes-chrome and 9Router infrastructure.

**Architecture:** Five independent modules, each porting a specific OpenClaw pattern: (1) CDP helpers for stable Chrome automation, (2) streaming agent loop with events/tool repair, (3) 9Router provider plugin pattern, (4) skill adoption from `.agents/skills/`, (5) gateway protocol for Codex↔Chrome messages.

**Tech Stack:** Node.js (ESM), existing `mcp-server/` and `js/` extension structure, 9Router at `:20128/v1`.

---

### Task 1: CDP Helpers Module

**Files:**
- Create: `zes-chrome/mcp-server/cdp-helpers.js`
- Modify: `zes-chrome/mcp-server/server.js` (add new REST routes)
- Test: manual via `curl` against running MCP server

**What it does:** Ports OpenClaw's `cdp.ts` and `cdp.helpers.ts` Chrome DevTools Protocol helpers: WS connection management, screenshot capture (viewport + full-page), navigation guard, target filtering.

- [ ] **Step 1: Create cdp-helpers.js with core helpers**

```javascript
// zes-chrome/mcp-server/cdp-helpers.js
// Ported from OpenClaw's CDP helpers — Chrome DevTools Protocol utilities

import WebSocket from 'ws';

const CDP_URL = 'http://localhost:9222/json';

export function isWebSocketUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'ws:' || parsed.protocol === 'wss:';
  } catch { return false; }
}

export function isDirectCdpWebSocketEndpoint(url) {
  if (!isWebSocketUrl(url)) return false;
  try {
    const parsed = new URL(url);
    return /\/devtools\/(?:browser|page|worker|shared_worker|service_worker)\/[^/]/i.test(parsed.pathname);
  } catch { return false; }
}

export async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`CDP HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

export function normalizeCdpWsUrl(wsUrl, cdpUrl) {
  const ws = new URL(wsUrl);
  const cdp = new URL(cdpUrl);
  const isWildcardBind = ws.hostname === '0.0.0.0' || ws.hostname === '[::]';
  const isLoopback = (h) => ['127.0.0.1', 'localhost', '::1', '0.0.0.0', '[::]'].includes(h);
  if ((isLoopback(ws.hostname) || isWildcardBind) && !isLoopback(cdp.hostname)) {
    ws.hostname = cdp.hostname;
    ws.port = cdp.port || (cdp.protocol === 'https:' ? '443' : '80');
    ws.protocol = cdp.protocol === 'https:' ? 'wss:' : 'ws:';
  } else if (isLoopback(ws.hostname) && isLoopback(cdp.hostname)) {
    ws.hostname = cdp.hostname;
  }
  return ws.toString();
}

export function withCdpSocket(wsUrl, fn, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let msgId = 1;
    const pending = new Map();
    const timer = setTimeout(() => {
      ws.close();
      reject(new Error('CDP socket timeout'));
    }, timeoutMs);

    ws.on('open', () => {
      clearTimeout(timer);
      // Wrap send to auto-increment IDs
      const send = (method, params = {}) => new Promise((r, rej) => {
        const id = msgId++;
        pending.set(id, r);
        ws.send(JSON.stringify({ id, method, params }));
      });
      Promise.resolve(fn(send)).then(resolve).catch(reject);
    });
    ws.on('message', (data) => {
      const msg = JSON.parse(data.toString());
      if (msg.id && pending.has(msg.id)) {
        pending.get(msg.id)(msg);
        pending.delete(msg.id);
      }
    });
    ws.on('error', (err) => { clearTimeout(timer); reject(err); });
    ws.on('close', () => { clearTimeout(timer); });
  });
}

export async function captureScreenshot(wsUrl, { fullPage, format = 'png', quality } = {}) {
  return withCdpSocket(wsUrl, async (send) => {
    await send('Page.enable');

    let savedVp = null;
    if (fullPage) {
      const metrics = await send('Page.getLayoutMetrics');
      const size = metrics?.result?.cssContentSize || metrics?.result?.contentSize;
      const cw = size?.width || 0;
      const ch = size?.height || 0;
      if (cw > 0 && ch > 0) {
        const vpResult = await send('Runtime.evaluate', {
          expression: '({ w: window.innerWidth, h: window.innerHeight, dpr: window.devicePixelRatio })',
          returnByValue: true,
        });
        const v = vpResult?.result?.value || { w: 1280, h: 720, dpr: 1 };
        savedVp = { w: v.w, h: v.h, dpr: v.dpr };
        await send('Emulation.setDeviceMetricsOverride', {
          width: Math.ceil(Math.max(v.w, cw)),
          height: Math.ceil(Math.max(v.h, ch)),
          deviceScaleFactor: v.dpr,
          mobile: false,
        });
      }
    }

    const result = await send('Page.captureScreenshot', {
      format,
      ...(quality ? { quality } : {}),
      ...(fullPage ? { captureBeyondViewport: true } : {}),
    });

    if (savedVp) {
      await send('Emulation.setDeviceMetricsOverride', {
        width: savedVp.w,
        height: savedVp.h,
        deviceScaleFactor: savedVp.dpr,
        mobile: false,
      });
    }

    return result?.result?.data || null;
  });
}

export async function listTargets() {
  const targets = await fetchJson(CDP_URL);
  return targets.filter(t => t.type === 'page');
}

export async function getActiveTab() {
  const tabs = await listTargets();
  return tabs[0] || null;
}

export async function evaluateOnPage(wsUrl, expression) {
  return withCdpSocket(wsUrl, async (send) => {
    const result = await send('Runtime.evaluate', {
      expression,
      returnByValue: true,
    });
    return result?.result?.value;
  });
}
```

- [ ] **Step 2: Add CDP screenshot endpoint to server.js**

```javascript
// In server.js ToolRegistry, add a /api/cdp/screenshot route

// Between the existing REST route and 404 handler, add:
if (req.url === '/api/cdp/screenshot' && req.method === 'POST') {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', async () => {
    try {
      const args = body ? JSON.parse(body) : {};
      const targets = await listTargets();
      const tab = targets.find(t => t.type === 'page') || targets[0];
      if (!tab) throw new Error('No page target found');
      const wsUrl = normalizeCdpWsUrl(tab.webSocketDebuggerUrl, CDP_URL);
      const base64 = await captureScreenshot(wsUrl, {
        fullPage: args.fullPage,
        format: args.format || 'png',
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, data: base64 }));
    } catch (err) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
  });
  return;
}
```

- [ ] **Step 3: Replace existing screenshot in tools.js to use new helpers**

In `tools.js`, update the `screenshot` tool to use the new `captureScreenshot` and `normalizeCdpWsUrl` from `cdp-helpers.js`.

- [ ] **Step 4: Update server.js to import from cdp-helpers**

```javascript
import { listTargets, captureScreenshot, normalizeCdpWsUrl, getPageTab } from './cdp-helpers.js';
```

- [ ] **Step 5: Test CDP screenshot endpoint**

Run: `curl -s -X POST http://localhost:5901/api/cdp/screenshot -d '{"fullPage":true}' | head -c 100`
Expected: returns JSON with `{"success":true,"data":"..."}` containing base64 PNG

- [ ] **Step 6: Commit**

```bash
cd /data/data/com.termux/files/home/Zes-System
git add zes-chrome/mcp-server/cdp-helpers.js zes-chrome/mcp-server/server.js zes-chrome/mcp-server/tools.js
git commit -m "feat: add CDP helpers from OpenClaw (screenshot, WS mgmt, target filtering)"
```

---

### Task 2: Streaming Agent Loop with Tool Repair

**Files:**
- Create: `zes-chrome/mcp-server/agent-stream.js`
- Modify: `zes-chrome/mcp-server/agent.js` (integrate streaming)
- Create: `zes-chrome/mcp-server/tool-repair.js`
- Create: `zes-chrome/mcp-server/schema-validate.js`

**What it does:** Ports OpenClaw's `agent-loop.ts` streaming events pattern and `tool-call-repair/` payload fixup. The agent can auto-repair malformed tool calls (e.g., missing required args, wrong types).

- [ ] **Step 1: Create schema-validate.js**

```javascript
// Ported from OpenClaw's llm-core validation.ts — TypeBox-like schema validation for tool calls
// Simplified version using JSON Schema compatible checks

export class SchemaValidator {
  constructor() {
    this._validators = new Map();
  }

  register(name, schema) {
    this._validators.set(name, schema);
  }

  validate(name, args) {
    const schema = this._validators.get(name);
    if (!schema) return { valid: true }; // Unknown tool, skip validation
    return this._validateObject(args, schema, name);
  }

  _validateObject(obj, schema, path) {
    const errors = [];
    if (!obj || typeof obj !== 'object') {
      return { valid: false, errors: [`${path}: expected object, got ${typeof obj}`] };
    }

    // Check required properties
    if (Array.isArray(schema.required)) {
      for (const key of schema.required) {
        if (!(key in obj)) {
          errors.push(`${path}.${key}: required field missing`);
        }
      }
    }

    // Check type of each property
    if (schema.properties) {
      for (const [key, propSchema] of Object.entries(schema.properties)) {
        if (key in obj) {
          const propErrors = this._validateProp(obj[key], propSchema, `${path}.${key}`);
          errors.push(...propErrors);
        }
      }
    }

    return { valid: errors.length === 0, errors };
  }

  _validateProp(value, schema, path) {
    const errors = [];
    if (schema.type === 'string' && typeof value !== 'string') {
      errors.push(`${path}: expected string, got ${typeof value}`);
    } else if (schema.type === 'number' && typeof value !== 'number') {
      errors.push(`${path}: expected number, got ${typeof value}`);
    } else if (schema.type === 'boolean' && typeof value !== 'boolean') {
      errors.push(`${path}: expected boolean, got ${typeof value}`);
    }
    return errors;
  }
}
```

- [ ] **Step 2: Create tool-repair.js**

```js
// Ported from OpenClaw's tool-call-repair/ — fixes malformed tool calls
// Fixes common LLM mistakes: missing fields, wrong types, extra fields

import { SchemaValidator } from './schema-validate.js';

const FUZZY_TOOL_MAP = {
  'clik': 'click',
  'clcik': 'click',
  'clck': 'click',
  'tyep': 'type',
  'typ': 'type',
  'typpe': 'type',
  'navigate': 'browse',
  'nav': 'browse',
  'goto': 'browse',
  'go': 'browse',
  'nvagiate': 'browse',
  'extract_text': 'extract',
  'get_text': 'extract',
  'page_text': 'extract',
  'screnshot': 'screenshot',
  'screen_shot': 'screenshot',
  'capture': 'screenshot',
  'get_context': 'ext_getContext',
  'context': 'ext_getContext',
};

export class ToolRepair {
  constructor(toolRegistry) {
    this.tools = toolRegistry;
    this.schema = new SchemaValidator();
    
    // Register schemas for known tools
    for (const tool of toolRegistry.list()) {
      this.schema.register(tool.name, tool.inputSchema);
    }
  }

  repair(call) {
    if (!call || typeof call !== 'object') return null;

    // Fix tool name via fuzzy map
    let toolName = call.tool || call.name || call.action;
    if (!toolName) return null;
    
    const fixedName = FUZZY_TOOL_MAP[toolName.toLowerCase()] || toolName;
    const tool = this.tools.get(fixedName);
    if (!tool) return null;

    let args = call.args || call.arguments || call.parameters || {};

    // Fix common selector patterns
    if (typeof args === 'string') {
      args = { selector: args, text: args };
    }

    // Ensure string values are strings
    for (const key of ['selector', 'text', 'url']) {
      if (key in args && typeof args[key] !== 'string') {
        args[key] = String(args[key]);
      }
    }

    // Validate
    const validation = this.schema.validate(fixedName, args);
    if (validation.valid || validation.errors.length === 0) {
      return { tool: fixedName, args, repaired: false };
    }

    // Attempt auto-fix for common issues
    const fixed = { ...args };

    // Handle renamed fields (LLMs sometimes use different names)
    if (!fixed.selector && (fixed.css || fixed.query || fixed.element || fixed.id)) {
      fixed.selector = fixed.css || fixed.query || fixed.element || fixed.id;
    }
    if (!fixed.url && (fixed.link || fixed.href || fixed.target)) {
      fixed.url = fixed.link || fixed.href || fixed.target;
    }
    if (!fixed.text && (fixed.value || fixed.content || fixed.input)) {
      fixed.text = fixed.value || fixed.content || fixed.input;
    }

    // Only keep relevant fields
    const relevantKeys = ['selector', 'text', 'url'];
    const cleanArgs = {};
    for (const k of relevantKeys) {
      if (k in fixed) cleanArgs[k] = fixed[k];
    }

    return { tool: fixedName, args: cleanArgs, repaired: true };
  }
}
```

- [ ] **Step 3: Create agent-stream.js (streaming agent loop)**

```js
// Agent loop with streaming events — ported from OpenClaw's agent-core/src/agent-loop.ts

export function createAgentStream() {
  const listeners = [];
  let ended = false;
  let finalResult = null;

  return {
    push(event) { if (!ended) for (const fn of listeners) fn(event); },
    subscribe(fn) { listeners.push(fn); return () => { const i = listeners.indexOf(fn); if (i >= 0) listeners.splice(i, 1); }; },
    end(result) { ended = true; finalResult = result; for (const fn of listeners) fn({ type: 'done', result }); },
    getResult() { return finalResult; },
  };
}

export async function runAgentStream(task, agent, options = {}) {
  const stream = createAgentStream();
  const { onEvent, signal } = options;

  if (onEvent) stream.subscribe(onEvent);

  // Start execution in background
  const promise = agent.run(task, {
    ...options,
    stream,
    signal,
  }).then(result => {
    stream.end(result);
    return result;
  }).catch(err => {
    stream.end({ success: false, error: err.message });
    throw err;
  });

  return { stream, promise };
}
```

- [ ] **Step 4: Integrate ToolRepair into agent.js**

In `agent.js`, import and use `ToolRepair` in the `run()` loop, replacing `_parseAction`:

```javascript
import { ToolRepair } from './tool-repair.js';

// In constructor:
this.repair = new ToolRepair(toolRegistry);

// Replace _parseAction usage:
const repaired = this.repair.repair(parsed);
if (!repaired) {
  messages.push({ role: 'user', content: 'Invalid response format...' });
  continue;
}

const tool = this.tools.get(repaired.tool);
```

- [ ] **Step 5: Validate streaming agent loop**

Test: `curl -X POST http://localhost:5901/api/agent/run -d '{"task":"Go to example.com and tell me the page title"}'`
Expected: Agent completes the task, returns summary.

- [ ] **Step 6: Commit**

```bash
git add zes-chrome/mcp-server/agent-stream.js zes-chrome/mcp-server/tool-repair.js zes-chrome/mcp-server/schema-validate.js zes-chrome/mcp-server/agent.js
git commit -m "feat: streaming agent loop with tool call repair (from OpenClaw patterns)"
```

---

### Task 3: Provider Plugin Pattern for 9Router

**Files:**
- Create: `zes-chrome/mcp-server/9router-provider.js`
- Modify: `storage/emulated/0/Download/ZES-project/Zeschrome/js/background.js` (add provider catalog)
- Create: `docs/9router-provider-plugin.md`

**What it does:** Ports OpenClaw's provider plugin pattern (model catalog, auth, streaming) into a reusable 9Router provider definition. Formalizes how providers are defined instead of ad-hoc code.

- [ ] **Step 1: Create 9router-provider.js**

```javascript
// 9Router Provider Plugin — modeled on OpenClaw's plugin-sdk provider pattern
// Registers models, handles auth, provides streaming/chat

const NINE_ROUTER_BASE = 'http://localhost:20128/v1';

export class NineRouterProvider {
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || NINE_ROUTER_BASE;
    this.defaultModel = options.defaultModel || 'groq/llama-3.3-70b-versatile';
    this.auth = options.auth || { method: 'none' };
    
    // Provider catalog — maps model IDs to API configs
    this.models = {
      'groq/llama-3.3-70b-versatile': { api: 'openai-completions', context: 32768 },
      'gh/gpt-5.4-mini-free-auto': { api: 'openai-completions', context: 262144 },
      'deepseek/deepseek-v4-flash-free': { api: 'openai-completions', context: 262144 },
      'anthropic/claude-sonnet-4-6': { api: 'openai-completions', context: 200000 },
      'openrouter/anthropic/claude-3.5': { api: 'openai-completions', context: 200000 },
    };
  }

  async chat(messages, options = {}) {
    const model = options.model || this.defaultModel;
    const body = {
      model,
      messages,
      temperature: options.temperature ?? 0.7,
      max_tokens: options.maxTokens ?? 4096,
      stream: options.stream ?? false,
    };

    const headers = { 'Content-Type': 'application/json' };
    if (this.auth.type === 'api-key' && this.auth.key) {
      headers['Authorization'] = `Bearer ${this.auth.key}`;
    }
    if (this.auth.type === 'header' && this.auth.header) {
      headers[this.auth.header.name] = this.auth.header.value;
    }

    const res = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const errorText = await res.text().catch(() => res.statusText);
      throw new Error(`9Router ${res.status}: ${errorText.slice(0, 200)}`);
    }

    if (options.stream) {
      return this._handleStream(res);
    }

    const data = await res.json();
    return data.choices?.[0]?.message?.content || '';
  }

  async *_handleStream(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data === '[DONE]') return;
          try {
            const parsed = JSON.parse(data);
            const content = parsed.choices?.[0]?.delta?.content || '';
            if (content) yield content;
          } catch {}
        }
      }
    }
  }

  listModels() {
    return Object.entries(this.models).map(([id, config]) => ({
      id,
      api: config.api,
      contextTokens: config.context,
    }));
  }

  testConnection() {
    return fetch(`${this.baseUrl}/models`, {
      headers: this.auth.type === 'api-key' ? { 'Authorization': `Bearer ${this.auth.key}` } : {},
    }).then(r => r.ok);
  }
}
```

- [ ] **Step 2: Update background.js to use NineRouterProvider**

Replace the ad-hoc `aiChat` function with an instance:

```javascript
import { NineRouterProvider } from './9router-provider.js';

const AI = new NineRouterProvider({ defaultModel: 'groq/llama-3.3-70b-versatile' });
```

- [ ] **Step 3: Create docs/9router-provider-plugin.md**

Documentation of the provider plugin pattern for future extension.

- [ ] **Step 4: Commit**

```bash
git add zes-chrome/mcp-server/9router-provider.js docs/9router-provider-plugin.md
cd /storage/emulated/0/Download/ZES-project/Zeschrome && git add js/background.js 2>/dev/null; cd /data/data/com.termux/files/home/Zes-System
git commit -m "feat: 9Router provider plugin (model catalog, streaming, auth pattern)"
```

---

### Task 4: Port OpenClaw Skills

**Files:**
- Create: `.agents/skills/technical-documentation/SKILL.md`
- Create: `.agents/skills/openclaw-debugging/SKILL.md`
- Create: `.agents/skills/gitcrawl/SKILL.md`

**What it does:** Ports the most applicable `.agents/skills/` from OpenClaw into ZES's agent context. These are ready-to-use agent instruction files.

- [ ] **Step 1: Create .agents/skills/ directory**

```bash
mkdir -p /data/data/com.termux/files/home/Zes-System/.agents/skills/technical-documentation
mkdir -p /data/data/com.termux/files/home/Zes-System/.agents/skills/openclaw-debugging
mkdir -p /data/data/com.termux/files/home/Zes-System/.agents/skills/gitcrawl
```

- [ ] **Step 2: Port technical-documentation skill**

Copy and adapt from OpenClaw's `.agents/skills/technical-documentation/SKILL.md`

- [ ] **Step 3: Port openclaw-debugging skill**

Copy and adapt for ZES/9Router context

- [ ] **Step 4: Port gitcrawl skill**

Copy and adapt

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/
git commit -m "feat: port OpenClaw skills (technical-documentation, debugging, gitcrawl)"
```

---

### Task 5: Gateway Protocol for Codex↔Chrome Messages

**Files:**
- Create: `zes-chrome/mcp-server/gateway-protocol.js`
- Modify: `zes-chrome/mcp-server/server.js` (add typed event endpoints)

**What it does:** Ports OpenClaw's `gateway-protocol/` event schema pattern — typed JSON messages between Codex and Chrome with validation. Currently ZES uses ad-hoc JS objects.

- [ ] **Step 1: Create gateway-protocol.js**

```javascript
// Gateway Protocol — typed agent events between Codex ↔ Chrome
// Ported from OpenClaw's gateway-protocol pattern

export const EventTypes = {
  AGENT_START: 'agent.start',
  AGENT_STEP: 'agent.step',
  AGENT_TOOL_CALL: 'agent.toolCall',
  AGENT_TOOL_RESULT: 'agent.toolResult',
  AGENT_COMPLETE: 'agent.complete',
  AGENT_ERROR: 'agent.error',
  PAGE_STATE: 'page.state',
  PAGE_NAVIGATED: 'page.navigated',
  SYSTEM_INFO: 'system.info',
};

export function createEvent(type, data = {}) {
  return {
    type,
    timestamp: Date.now(),
    id: `evt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    data,
  };
}

export function validateEvent(event) {
  if (!event || typeof event !== 'object') return { valid: false, error: 'not an object' };
  if (!event.type) return { valid: false, error: 'missing type' };
  if (!Object.values(EventTypes).includes(event.type)) return { valid: false, error: `unknown type: ${event.type}` };
  return { valid: true };
}
```

- [ ] **Step 2: Register event endpoint in server.js**

Add: `POST /api/events` for event submission, `GET /api/events/stream` for SSE streaming.

- [ ] **Step 3: Commit**

```bash
git add zes-chrome/mcp-server/gateway-protocol.js
git commit -m "feat: gateway protocol for typed Codex↔Chrome events"
```
