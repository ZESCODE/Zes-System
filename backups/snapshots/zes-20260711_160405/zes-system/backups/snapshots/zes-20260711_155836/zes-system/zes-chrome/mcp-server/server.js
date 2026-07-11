// zesChrome MCP Server — Codex ↔ Chrome bridge via CDP
// Runs on :5901

import http from 'http';
import { ToolRegistry } from './tools.js';
import { captureScreenshot, normalizeCdpWsUrl, getActiveTab, listTargets } from './cdp-helpers.js';

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

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // Health check
  if (req.url === '/health' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', port: PORT }));
    return;
  }

  // MCP endpoint
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

  // Tool-specific REST shortcuts
  if (req.url.startsWith('/api/') && req.method === 'POST') {
    const toolName = req.url.slice(5); // /api/browse -> browse
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const tool = tools.get(toolName);
        if (!tool) throw new Error(`Unknown tool: ${toolName}`);
        const args = body ? JSON.parse(body) : {};
        const result = await tool.execute(args);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // CDP screenshot endpoint (uses OpenClaw-style CDP helpers)
  if (req.url === '/api/cdp/screenshot' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const args = body ? JSON.parse(body) : {};
        const tab = await getActiveTab();
        if (!tab) throw new Error('No active page tab');
        const wsUrl = normalizeCdpWsUrl(tab.webSocketDebuggerUrl, 'http://localhost:9222');
        const base64 = await captureScreenshot(wsUrl, { fullPage: args.fullPage, format: 'png' });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, data: base64 }));
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // CDP targets list endpoint
  if (req.url === '/api/cdp/targets' && req.method === 'GET') {
    try {
      const targets = await listTargets();
      const pages = targets.filter(t => t.type === 'page').map(t => ({
        id: t.id, title: t.title, url: t.url,
      }));
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, targets: pages }));
    } catch (err) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`ZES Chrome MCP Server`);
  console.log(`  Port: :${PORT}`);
  console.log(`  MCP:  http://localhost:${PORT}/mcp`);
  console.log(`  REST: http://localhost:${PORT}/api/<tool>`);
  console.log(`  CDP:  http://localhost:9222`);
});
