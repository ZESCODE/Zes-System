# zesChrome Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the zesChrome Chrome extension (popup + side panel) and MCP server that Codex agents use to control the browser.

**Architecture:** Manifest V3 Chrome extension with popup (320×400px quick actions) and side panel (full AI chat UI). A Node.js MCP server on `:5901` provides tool-calling interface for Codex — it communicates with Chrome via the Chrome DevTools Protocol (CDP) on `:9222`, not through an extension bridge. Background service worker handles tab tracking and message routing.

**Tech Stack:** Chrome Extensions (MV3), vanilla JS (popup+sidepanel), Node.js (MCP server), Chrome DevTools Protocol (CDP)

**Plan Location:** `~/Zes-System/zes-chrome/`

---

### Task 1: Create Extension Directory & Manifest

**Files:**
- Create: `~/Zes-System/zes-chrome/manifest.json`
- Create: `~/Zes-System/zes-chrome/icons/icon16.png`
- Create: `~/Zes-System/zes-chrome/icons/icon48.png`
- Create: `~/Zes-System/zes-chrome/icons/icon128.png`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p ~/Zes-System/zes-chrome/{icons,lib,scripts}
```

- [ ] **Step 2: Write manifest.json**

```json
{
  "manifest_version": 3,
  "name": "ZES Chrome — AI Browser Agent",
  "short_name": "zesChrome",
  "version": "1.0.0",
  "description": "AI-powered browser agent connected to Codex and 9Router",
  "author": "ZES System",
  "minimum_chrome_version": "101",
  "permissions": [
    "sidePanel", "scripting", "tabs", "storage",
    "unlimitedStorage", "activeTab", "identity"
  ],
  "host_permissions": ["<all_urls>"],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "action": {
    "default_title": "zesChrome",
    "default_popup": "popup.html"
  },
  "side_panel": {
    "default_path": "sidepanel.html"
  },
  "commands": {
    "_execute_action": {
      "suggested_key": {
        "default": "Ctrl+Shift+S",
        "mac": "Command+Shift+S"
      }
    }
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ]
}
```

- [ ] **Step 3: Create placeholder icons**

```bash
cd ~/Zes-System/zes-chrome/icons/
python3 -c "
import struct, zlib
def create_png(w, h, filename):
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    raw = b''
    for y in range(h):
        raw += b'\\x00' + b'\\x00\\x00\\x00' * w
    idat = zlib.compress(raw)
    with open(filename, 'wb') as f:
        f.write(b'\\x89PNG\\r\\n\\x1a\\n')
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', idat))
        f.write(chunk(b'IEND', b''))
for s, n in [(16,'icon16.png'),(48,'icon48.png'),(128,'icon128.png')]:
    create_png(s, s, n)
print('Icons created')
"
```

- [ ] **Step 4: Commit**

```bash
cd ~/Zes-System && git add zes-chrome/ && git commit -m "feat(zes-chrome): scaffold extension with manifest V3"
```

---

### Task 2: Background Service Worker

**Files:**
- Create: `~/Zes-System/zes-chrome/background.js`
- Create: `~/Zes-System/zes-chrome/lib/api-client.js`

- [ ] **Step 1: Write background.js**

```javascript
// Background Service Worker — zesChrome
// Tab tracking, message routing, proxy to Dashboard (:8083)

const DASHBOARD_URL = 'http://localhost:8083';

let agentState = {
  active: false,
  currentTask: null,
  currentTabId: null
};

chrome.tabs.onActivated.addListener(({ tabId }) => {
  agentState.currentTabId = tabId;
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'GET_STATE':
      sendResponse(agentState);
      break;

    case 'TOGGLE_AGENT':
      agentState.active = !agentState.active;
      sendResponse({ active: agentState.active });
      break;

    case 'CAPTURE_SCREENSHOT':
      chrome.tabs.captureVisibleTab(agentState.currentTabId, { format: 'png' })
        .then(dataUrl => sendResponse({ screenshot: dataUrl }))
        .catch(err => sendResponse({ error: err.message }));
      return true;

    case 'EXECUTE_ACTION':
      executeAction(message.action, message.args)
        .then(result => sendResponse(result))
        .catch(err => sendResponse({ error: err.message }));
      return true;

    case 'CHAT_MESSAGE':
      proxyToDashboard('/api/agent/chat', {
        message: message.text,
        history: message.history || []
      })
        .then(res => sendResponse(res))
        .catch(err => sendResponse({ error: err.message }));
      return true;

    case 'PAGE_LOADED':
      console.log(`Page loaded: ${message.title} (${message.url})`);
      sendResponse({ received: true });
      break;
  }
});

