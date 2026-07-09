// MCP Tools — Controls Chrome via CDP + ZES Extension Bridge
// Uses Chrome DevTools Protocol directly + extension service worker

import { BrowserAgent } from "./agent.js";
import { captureScreenshot, captureScreenshotPng, normalizeCdpWsUrl, getActiveTab, listTargets, withCdpSocket, evaluateOnPage } from "./cdp-helpers.js";
let _agentInstance = null;
let _registry = null;
function getAgent() {
  if (!_agentInstance) _agentInstance = new BrowserAgent(_registry);
  return _agentInstance;
}


const CDP_URL = 'http://localhost:9222/json';

export class ToolRegistry {
  constructor() {
    this._tools = new Map();
    this._ws = null;
    this._msgId = 1;
    this._pending = new Map();
    this.registerDefaults();
    _registry = this;
  }

  async _connect() {
    const res = await fetch(CDP_URL);
    const targets = await res.json();
    const tab = targets.find(t => t.type === 'page') || targets[0];
    if (!tab) throw new Error('No browser tab found.');

    this._ws = new WebSocket(tab.webSocketDebuggerUrl);
    this._ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.id && this._pending.has(data.id)) {
        const { resolve } = this._pending.get(data.id);
        this._pending.delete(data.id);
        if (data.error) resolve({ error: data.error });
        else resolve(data.result);
      }
    };
    return new Promise((resolve, reject) => {
      this._ws.onopen = () => resolve();
      this._ws.onerror = () => reject(new Error('CDP WebSocket connection failed'));
    });
  }

  async _send(method, params = {}) {
    if (!this._ws || this._ws.readyState !== WebSocket.OPEN) await this._connect();
    const id = this._msgId++;
    this._ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve) => {
      this._pending.set(id, { resolve });
    });
  }

  async _evaluate(expression) {
    const result = await this._send('Runtime.evaluate', {
      expression, returnByValue: true
    });
    if (result.error) throw new Error(result.error.message);
    return result.result?.value;
  }

  async _navigate(url, waitMs = 2000) {
    await this._send('Page.enable');
    await this._send('Page.navigate', { url });
    await new Promise(r => setTimeout(r, waitMs));
    const val = await this._evaluate(
      'JSON.stringify({title: document.title, text: document.body.innerText.slice(0,10000)})'
    );
    return val ? JSON.parse(val) : { title: 'Unknown', text: '' };
  }

  async _sendExtensionMessage(action, args = {}) {
    // Connect to a page via CDP and execute DOM actions directly
    const res = await fetch(CDP_URL);
    const targets = await res.json();
    const tab = targets.find(t => t.type === 'page') || targets[0];
    if (!tab) throw new Error('No browser tab found');

    const ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = () => reject(new Error('CDP connection failed'));
    });

    let nid = 1;
    const pend = new Map();
    ws.onmessage = (ev) => {
      const d = JSON.parse(ev.data);
      if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); }
    };
    const send = (method, params = {}) => new Promise(r => {
      const id = nid++; pend.set(id, r); ws.send(JSON.stringify({ id, method, params }));
    });

    try {
      await send('Runtime.enable');
      const as = JSON.stringify(args);

      if (action === 'getContext') {
        const r = await send('Runtime.evaluate', {
          expression: 'JSON.stringify({title: document.title, url: window.location.href, text: (document.body.innerText || "").slice(0, 5000)})',
          returnByValue: true
        });
        ws.close();
        try { return { success: true, data: JSON.parse(r.result.result.value) }; } catch(e) { return { success: false, error: 'Parse failed: ' + (e.message||'') }; }
      }
      
      if (action === 'extract') {
        var selExpr = JSON.stringify(args.selector || 'body');
        const r = await send('Runtime.evaluate', {
          expression: '(function(s) { var e = s === "body" ? null : document.querySelector(s); var t = e ? (e.textContent || e.innerText) : document.body.innerText; return JSON.stringify({text: (t || "").slice(0, 10000)}); })(' + selExpr + ')',
          returnByValue: true
        });
        ws.close();
        try { return { success: true, data: JSON.parse(r.result.result.value) }; } catch(e) { return { success: false, error: 'Parse failed: ' + (e.message||'') }; }
      }
      
      if (action === 'click') {
        var selExpr = JSON.stringify(args.selector);
        const r = await send('Runtime.evaluate', {
          expression: '(function(s) { var e = document.querySelector(s); if (!e) return JSON.stringify({error: "not found"}); e.click(); return JSON.stringify({text: "clicked"}); })(' + selExpr + ')',
          returnByValue: true
        });
        ws.close();
        try { var d = JSON.parse(r.result.result.value); return d.error ? { success: false, error: d.error } : { success: true, data: d }; } catch(e) { return { success: false, error: 'Parse failed: ' + (e.message||'') }; }
      }
      
      if (action === 'type') {
        var sExpr = JSON.stringify(args.selector);
        var tExpr = JSON.stringify(args.text);
        const r = await send('Runtime.evaluate', {
          expression: '(function(s, t) { var e = document.querySelector(s); if (!e) return JSON.stringify({error:"not found"}); e.focus(); e.value = t; e.dispatchEvent(new Event("input", {bubbles:true})); e.dispatchEvent(new Event("change", {bubbles:true})); return JSON.stringify({text:"typed"}); })(' + sExpr + ', ' + tExpr + ')',
          returnByValue: true
        });
        ws.close();
        try { var d = JSON.parse(r.result.result.value); return d.error ? { success: false, error: d.error } : { success: true, data: d }; } catch(e) { return { success: false, error: 'Parse failed: ' + (e.message||'') }; }
      }

      ws.close();
      return { success: false, error: 'Unknown action: ' + action };
    } catch (err) { ws.close(); throw err; }
  }

  async _listTargets() {
    const res = await fetch(CDP_URL);
    return await res.json();
  }

  register(name, tool) { this._tools.set(name, tool); }
  get(name) { return this._tools.get(name); }
  list() { return Array.from(this._tools.values()); }

  registerDefaults() {
    // browse — Navigate to URL
    this.register('browse', {
      name: 'browse',
      description: 'Navigate to a URL and return page content',
      inputSchema: {
        type: 'object',
        properties: { url: { type: 'string', description: 'Full URL to navigate to' } },
        required: ['url']
      },
      execute: async (args) => {
        const ctx = await this._navigate(args.url);
        const text = ctx.text ? ctx.text.slice(0, 5000) : '(empty)';
        return { content: [{ type: 'text', text: 'Title: ' + (ctx.title || 'Untitled') + '\nURL: ' + args.url + '\n\n' + text }] };
      }
    });

    // screenshot — Capture visible tab (uses CDP helpers for stability)
    this.register('screenshot', {
      name: 'screenshot',
      description: 'Take a screenshot of the current tab. Pass fullPage:true to capture entire page.',
      inputSchema: { type: 'object', properties: {
        fullPage: { type: 'boolean', description: 'Capture full page content beyond viewport' }
      }, required: [] },
      execute: async (args = {}) => {
        const tab = await getActiveTab();
        if (!tab) throw new Error('No active page tab found');
        const wsUrl = normalizeCdpWsUrl(tab.webSocketDebuggerUrl, CDP_URL);
        const base64 = await captureScreenshotPng(wsUrl, { fullPage: args.fullPage === true });
        if (!base64) throw new Error('Screenshot failed: no data');
        return { content: [{ type: 'image', data: 'data:image/png;base64,' + base64, mimeType: 'image/png' }] };
      }
    });

    // click — CDP click element
    this.register('click', {
      name: 'click',
      description: 'Click an element by CSS selector',
      inputSchema: {
        type: 'object',
        properties: { selector: { type: 'string', description: 'CSS selector' } },
        required: ['selector']
      },
      execute: async (args) => {
        const s = args.selector.replace(/'/g, "\\'");
        const r = await this._evaluate("(() => { const e = document.querySelector('" + s + "'); if (!e) return 'NOT_FOUND'; e.click(); return 'CLICKED'; })()");
        if (r === 'NOT_FOUND') throw new Error('Element not found: ' + args.selector);
        return { content: [{ type: 'text', text: 'Clicked: ' + args.selector }] };
      }
    });

    // type — CDP type text
    this.register('type', {
      name: 'type',
      description: 'Type text into an input field',
      inputSchema: {
        type: 'object',
        properties: {
          selector: { type: 'string', description: 'CSS selector for input' },
          text: { type: 'string', description: 'Text to type' }
        },
        required: ['selector', 'text']
      },
      execute: async (args) => {
        const s = args.selector.replace(/'/g, "\\'");
        const t = args.text.replace(/'/g, "\\'").replace(/\\/g, '\\\\');
        const r = await this._evaluate("(() => { const e = document.querySelector('" + s + "'); if (!e) return 'NOT_FOUND'; e.value = '" + t + "'; e.dispatchEvent(new Event('input', {bubbles:true})); e.dispatchEvent(new Event('change', {bubbles:true})); return 'TYPED'; })()");
        if (r === 'NOT_FOUND') throw new Error('Element not found: ' + args.selector);
        return { content: [{ type: 'text', text: 'Typed into: ' + args.selector }] };
      }
    });

    // extract — Get text from page
    this.register('extract', {
      name: 'extract',
      description: 'Extract text from the page or a specific element',
      inputSchema: {
        type: 'object',
        properties: { selector: { type: 'string', description: 'CSS selector (use body for full page)' } },
        required: []
      },
      execute: async (args) => {
        const sel = args.selector || 'body';
        const s = sel.replace(/'/g, "\\'");
        const text = await this._evaluate("(() => { const e = document.querySelector('" + s + "'); return e ? (e.textContent || e.innerText || '').slice(0, 10000) : 'NOT_FOUND'; })()");
        if (text === 'NOT_FOUND' && sel !== 'body') throw new Error('Element not found: ' + sel);
        return { content: [{ type: 'text', text: text || '(empty)' }] };
      }
    });

    // wait — Wait for element
    this.register('wait', {
      name: 'wait',
      description: 'Wait for an element to appear',
      inputSchema: {
        type: 'object',
        properties: {
          selector: { type: 'string', description: 'CSS selector' },
          timeout: { type: 'number', description: 'Max wait in ms', default: 10000 }
        },
        required: ['selector']
      },
      execute: async (args) => {
        const s = args.selector.replace(/'/g, "\\'");
        const timeout = args.timeout || 10000;
        const start = Date.now();
        let found = false;
        while (Date.now() - start < timeout) {
          const r = await this._evaluate("!!document.querySelector('" + s + "')");
          if (r) { found = true; break; }
          await new Promise(r => setTimeout(r, 500));
        }
        return { content: [{ type: 'text', text: found ? 'Element appeared: ' + args.selector : 'Timeout: ' + args.selector }] };
      }
    });

    // auth — Start OAuth
    this.register('auth', {
      name: 'auth',
      description: 'Start OAuth flow for a connected service',
      inputSchema: {
        type: 'object',
        properties: { service: { type: 'string', enum: ['gmail', 'drive', 'calendar', 'github', 'slack'], description: 'Service to authenticate' } },
        required: ['service']
      },
      execute: async (args) => {
        await this._navigate('http://localhost:8083/auth/' + args.service);
        return { content: [{ type: 'text', text: 'Auth flow started for ' + args.service }] };
      }
    });

    // run_task — Autonomous browser agent (via 9Router)
    this.register('run_task', {
      name: 'run_task',
      description: 'Run an autonomous browser task using 9Router AI via zeschrome-mcp tools',
      inputSchema: {
        type: 'object',
        properties: {
          task: { type: 'string', description: 'Natural language browser task' },
          model: { type: 'string', description: '9Router model slug (default: groq/llama-3.3-70b-versatile)' }
        },
        required: ['task']
      },
      execute: async (args) => {
        const agent = getAgent();
        const result = await agent.run(args.task, { model: args.model });
        const text = result.success
          ? 'Task completed in ' + result.iterations + ' steps.\n' + (result.summary || '')
          : 'Task stopped: ' + (result.summary || 'max iterations reached');
        return { content: [{ type: 'text', text }] };
      }
    });

    // ============================================================
    // EXTENSION BRIDGE TOOLS — Via ZES Chrome Background SW
    // ============================================================

    // ext_click — Click element via extension MCP bridge
    this.register('ext_click', {
      name: 'ext_click',
      description: 'Click an element via the ZES Chrome extension (better event handling)',
      inputSchema: {
        type: 'object',
        properties: { selector: { type: 'string', description: 'CSS selector' } },
        required: ['selector']
      },
      execute: async (args) => {
        const r = await this._sendExtensionMessage('click', { selector: args.selector });
        if (r?.success) return { content: [{ type: 'text', text: r.data?.text || 'Clicked: ' + args.selector }] };
        throw new Error(r?.error || 'Click failed');
      }
    });

    // ext_type — Type text via extension bridge
    this.register('ext_type', {
      name: 'ext_type',
      description: 'Type text into an input field via the ZES Chrome extension',
      inputSchema: {
        type: 'object',
        properties: {
          selector: { type: 'string', description: 'CSS selector for input' },
          text: { type: 'string', description: 'Text to type' }
        },
        required: ['selector', 'text']
      },
      execute: async (args) => {
        const r = await this._sendExtensionMessage('type', { selector: args.selector, text: args.text });
        if (r?.success) return { content: [{ type: 'text', text: r.data?.text || 'Typed: ' + args.selector }] };
        throw new Error(r?.error || 'Type failed');
      }
    });

    // ext_extract — Extract text via extension bridge
    this.register('ext_extract', {
      name: 'ext_extract',
      description: 'Extract text from page or element via the ZES Chrome extension',
      inputSchema: {
        type: 'object',
        properties: { selector: { type: 'string', description: 'CSS selector (body for full page)' } },
        required: []
      },
      execute: async (args) => {
        const r = await this._sendExtensionMessage('extract', { selector: args.selector || 'body' });
        if (r?.success) return { content: [{ type: 'text', text: r.data?.text || '(empty)' }] };
        throw new Error(r?.error || 'Extract failed');
      }
    });

    // ext_getContext — Full page context via extension
    this.register('ext_getContext', {
      name: 'ext_getContext',
      description: 'Get full page context (title, URL, text) via extension',
      inputSchema: { type: 'object', properties: {}, required: [] },
      execute: async (args) => {
        const r = await this._sendExtensionMessage('getContext', {});
        if (r?.success && r.data) {
          return { content: [{ type: 'text', text: 'Title: ' + (r.data.title || '?') + '\nURL: ' + (r.data.url || '?') + '\n\n' + (r.data.text || '').slice(0, 3000) }] };
        }
        throw new Error(r?.error || 'Context failed');
      }
    });

    // list_tabs — List open Chrome tabs
    this.register('list_tabs', {
      name: 'list_tabs',
      description: 'List all open Chrome tabs',
      inputSchema: { type: 'object', properties: {}, required: [] },
      execute: async () => {
        const targets = await this._listTargets();
        const tabs = targets.filter(t => t.type === 'page')
          .map(t => '  ' + (t.id?.slice(0, 16) || '?') + '... | ' + (t.url?.slice(0, 80) || '?') + ' | ' + (t.title?.slice(0, 50) || '?'));
        return { content: [{ type: 'text', text: 'Chrome Tabs (' + tabs.length + '):\n' + (tabs.length ? tabs.join('\n') : '(none)') }] };
      }
    });

    // ext_agent — Check extension agent state
    this.register('ext_agent', {
      name: 'ext_agent',
      description: 'Check ZES Chrome extension agent state',
      inputSchema: { type: 'object', properties: {}, required: [] },
      execute: async () => {
        const targets = await this._listTargets();
        const sw = targets.find(t => t.type === 'service_worker');
        const extId = sw ? (sw.url?.match(/chrome-extension:\/\/([^\/]+)/)?.[1] || 'unknown') : 'not found';
        return { content: [{ type: 'text', text: 'Extension: ZES Chrome\n  Active: ' + (sw ? 'yes' : 'no') + '\n  SW ID: ' + extId }] };
      }
    });
  }
}
