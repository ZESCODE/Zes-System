// CDP Helpers — Chrome DevTools Protocol utilities
// Ported from OpenClaw's cdp.ts / cdp.helpers.ts patterns
// WS management, screenshot capture, target filtering, navigation guard

import WebSocket from 'ws';

const CDP_URL = 'http://localhost:9222/json';

// ── URL helpers ──────────────────────────────────────────────

export function isWebSocketUrl(url) {
  try { const p = new URL(url); return p.protocol === 'ws:' || p.protocol === 'wss:'; }
  catch { return false; }
}

export function isDirectCdpWebSocketEndpoint(url) {
  if (!isWebSocketUrl(url)) return false;
  try {
    const p = new URL(url);
    return /\/devtools\/(?:browser|page|worker|shared_worker|service_worker)\/[^/]/i.test(p.pathname);
  } catch { return false; }
}

export async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`CDP HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

function isLoopbackHost(hostname) {
  return ['127.0.0.1', 'localhost', '::1', '0.0.0.0', '[::]'].includes(hostname);
}

export function normalizeCdpWsUrl(wsUrl, cdpUrl) {
  const ws = new URL(wsUrl);
  const cdp = new URL(cdpUrl);
  const isWildcardBind = ws.hostname === '0.0.0.0' || ws.hostname === '[::]';
  if ((isLoopbackHost(ws.hostname) || isWildcardBind) && !isLoopbackHost(cdp.hostname)) {
    ws.hostname = cdp.hostname;
    ws.port = cdp.port || (cdp.protocol === 'https:' ? '443' : '80');
    ws.protocol = cdp.protocol === 'https:' ? 'wss:' : 'ws:';
  } else if (isLoopbackHost(ws.hostname) && isLoopbackHost(cdp.hostname)) {
    ws.hostname = cdp.hostname;
  }
  if (cdp.protocol === 'https:' && ws.protocol === 'ws:') ws.protocol = 'wss:';
  if (!ws.username && !ws.password && (cdp.username || cdp.password)) {
    ws.username = cdp.username;
    ws.password = cdp.password;
  }
  return ws.toString();
}

// ── WebSocket session management ────────────────────────────

/**
 * Execute a function with a CDP WebSocket connection.
 * The fn receives a send(method, params) function that returns promises.
 */
export function withCdpSocket(wsUrl, fn, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let msgId = 1;
    const pending = new Map();
    const timer = setTimeout(() => {
      ws.close();
      reject(new Error(`CDP socket timeout after ${timeoutMs}ms`));
    }, timeoutMs);

    ws.on('open', () => {
      clearTimeout(timer);
      const send = (method, params = {}) => new Promise((r, rej) => {
        const id = msgId++;
        pending.set(id, r);
        ws.send(JSON.stringify({ id, method, params }));
      });
      try { Promise.resolve(fn(send)).then(resolve).catch(reject); }
      catch (err) { reject(err); }
    });
    ws.on('message', (data) => {
      let msg;
      try { msg = JSON.parse(data.toString()); } catch { return; }
      if (msg.id && pending.has(msg.id)) {
        pending.get(msg.id)(msg);
        pending.delete(msg.id);
      }
    });
    ws.on('error', (err) => { clearTimeout(timer); reject(err); });
    ws.on('close', () => { clearTimeout(timer); });
  });
}

// ── Screenshot capture ───────────────────────────────────────

export async function captureScreenshot(wsUrl, opts = {}) {
  const { fullPage, format = 'png', quality } = opts;

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
          expression: 'JSON.stringify({w:innerWidth,h:innerHeight,dpr:devicePixelRatio})',
          returnByValue: true,
        });
        let v = { w: 1280, h: 720, dpr: 1 };
        try { v = JSON.parse(vpResult?.result?.value || '{}'); } catch {}
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
      ...(quality !== undefined ? { quality: Math.max(0, Math.min(100, quality)) } : {}),
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

export async function captureScreenshotPng(wsUrl, opts = {}) {
  return captureScreenshot(wsUrl, { ...opts, format: 'png' });
}

// ── Target management ──────────────────────────────────────

export async function listTargets() {
  return fetchJson(CDP_URL);
}

export async function getActiveTab() {
  const targets = await listTargets();
  return targets.find(t => t.type === 'page') || targets[0] || null;
}

// ── Page evaluation ─────────────────────────────────────────

export async function evaluateOnPage(wsUrl, expression) {
  return withCdpSocket(wsUrl, async (send) => {
    const result = await send('Runtime.evaluate', {
      expression,
      returnByValue: true,
    });
    return result?.result?.value;
  });
}