async function executeAction(action, args) {
  const tabId = agentState.currentTabId;
  if (!tabId) throw new Error('No active tab');

  if (action === 'click') {
    await chrome.scripting.executeScript({
      target: { tabId },
      func: (selector) => {
        const el = document.querySelector(selector);
        if (!el) throw new Error(`Element not found: ${selector}`);
        el.click();
        return { success: true };
      },
      args: [args.selector]
    });
  } else if (action === 'type') {
    await chrome.scripting.executeScript({
      target: { tabId },
      func: (selector, text) => {
        const el = document.querySelector(selector);
        if (!el) throw new Error(`Element not found: ${selector}`);
        el.value = text;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        return { success: true };
      },
      args: [args.selector, args.text]
    });
  } else if (action === 'extract') {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: (selector) => {
        if (selector === 'body') return document.body.innerText.slice(0, 10000);
        const el = document.querySelector(selector);
        return el ? el.innerText || el.value || el.textContent : null;
      },
      args: [args.selector || 'body']
    });
    return { text: results[0]?.result || '' };
  } else if (action === 'wait') {
    return await waitForElement(args.selector, args.timeout || 10000);
  }

  return { success: true };
}

async function waitForElement(selector, timeoutMs) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const results = await chrome.scripting.executeScript({
      target: { tabId: agentState.currentTabId },
      func: (sel) => !!document.querySelector(sel),
      args: [selector]
    });
    if (results[0]?.result) return { text: `Element appeared: ${selector}` };
    await new Promise(r => setTimeout(r, 500));
  }
  return { text: `Timeout waiting for: ${selector}` };
}

async function proxyToDashboard(path, body) {
  const res = await fetch(`${DASHBOARD_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Dashboard error: ${res.status}`);
  return res.json();
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});
```

- [ ] **Step 2: Write api-client.js**

```javascript
// API Client — talks to Dashboard (:8083)

export class ApiClient {
  static BASE = 'http://localhost:8083';

