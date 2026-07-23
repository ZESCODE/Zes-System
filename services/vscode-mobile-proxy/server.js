#!/usr/bin/env node
/**
 * VS Code Mobile Proxy — Mobile-optimized wrapper for VS Code Server
 * Panel on top, code editor below, one-column mobile layout
 * Proxies VS Code Server at :8000
 */
const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = 8081;
const VSCODE_URL = "http://127.0.0.1:8000";

// Mobile-optimized wrapper HTML
const WRAPPER_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes, viewport-fit=cover">
<title>ZES Code — Mobile</title>
<style>
:root{--color-primary:#6366f1;--color-secondary:#06b6d4;--color-success:#10b981;--color-danger:#ef4444;--glass-bg:#0f172abf;--glass-border:#6366f133;--color-text:#f1f5f9;--color-text-muted:#64748b;--bg-base:#020617;--bg-input:#1e293b99;--font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;--text-xs:.7rem;--text-sm:.875rem;--radius-sm:.375rem;--radius-md:.5rem;--radius-lg:.75rem;--radius-full:9999px;--transition-fast:.15s ease;--z-sticky:200;--z-modal:300}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#1e1e1e;font-family:var(--font-family);touch-action:none;position:fixed;top:0;left:0;right:0;bottom:0;color:var(--color-text)}
#panel-bar{position:fixed;top:0;left:0;right:0;z-index:99999;display:flex;align-items:center;gap:4px;padding:2px 8px;height:36px;background:var(--glass-bg);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border-bottom:1px solid var(--glass-border);transition:transform .25s ease}
#panel-bar.hidden{transform:translateY(-100%)}
.pb-btn{display:flex;align-items:center;gap:4px;padding:4px 10px;border-radius:6px;border:none;background:transparent;color:#888;font-size:12px;cursor:pointer;white-space:nowrap}
.pb-btn:hover,.pb-btn.active{color:#fff;background:var(--color-primary-light)}
.pb-brand{display:flex;align-items:center;gap:6px;margin-right:4px;padding:2px 6px;border-radius:4px;background:linear-gradient(90deg,#6366f1,#06b6d4);color:#fff;font-weight:700;font-size:11px;border:none;cursor:pointer}
.pb-spacer{flex:1}
#code-frame{width:100%;flex:1;border:none;margin-top:36px;background:#1e1e1e}
@media(max-width:480px){.pb-btn{padding:4px 6px;font-size:11px}.pb-hide-mobile{display:none}}
</style>
</head>
<body>
<div id="panel-bar">
  <button class="pb-brand" onclick="window.location.href=\'http://localhost:8083\'">ZES</button>
  <button class="pb-btn active" onclick="updateView(\'explorer\')">📁</button>
  <button class="pb-btn" onclick="updateView(\'search\')">🔍</button>
  <button class="pb-btn" onclick="updateView(\'source\')">📝</button>
  <button class="pb-btn pb-hide-mobile" onclick="updateView(\'terminal\')">⌨️</button>
  <div class="pb-spacer"></div>
  <button class="pb-btn" onclick="togglePanel()">▽</button>
</div>
<iframe id="code-frame" src="${VSCODE_URL}" allow="clipboard-read;clipboard-write"></iframe>
<script>
function updateView(view){document.querySelectorAll(".pb-btn").forEach(b=>b.classList.remove("active"));event.target.classList.add("active");var f=document.getElementById("code-frame");var u={explorer:"${VSCODE_URL}",search:"${VSCODE_URL}/?view=search",source:"${VSCODE_URL}/?view=editor",terminal:"http://localhost:7173/"};f.src=u[view]||"${VSCODE_URL}"}
function togglePanel(){document.getElementById("panel-bar").classList.toggle("hidden")}
</script>
</body>
</html>`;

const server = http.createServer((req, res) => {
  if (req.url === "/" || req.url === "/index.html") {
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(WRAPPER_HTML);
  } else {
    res.writeHead(302, { "Location": VSCODE_URL + req.url });
    res.end();
  }
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`VS Code Mobile Proxy on :${PORT} → ${VSCODE_URL}`);
});
