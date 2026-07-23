// CDP Browser Skill — Chrome DevTools Protocol browser automation
// Reuses cdp-helpers.js for WebSocket management

import { withCdpSocket, listTargets, captureScreenshot, evaluateOnPage } from "../cdp-helpers.js";

const CDP_HTTP = "http://localhost:9222/json";

export class CDPSkill {
  name = "cdp";
  description = "Chrome browser automation via CDP";

  async _getWsUrl() {
    const targets = await listTargets();
    const tab = targets.find(t => t.type === "page") || targets[0];
    if (!tab) throw new Error("No browser tab found on " + CDP_HTTP);
    return tab.webSocketDebuggerUrl;
  }

  tools() {
    return [
      {
        name: "navigate",
        description: "Navigate Chrome to a URL and wait for page load",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string", description: "Full URL to navigate to" },
            waitMs: { type: "number", description: "Milliseconds to wait after navigation", default: 3000 }
          },
          required: ["url"]
        }
      },
      {
        name: "screenshot",
        description: "Capture screenshot of current page as base64 PNG",
        inputSchema: {
          type: "object",
          properties: {
            fullPage: { type: "boolean", description: "Capture full page (including scroll)", default: false },
            quality: { type: "number", description: "JPEG quality 0-100 (PNG ignores)", minimum: 0, maximum: 100 }
          }
        }
      },
      {
        name: "evaluate",
        description: "Execute JavaScript in the page context and return the result",
        inputSchema: {
          type: "object",
          properties: {
            expression: { type: "string", description: "JavaScript expression to evaluate" }
          },
          required: ["expression"]
        }
      },
      {
        name: "extract",
        description: "Extract text content from the page or a specific element",
        inputSchema: {
          type: "object",
          properties: {
            selector: { type: "string", description: "CSS selector (omit for full page text)" },
            maxLength: { type: "number", description: "Maximum text length to return", default: 10000 }
          }
        }
      },
      {
        name: "click",
        description: "Click an element on the page by CSS selector",
        inputSchema: {
          type: "object",
          properties: {
            selector: { type: "string", description: "CSS selector for the element to click" }
          },
          required: ["selector"]
        }
      },
      {
        name: "type",
        description: "Type text into an input field",
        inputSchema: {
          type: "object",
          properties: {
            selector: { type: "string", description: "CSS selector for the input element" },
            text: { type: "string", description: "Text to type" }
          },
          required: ["selector", "text"]
        }
      },
      {
        name: "get_console_logs",
        description: "Get recent console log entries from the page",
        inputSchema: { type: "object", properties: {}, required: [] }
      },
      {
        name: "get_performance",
        description: "Get performance metrics (JS heap, script duration, layout count)",
        inputSchema: { type: "object", properties: {}, required: [] }
      },
      {
        name: "list_tabs",
        description: "List all open Chrome tabs/ pages",
        inputSchema: { type: "object", properties: {}, required: [] }
      },
      {
        name: "get_accessibility",
        description: "Get accessibility tree for the current page",
        inputSchema: {
          type: "object",
          properties: {
            depth: { type: "number", description: "Tree depth to traverse", default: 4 }
          }
        }
      },
      {
        name: "clear_cache",
        description: "Clear browser cache and cookies",
        inputSchema: { type: "object", properties: {}, required: [] }
      }
    ];
  }

  async navigate(args) {
    const wsUrl = await this._getWsUrl();
    return withCdpSocket(wsUrl, async (send) => {
      await send("Page.enable");
      await send("Page.navigate", { url: args.url });
      await new Promise(r => setTimeout(r, args.waitMs || 3000));
      const state = await send("Runtime.evaluate", {
        expression: "JSON.stringify({ title: document.title, url: location.href, readyState: document.readyState })",
        returnByValue: true
      });
      const raw = state?.result?.result?.value;
      const data = raw ? JSON.parse(raw) : {};
      return { success: true, data };
    });
  }

  async screenshot(args) {
    const wsUrl = await this._getWsUrl();
    const data = await captureScreenshot(wsUrl, {
      format: "png",
      fullPage: args?.fullPage || false,
      quality: args?.quality
    });
    return { success: true, data, contentType: "image" };
  }

  async evaluate(args) {
    const wsUrl = await this._getWsUrl();
    return withCdpSocket(wsUrl, async (send) => {
      const result = await send("Runtime.evaluate", {
        expression: args.expression,
        returnByValue: true
      });
      const value = result?.result?.result?.value;
      if (result?.result?.exceptionDetails) {
        const exc = result.result.exceptionDetails;
        return { success: false, error: exc.text + ": " + (exc.exception?.description || ""), exception: exc };
      }
      return { success: true, data: value };
    });
  }

  async extract(args) {
    const wsUrl = await this._getWsUrl();
    const selector = args?.selector || "body";
    const maxLen = args?.maxLength || 10000;
    return withCdpSocket(wsUrl, async (send) => {
      const expr = '(function(s) { var e = document.querySelector(s); var t = e ? (e.textContent || e.innerText) : document.body.innerText; return JSON.stringify({ text: (t || "").slice(0, ' + maxLen + ') }); })(' + JSON.stringify(selector) + ')';
      const result = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
      if (result?.result?.exceptionDetails) {
        const exc = result.result.exceptionDetails;
        return { success: false, error: exc.text + ": " + (exc.exception?.description || ""), exception: exc };
      }
      const rawVal = result?.result?.result?.value;
      if (!rawVal) return { success: true, data: { text: "" } };
      try {
        return { success: true, data: JSON.parse(rawVal) };
      } catch {
        return { success: true, data: { text: rawVal } };
      }
    });
  }

  async click(args) {
    const wsUrl = await this._getWsUrl();
    return withCdpSocket(wsUrl, async (send) => {
      const expr = '(function(s) { var e = document.querySelector(s); if (!e) return JSON.stringify({ error: "not found" }); e.click(); return JSON.stringify({ clicked: true }); })(' + JSON.stringify(args.selector) + ')';
      const result = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
      if (result?.result?.exceptionDetails) {
        const exc = result.result.exceptionDetails;
        return { success: false, error: exc.text + ": " + (exc.exception?.description || ""), exception: exc };
      }
      const rawVal = result?.result?.result?.value;
      if (!rawVal) return { success: true, data: { clicked: true }, note: "no value returned" };
      try {
        return { success: true, data: JSON.parse(rawVal) };
      } catch {
        return { success: true, data: { clicked: true } };
      }
    });
  }

  async type(args) {
    const wsUrl = await this._getWsUrl();
    return withCdpSocket(wsUrl, async (send) => {
      const expr = '(function(s, t) { var e = document.querySelector(s); if (!e) return JSON.stringify({ error: "not found" }); e.value = t; e.dispatchEvent(new Event("input", { bubbles: true })); return JSON.stringify({ typed: true }); })(' + JSON.stringify(args.selector) + ', ' + JSON.stringify(args.text) + ')';
      const result = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
      if (result?.result?.exceptionDetails) {
        const exc = result.result.exceptionDetails;
        return { success: false, error: exc.text + ": " + (exc.exception?.description || ""), exception: exc };
      }
      const rawVal = result?.result?.result?.value;
      if (!rawVal) return { success: true, data: { typed: true }, note: "no value returned" };
      try {
        return { success: true, data: JSON.parse(rawVal) };
      } catch {
        return { success: true, data: { typed: true } };
      }
    });
  }

  async get_console_logs(args) {
    const wsUrl = await this._getWsUrl();
    return withCdpSocket(wsUrl, async (send) => {
      await send("Console.enable");
      await send("Log.enable");
      await new Promise(r => setTimeout(r, 300));
      const result = await send("Runtime.evaluate", {
        expression: "JSON.stringify(window.__CDP_CONSOLE_LOGS__ || [])",
        returnByValue: true
      });
      const rawConsole = result?.result?.result?.value;
      return { success: true, data: rawConsole ? JSON.parse(rawConsole) : [] };
    });
  }

  async get_performance(args) {
    const wsUrl = await this._getWsUrl();
    return withCdpSocket(wsUrl, async (send) => {
      const perf = await send("Performance.getMetrics");
      const metrics = perf?.result?.metrics || [];
      const map = {};
      for (const m of metrics) map[m.name] = m.value;
      return { success: true, data: map };
    });
  }

  async list_tabs(args) {
    const targets = await listTargets();
    const tabs = targets.filter(t => t.type === "page").map(t => ({
      id: (t.id || "").slice(0, 16),
      title: t.title || "",
      url: (t.url || "").slice(0, 120),
      wsUrl: t.webSocketDebuggerUrl || ""
    }));
    return { success: true, data: tabs };
  }

  async get_accessibility(args) {
    const wsUrl = await this._getWsUrl();
    const depth = args?.depth || 4;
    return withCdpSocket(wsUrl, async (send) => {
      const result = await send("Accessibility.getFullAXTree", {
        depth,
        fetchRelatives: true
      });
      const nodes = result?.result?.nodes || [];
      const tree = [];
      for (const node of nodes) {
        const nameAttr = node.attributes?.find(a => a.name === "name");
        const roleAttr = node.attributes?.find(a => a.name === "role");
        tree.push({
          role: roleAttr?.value || "",
          name: nameAttr?.value || "",
          ignored: node.ignored || false
        });
      }
      return { success: true, data: tree.filter(n => !n.ignored && n.role) };
    });
  }

  async clear_cache(args) {
    const wsUrl = await this._getWsUrl();
    return withCdpSocket(wsUrl, async (send) => {
      await send("Network.clearBrowserCache");
      await send("Network.clearBrowserCookies");
      return { success: true, data: { cacheCleared: true, cookiesCleared: true } };
    });
  }
}