  static async fetch(path, options = {}) {
    const res = await fetch(`${this.BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  }

  static chat(message, history = []) {
    return this.fetch('/api/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, history })
    });
  }

  static getModels() { return this.fetch('/api/models'); }
  static getServices() { return this.fetch('/api/services'); }
  static getHistory() { return this.fetch('/api/agent/history'); }
}
```

- [ ] **Step 3: Commit**

```bash
cd ~/Zes-System && git add zes-chrome/background.js zes-chrome/lib/api-client.js && git commit -m "feat(zes-chrome): background service worker and API client"
```

---

### Task 3: Popup UI

**Files:**
- Create: `~/Zes-System/zes-chrome/popup.html`
- Create: `~/Zes-System/zes-chrome/popup.js`
- Create: `~/Zes-System/zes-chrome/popup.css`

- [ ] **Step 1: Write popup.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>zesChrome</title>
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="popup-container">
    <div class="header">
      <div class="logo">
        <div class="z-logo">Z</div>
        <span class="title">zesChrome</span>
      </div>
      <div class="agent-toggle">
        <span class="toggle-label">Agent</span>
        <label class="switch">
          <input type="checkbox" id="agentToggle">
          <span class="slider"></span>
        </label>
      </div>
    </div>

    <div class="status-bar">
      <div class="status-item">
        <span class="status-dot" id="mcpStatus"></span>
        <span>MCP</span>
      </div>
      <div class="status-item">
        <span class="status-dot" id="dashboardStatus"></span>
        <span>Dashboard</span>
      </div>
      <div class="status-item">
        <span class="status-dot" id="modelStatus"></span>
        <span>9Router</span>
      </div>
    </div>

    <div class="section-label">Connected Services</div>
    <div class="services" id="servicesList">
      <div class="service-item disabled">Gmail</div>
      <div class="service-item disabled">Drive</div>
      <div class="service-item disabled">GitHub</div>
    </div>

    <div class="section-label">Quick Actions</div>
    <div class="quick-actions">
      <button class="action-btn" id="openSidePanel">💬 Open Side Panel</button>
      <button class="action-btn" id="captureScreenshot">📸 Screenshot</button>
      <button class="action-btn" id="openDashboard">📊 Dashboard</button>
    </div>

    <div class="section-label">Recent Tasks</div>
    <div class="task-list" id="taskList">
      <div class="task-item empty">No recent tasks</div>
    </div>

    <div class="footer">
      <span>ZES System v1.0</span>
      <a href="#" id="settingsBtn">⚙️</a>
    </div>
  </div>
  <script src="popup.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write popup.css**

```css
:root {
  --bg: #0d1117; --surface: #161b22; --surface2: #21262d;
  --border: #30363d; --text: #e6edf3; --muted: #8b949e;
  --accent: #03a9f4; --accent2: #f441a5; --success: #3fb950;
  --error: #f85149;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 340px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg); color: var(--text); font-size: 13px;
}
.popup-container { padding: 12px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.logo { display: flex; align-items: center; gap: 8px; }
.z-logo {
  width: 28px; height: 28px; border-radius: 6px;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 16px; color: #fff;
}
.title { font-weight: 600; font-size: 15px; }
.switch { position: relative; display: inline-block; width: 36px; height: 20px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
  background-color: var(--surface2); transition: .3s; border-radius: 20px;
}
.slider:before {
  position: absolute; content: ""; height: 14px; width: 14px; left: 3px; bottom: 3px;
  background-color: var(--muted); transition: .3s; border-radius: 50%;
}
input:checked + .slider { background: linear-gradient(90deg, var(--accent), var(--accent2)); }
input:checked + .slider:before { transform: translateX(16px); background: #fff; }
.toggle-label { font-size: 12px; color: var(--muted); margin-right: 6px; }
.status-bar {
  display: flex; gap: 12px; margin-bottom: 12px;
  background: var(--surface); padding: 8px 12px; border-radius: 6px;
}
.status-item { display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--muted); }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--error); }
.status-dot.online { background: var(--success); }
.section-label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; margin-top: 8px; }
.services { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 4px; }
.service-item {
  padding: 4px 10px; border-radius: 12px; font-size: 11px;
  background: var(--surface); border: 1px solid var(--border); color: var(--muted);
}
.quick-actions { display: flex; flex-direction: column; gap: 6px; }
.action-btn {
  padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px;
  background: var(--surface); color: var(--text); font-size: 12px; cursor: pointer;
  text-align: left; transition: background .2s;
}
.action-btn:hover { background: var(--surface2); }
.task-list { margin-bottom: 4px; }
.task-item { padding: 8px; border-radius: 6px; background: var(--surface); font-size: 12px; color: var(--text); }
.task-item.empty { color: var(--muted); text-align: center; }
.footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 12px; padding-top: 8px; border-top: 1px solid var(--border);
  font-size: 11px; color: var(--muted);
}
.footer a { color: var(--muted); text-decoration: none; font-size: 14px; }
```

- [ ] **Step 3: Write popup.js**

```javascript
document.addEventListener('DOMContentLoaded', async () => {
  const state = await chrome.runtime.sendMessage({ type: 'GET_STATE' });

  const toggle = document.getElementById('agentToggle');
  toggle.checked = state.active;
  toggle.addEventListener('change', async () => {
    await chrome.runtime.sendMessage({ type: 'TOGGLE_AGENT' });
  });

  checkStatuses();

  document.getElementById('openSidePanel').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) { await chrome.sidePanel.open({ tabId: tab.id }); window.close(); }
  });

  document.getElementById('captureScreenshot').addEventListener('click', async () => {
    const result = await chrome.runtime.sendMessage({ type: 'CAPTURE_SCREENSHOT' });
    if (result.screenshot) {
      const w = window.open('');
      w.document.write(`<img src="${result.screenshot}" style="max-width:100%">`);
    }
  });

  document.getElementById('openDashboard').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:8083' });
  });
});

async function checkStatuses() {
  try { const r = await fetch('http://localhost:5901/health'); if (r.ok) document.getElementById('mcpStatus').classList.add('online'); } catch {}
  try { const r = await fetch('http://localhost:8083/'); if (r.ok) document.getElementById('dashboardStatus').classList.add('online'); } catch {}
  try { const r = await fetch('http://localhost:20128/'); if (r.ok || r.status === 307) document.getElementById('modelStatus').classList.add('online'); } catch {}
}
```

- [ ] **Step 4: Commit**

```bash
cd ~/Zes-System && git add zes-chrome/popup.* && git commit -m "feat(zes-chrome): popup UI with agent toggle and status"
```

---

### Task 4: Side Panel UI

**Files:**
- Create: `~/Zes-System/zes-chrome/sidepanel.html`
- Create: `~/Zes-System/zes-chrome/sidepanel.js`
- Create: `~/Zes-System/zes-chrome/sidepanel.css`

- [ ] **Step 1: Write sidepanel.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>zesChrome Agent</title>
  <link rel="stylesheet" href="sidepanel.css">
</head>
<body>
  <div id="app">
    <div class="panel-header">
      <div class="panel-logo">
        <div class="z-logo">Z</div>
        <span>zesChrome Agent</span>
      </div>
      <button id="settingsBtn" title="Settings">⚙️</button>
    </div>

    <div class="tab-bar">
      <button class="tab active" data-tab="chat">💬 Chat</button>
      <button class="tab" data-tab="agent">🤖 Agent</button>
      <button class="tab" data-tab="services">🔌 Services</button>
      <button class="tab" data-tab="history">📋 History</button>
    </div>

    <div class="tab-content active" id="tab-chat">
      <div class="messages" id="messages"></div>
      <div class="input-area">
        <textarea id="chatInput" placeholder="Ask the agent to do something..." rows="3"></textarea>
        <button id="sendBtn">Send</button>
      </div>
    </div>

    <div class="tab-content" id="tab-agent">
      <div class="agent-status">
        <div class="status-indicator" id="agentStatusIndicator">● Idle</div>
        <button id="toggleAgentBtn" class="primary-btn">Activate Agent</button>
      </div>
      <div class="agent-info">
        <p><strong>Model:</strong> <span id="currentModel">Claude (9Router)</span></p>
        <p><strong>Tab:</strong> <span id="currentTab">None</span></p>
      </div>
      <div class="section-label">Current Task</div>
      <div class="task-progress" id="taskProgress">
        <div class="task-step">No active task</div>
      </div>
    </div>

    <div class="tab-content" id="tab-services">
      <div class="services-list" id="servicesPanel">
        <div class="service-card" data-service="gmail">
          <span>📧 Gmail</span>
          <span class="service-status disconnected">Disconnected</span>
          <button class="connect-btn" data-service="gmail">Connect</button>
        </div>
        <div class="service-card" data-service="drive">
          <span>📁 Drive</span>
          <span class="service-status disconnected">Disconnected</span>
          <button class="connect-btn" data-service="drive">Connect</button>
        </div>
        <div class="service-card" data-service="calendar">
          <span>📅 Calendar</span>
          <span class="service-status disconnected">Disconnected</span>
          <button class="connect-btn" data-service="calendar">Connect</button>
        </div>
        <div class="service-card" data-service="github">
          <span>🐙 GitHub</span>
          <span class="service-status disconnected">Disconnected</span>
          <button class="connect-btn" data-service="github">Connect</button>
        </div>
      </div>
    </div>

    <div class="tab-content" id="tab-history">
      <div class="history-filters">
        <input type="text" id="historySearch" placeholder="Search history...">
      </div>
      <div class="history-list" id="historyList">
        <div class="history-item empty">No history yet</div>
      </div>
    </div>
  </div>
  <script src="sidepanel.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write sidepanel.css**

```css
:root {
  --bg: #0d1117; --surface: #161b22; --surface2: #21262d;
  --border: #30363d; --text: #e6edf3; --text2: #c9d1d9;
  --muted: #8b949e; --accent: #03a9f4; --accent2: #f441a5;
  --success: #3fb950; --error: #f85149;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg); color: var(--text); font-size: 13px;
  height: 100vh; overflow: hidden;
}
#app { display: flex; flex-direction: column; height: 100vh; }
.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px; border-bottom: 1px solid var(--border); background: var(--surface);
}
.panel-logo { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.z-logo {
  width: 24px; height: 24px; border-radius: 4px;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; color: #fff; font-weight: 700;
}
#settingsBtn { background: none; border: none; color: var(--muted); font-size: 16px; cursor: pointer; }
.tab-bar {
  display: flex; border-bottom: 1px solid var(--border); background: var(--surface);
}
.tab {
  flex: 1; padding: 8px 4px; border: none; background: transparent;
  color: var(--muted); font-size: 11px; cursor: pointer;
  border-bottom: 2px solid transparent; transition: all .2s;
}
.tab:hover { color: var(--text); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-content { display: none; flex: 1; overflow-y: auto; padding: 8px; }
.tab-content.active { display: flex; flex-direction: column; }
.messages { flex: 1; overflow-y: auto; margin-bottom: 8px; }
.message {
  padding: 8px 10px; margin-bottom: 6px; border-radius: 6px;
  background: var(--surface); font-size: 12px; line-height: 1.5;
}
.message.user { border-left: 3px solid var(--accent); }
.message.assistant { border-left: 3px solid var(--accent2); }
.message.system { border-left: 3px solid var(--warning); font-style: italic; color: var(--muted); }
.input-area { display: flex; gap: 6px; align-items: end; }
#chatInput {
  flex: 1; padding: 8px; border: 1px solid var(--border); border-radius: 6px;
  background: var(--surface); color: var(--text); font-size: 12px;
  resize: none; font-family: inherit; min-height: 44px;
}
#chatInput:focus { outline: none; border-color: var(--accent); }
#sendBtn {
  padding: 8px 16px; border: none; border-radius: 6px;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  color: #fff; font-size: 12px; font-weight: 600; cursor: pointer;
}
.agent-status { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.status-indicator { font-size: 13px; font-weight: 600; }
.primary-btn {
  padding: 6px 14px; border: none; border-radius: 6px;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  color: #fff; font-size: 12px; font-weight: 600; cursor: pointer;
}
.agent-info p { margin-bottom: 4px; font-size: 12px; color: var(--text2); }
.section-label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
.services-list { display: flex; flex-direction: column; gap: 6px; }
.service-card {
  display: flex; align-items: center; gap: 8px;
  padding: 10px; border-radius: 6px; background: var(--surface); font-size: 12px;
}
.service-card span:first-child { flex: 1; }
.service-status { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.service-status.disconnected { background: rgba(248,81,73,0.1); color: var(--error); }
.service-status.connected { background: rgba(63,185,80,0.1); color: var(--success); }
.connect-btn {
  padding: 4px 10px; border: 1px solid var(--border); border-radius: 4px;
  background: var(--surface2); color: var(--text); font-size: 11px; cursor: pointer;
}
.history-filters { margin-bottom: 8px; }
#historySearch { width: 100%; padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface); color: var(--text); font-size: 12px; }
.history-item { padding: 8px; border-radius: 6px; background: var(--surface); margin-bottom: 4px; font-size: 12px; }
```

- [ ] **Step 3: Write sidepanel.js**

```javascript
let chatHistory = [];
let agentActive = false;

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
    });
  });

  const sendBtn = document.getElementById('sendBtn');
  const chatInput = document.getElementById('chatInput');
  sendBtn.addEventListener('click', () => sendMessage());
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  document.getElementById('toggleAgentBtn').addEventListener('click', async () => {
    const result = await chrome.runtime.sendMessage({ type: 'TOGGLE_AGENT' });
    agentActive = result.active;
    updateAgentUI();
  });

  document.querySelectorAll('.connect-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      chrome.tabs.create({ url: `http://localhost:8083/auth/${btn.dataset.service}` });
    });
  });

  loadState();
});

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, 'user');
  input.value = '';
  const thinkingId = addMessage('Thinking...', 'system');

  try {
    const response = await chrome.runtime.sendMessage({
      type: 'CHAT_MESSAGE', text, history: chatHistory.slice(-10)
    });
    document.getElementById(thinkingId)?.remove();
    if (response.error) addMessage(`Error: ${response.error}`, 'system');
    else addMessage(response.text || response.message || JSON.stringify(response), 'assistant');
  } catch (err) {
    document.getElementById(thinkingId)?.remove();
    addMessage(`Error: ${err.message}`, 'system');
  }
}

function addMessage(text, role) {
  const messages = document.getElementById('messages');
  const id = `msg-${Date.now()}`;
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.id = id;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  chatHistory.push({ role, text });
  return id;
}

async function loadState() {
  try {
    const state = await chrome.runtime.sendMessage({ type: 'GET_STATE' });
    agentActive = state.active;
    updateAgentUI();
    if (state.currentTabId) {
      const tab = await chrome.tabs.get(state.currentTabId);
      document.getElementById('currentTab').textContent = tab?.title || 'Unknown';
    }
  } catch (err) { console.error('Failed to load state:', err); }
}

function updateAgentUI() {
  const indicator = document.getElementById('agentStatusIndicator');
  const btn = document.getElementById('toggleAgentBtn');
  if (agentActive) {
    indicator.textContent = '● Active';
    indicator.style.color = 'var(--success)';
    btn.textContent = 'Deactivate';
  } else {
    indicator.textContent = '● Idle';
    indicator.style.color = 'var(--muted)';
    btn.textContent = 'Activate Agent';
  }
}
```

- [ ] **Step 4: Commit**

```bash
cd ~/Zes-System && git add zes-chrome/sidepanel.* && git commit -m "feat(zes-chrome): side panel UI with chat, agent, services tabs"
```

---

### Task 5: Content Script

**Files:**
- Create: `~/Zes-System/zes-chrome/content.js`

- [ ] **Step 1: Write content.js**

```javascript
// zesChrome Content Script — runs on every page
// Reports page context and handles element interaction

(() => {
  'use strict';

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.action) {
      case 'GET_PAGE_CONTEXT':
        sendResponse(getPageContext());
        break;
      case 'FIND_ELEMENT':
        sendResponse(findElement(message.selector));
        break;
      case 'GET_FORM_FIELDS':
        sendResponse(getFormFields());
        break;
    }
    return true;
  });

  function getPageContext() {
    return {
      title: document.title,
      url: window.location.href,
      text: document.body.innerText.slice(0, 10000),
      forms: Array.from(document.forms).map(f => ({
        id: f.id,
        fields: Array.from(f.elements).map(e => ({
          name: e.name, type: e.type, placeholder: e.placeholder, id: e.id, required: e.required
        }))
      })),
      stats: {
        links: document.querySelectorAll('a').length,
        buttons: document.querySelectorAll('button, [role=button]').length,
        inputs: document.querySelectorAll('input, textarea, select').length
      }
    };
  }

  function findElement(selector) {
    const el = document.querySelector(selector);
    if (!el) return { found: false };
    const rect = el.getBoundingClientRect();
    return {
      found: true, tag: el.tagName,
      text: el.textContent?.slice(0, 200),
      rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      visible: rect.width > 0 && rect.height > 0
    };
  }

  function getFormFields() {
    return Array.from(document.querySelectorAll('input, textarea, select')).map(el => {
      const label = document.querySelector(`label[for="${el.id}"]`);
      const parentLabel = el.closest('label');
      return {
        id: el.id, name: el.name, type: el.type,
        placeholder: el.placeholder,
        label: label?.textContent || parentLabel?.textContent || '',
        value: el.value, required: el.required
      };
    });
  }

  chrome.runtime.sendMessage({
    type: 'PAGE_LOADED',
    url: window.location.href,
    title: document.title
  });
})();
```

- [ ] **Step 2: Commit**

```bash
cd ~/Zes-System && git add zes-chrome/content.js && git commit -m "feat(zes-chrome): content script for page context and interaction"
```

---

### Task 6: MCP Server (Codex Integration)

**Files:**
- Create: `~/Zes-System/zes-chrome/mcp-server/package.json`
- Create: `~/Zes-System/zes-chrome/mcp-server/server.js`
- Create: `~/Zes-System/zes-chrome/mcp-server/tools.js`

The MCP server is a Node.js process on `:5901` that Codex agents call to control the browser. It communicates with Chrome via the Chrome DevTools Protocol (CDP) on `:9222` — no extension bridge needed.

- [ ] **Step 1: Write package.json**

```bash
mkdir -p ~/Zes-System/zes-chrome/mcp-server
cat > ~/Zes-System/zes-chrome/mcp-server/package.json << 'EOF'
{
  "name": "zeschrome-mcp",
  "version": "1.0.0",
  "description": "MCP server bridging Codex ↔ Chrome browser via CDP",
  "main": "server.js",
  "type": "module",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {}
}
EOF
```

- [ ] **Step 2: Write server.js**

```javascript
import http from 'http';
import { ToolRegistry } from './tools.js';

const PORT = 5901;
const tools = new ToolRegistry();

async function handleMCP(method, params) {
  switch (method) {
    case 'mcp.listTools':
      return {
        tools: tools.list().map(t => ({
          name: t.name,
          description: t.description,
          inputSchema: t.inputSchema
        }))
      };
    case 'mcp.callTool': {
      const tool = tools.get(params.name);
      if (!tool) throw new Error(`Unknown tool: ${params.name}`);
      return await tool.execute(params.arguments || {});
    }
    case 'mcp.ping':
      return { status: 'ok', timestamp: Date.now() };
    default:
      throw new Error(`Unknown method: ${method}`);
  }
}

const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.writeHead(200); res.end(); return; }

  if (req.url === '/health' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', port: PORT }));
    return;
  }

  if (req.url === '/mcp' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const { method, params } = JSON.parse(body);
        const result = await handleMCP(method, params);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ jsonrpc: '2.0', result, id: params?.id || 1 }));
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          jsonrpc: '2.0',
          error: { code: -32603, message: err.message },
          id: null
        }));
      }
    });
    return;
  }

  res.writeHead(404); res.end('Not found');
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`zesChrome MCP Server on :${PORT}`);
  console.log(`MCP: http://localhost:${PORT}/mcp`);
  console.log(`Health: http://localhost:${PORT}/health`);
});
```

- [ ] **Step 3: Write tools.js**

```javascript
// MCP Tools — controls Chrome via CDP on :9222
// Uses Chrome DevTools Protocol directly, no extension bridge needed

const CDP_URL = 'http://localhost:9222/json';

export class ToolRegistry {
  constructor() {
    this._tools = new Map();
    this._ws = null;
    this._msgId = 1;
    this._pending = new Map();
    this.registerDefaults();
  }

  async _connect() {
    const res = await fetch(CDP_URL);
    const targets = await res.json();
    const tab = targets.find(t => t.type === 'page') || targets[0];
    if (!tab) throw new Error('No browser tab found via CDP');
    this._ws = new WebSocket(tab.webSocketDebuggerUrl);
    this._ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.id && this._pending.has(data.id)) {
        this._pending.get(data.id)(data);
        this._pending.delete(data.id);
      }
    };
    return new Promise((resolve, reject) => {
      this._ws.onopen = () => resolve();
      this._ws.onerror = (e) => reject(e);
    });
  }

  async _send(method, params = {}) {
    if (!this._ws || this._ws.readyState !== WebSocket.OPEN) await this._connect();
    const id = this._msgId++;
    this._ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve) => {
      this._pending.set(id, (data) => {
        if (data.error) reject(new Error(data.error.message));
        else resolve(data.result);
      });
    });
  }

  async _evaluate(expression) {
    const result = await this._send('Runtime.evaluate', {
      expression, returnByValue: true
    });
    return result.result?.value;
  }

  async _navigate(url) {
    await this._send('Page.enable');
    await this._send('Page.navigate', { url });
    await new Promise(r => setTimeout(r, 2000));
    return await this._evaluate(
      'JSON.stringify({title: document.title, text: document.body.innerText.slice(0,10000)})'
    ).then(JSON.parse);
  }

  register(name, tool) { this._tools.set(name, tool); }
  get(name) { return this._tools.get(name); }
  list() { return Array.from(this._tools.values()); }

  registerDefaults() {
    this.register('browse', {
      name: 'browse',
      description: 'Navigate to a URL and return page content',
      inputSchema: {
        type: 'object',
        properties: { url: { type: 'string' } },
        required: ['url']
      },
      execute: async (args) => {
        const ctx = await this._navigate(args.url);
        return { content: [{ type: 'text', text: `Title: ${ctx.title}\n\n${ctx.text.slice(0,5000)}` }] };
      }
    });

    this.register('screenshot', {
      name: 'screenshot',
      description: 'Take a screenshot of the current tab',
      inputSchema: { type: 'object', properties: {}, required: [] },
      execute: async () => {
        await this._send('Page.enable');
        const { data } = await this._send('Page.captureScreenshot', { format: 'png' });
        return { content: [{ type: 'image', data: `data:image/png;base64,${data}`, mimeType: 'image/png' }] };
      }
    });

    this.register('click', {
      name: 'click',
      description: 'Click an element by CSS selector',
      inputSchema: {
        type: 'object',
        properties: { selector: { type: 'string' } },
        required: ['selector']
      },
      execute: async (args) => {
        const result = await this._evaluate(
          `(()=>{const e=document.querySelector('${args.selector.replace(/'/g,"\\'")}');if(!e)return'NOT_FOUND';e.click();return'CLICKED'})()`
        );
        return { content: [{ type: 'text', text: `${result}: ${args.selector}` }] };
      }
    });

    this.register('type', {
      name: 'type',
      description: 'Type text into an input field',
      inputSchema: {
        type: 'object',
        properties: {
          selector: { type: 'string' },
          text: { type: 'string' }
        },
        required: ['selector', 'text']
      },
      execute: async (args) => {
        const safeText = args.text.replace(/'/g, "\\'").replace(/\\/g, '\\\\');
        const result = await this._evaluate(
          `(()=>{const e=document.querySelector('${args.selector.replace(/'/g,"\\'")}');if(!e)return'NOT_FOUND';e.value='${safeText}';e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return'TYPED'})()`
        );
        return { content: [{ type: 'text', text: `${result}: ${args.selector}` }] };
      }
    });

    this.register('extract', {
      name: 'extract',
      description: 'Extract text from the page or element',
      inputSchema: {
        type: 'object',
        properties: {
          selector: { type: 'string', description: 'CSS selector (body for full page)', default: 'body' }
        },
        required: []
      },
      execute: async (args) => {
        const sel = args.selector || 'body';
        const text = await this._evaluate(
          `document.querySelector('${sel.replace(/'/g,"\\'")}')?.textContent?.slice(0,10000)||''`
        );
        return { content: [{ type: 'text', text }] };
      }
    });

    this.register('wait', {
      name: 'wait',
      description: 'Wait for an element to appear on the page',
      inputSchema: {
        type: 'object',
        properties: {
          selector: { type: 'string' },
          timeout: { type: 'number', default: 10000 }
        },
        required: ['selector']
      },
      execute: async (args) => {
        const timeout = args.timeout || 10000;
        const start = Date.now();
        let found = false;
        while (Date.now() - start < timeout) {
          const result = await this._evaluate(
            `!!document.querySelector('${args.selector.replace(/'/g,"\\'")}')`
          );
          if (result) { found = true; break; }
          await new Promise(r => setTimeout(r, 500));
        }
        return { content: [{ type: 'text', text: found ? `Appeared: ${args.selector}` : `Timeout: ${args.selector}` }] };
      }
    });

    this.register('auth', {
      name: 'auth',
      description: 'Start OAuth flow for a service',
      inputSchema: {
        type: 'object',
        properties: {
          service: { type: 'string', enum: ['gmail','drive','calendar','github','slack'] }
        },
        required: ['service']
      },
      execute: async (args) => {
        await this._navigate(`http://localhost:8083/auth/${args.service}`);
        return { content: [{ type: 'text', text: `Auth flow started for ${args.service}` }] };
      }
    });

    this.register('run_task', {
      name: 'run_task',
      description: 'Run an autonomous browser task via AI',
      inputSchema: {
        type: 'object',
        properties: { task: { type: 'string' } },
        required: ['task']
      },
      execute: async (args) => {
        const res = await fetch('http://localhost:8083/api/agent/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: args.task, history: [], mode: 'autonomous' })
        });
        const data = await res.json();
        return { content: [{ type: 'text', text: data.text || JSON.stringify(data) }] };
      }
    });
  }
}
```

- [ ] **Step 4: Create runsv service**

```bash
# Create runsv service directory
mkdir -p ~/.9router/services/zeschrome-mcp/log

# Main run script
cat > ~/.9router/services/zeschrome-mcp/run << 'SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
exec node /data/data/com.termux/files/home/Zes-System/zes-chrome/mcp-server/server.js
SCRIPT
chmod +x ~/.9router/services/zeschrome-mcp/run

# Log run script
cat > ~/.9router/services/zeschrome-mcp/log/run << 'SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
exec svlogd -tt /data/data/com.termux/files/home/.9router/services/zeschrome-mcp/log/
SCRIPT
chmod +x ~/.9router/services/zeschrome-mcp/log/run

# Link to runsv
ln -sf ~/.9router/services/zeschrome-mcp /data/data/com.termux/files/usr/var/service/zeschrome-mcp
```

- [ ] **Step 5: Install and test server**

```bash
cd ~/Zes-System/zes-chrome/mcp-server
node server.js &
sleep 1
curl -s http://localhost:5901/health
```

Expected: `{"status":"ok","port":5901}`

- [ ] **Step 6: Test MCP tool listing**

```bash
curl -s -X POST http://localhost:5901/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"mcp.listTools","params":{},"id":1}'
```

Expected: JSON response with 8 tool definitions (browse, screenshot, click, type, extract, wait, auth, run_task)

- [ ] **Step 7: Commit**

```bash
cd ~/Zes-System && git add zes-chrome/mcp-server/ && git commit -m "feat(zes-chrome): MCP server on :5901 with CDP-based Chrome control"
```

---

### Task 7: Load Extension in Chrome & Final Verification

- [ ] **Step 1: Load the extension in Chrome**

```bash
echo "1. Open chrome://extensions"
echo "2. Enable 'Developer mode'"
echo "3. Click 'Load unpacked'"
echo "4. Select ~/Zes-System/zes-chrome/"
echo "5. Extension 'ZES Chrome — AI Browser Agent' should appear"
```

- [ ] **Step 2: Verify all components**

```bash
# 1. Start MCP server
cd ~/Zes-System/zes-chrome/mcp-server && node server.js &
sleep 1

# 2. Health check
echo "=== Health ===" && curl -s http://localhost:5901/health

# 3. List tools
echo "=== Tools ===" && curl -s -X POST http://localhost:5901/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"mcp.listTools","params":{},"id":1}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'{len(d[\"result\"][\"tools\"])} tools: ' + ', '.join(t['name'] for t in d['result']['tools']))"

# 4. Test screenshot (requires Chrome running with --remote-debugging-port=9222)
echo "=== Screenshot ===" && curl -s -X POST http://localhost:5901/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"mcp.callTool","params":{"name":"screenshot","arguments":{}},"id":1}' | python3 -c "import sys,json;d=json.load(sys.stdin);r=d['result']['content'][0];print(f'{r[\"type\"]}: {len(r[\"data\"])} chars')"

# 5. Extension checks
echo "=== Popup ===" && [ -f ~/Zes-System/zes-chrome/popup.html ] && echo "popup.html exists ✓"
echo "=== Side Panel ===" && [ -f ~/Zes-System/zes-chrome/sidepanel.html ] && echo "sidepanel.html exists ✓"
echo "=== Manifest ===" && python3 -c "import json;m=json.load(open('~/Zes-System/zes-chrome/manifest.json'));print(f'Version {m[\"version\"]} ✓')"
```

- [ ] **Step 3: Commit final**

```bash
cd ~/Zes-System && git add -A && git commit -m "feat(zes-chrome): Phase 1 complete — extension + MCP server"
```

---

## Verification Checklist

- [ ] Extension loads in `chrome://extensions` without errors
- [ ] Popup opens with Z logo, agent toggle, status dots, quick actions
- [ ] Side panel opens with Chat, Agent, Services, History tabs
- [ ] Content script runs on every page (check console for "PAGE_LOADED")
- [ ] `curl http://localhost:5901/health` returns 200
- [ ] `mcp.listTools` returns 8 tools
- [ ] `mcp.callTool screenshot` captures screenshot data
- [ ] `mcp.callTool browse` navigates Chrome to a URL
- [ ] `mcp.callTool click` clicks an element
- [ ] `sv status zeschrome-mcp` shows "run"
- [ ] All files committed to `~/Zes-System`

## Phase 2 Preview

Dashboard API endpoints, Composio OAuth, computer-use (Gemini vision), multi-model agent planner, Hermes cron integration.
