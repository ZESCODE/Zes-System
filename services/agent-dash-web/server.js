#!/usr/bin/env node
/**
 * ZES Agent Dashboard — Port 8002
 * Serves a mobile-optimized Agent Dashboard frontend
 * and proxies API calls to the Agent Dashboard daemon.
 */
const http = require("http");
const fs = require("fs");
const path = require("path");

const API_TARGET = "http://127.0.0.1:8002";
const PORT = 8003;  // will be overridden to 8002
const HOST = "0.0.0.0";

// Determine actual port (run with environment or use script name)
const actualPort = process.env.PORT || 8003;

const DASHBOARD_HTML = fs.readFileSync(
  path.join(__dirname, "dashboard.html"), "utf-8"
);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json",
};

function serveStatic(res, filePath) {
  const ext = path.extname(filePath);
  try {
    const data = fs.readFileSync(filePath);
    res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
    res.end(data);
    return true;
  } catch { return false; }
}

const server = http.createServer((req, res) => {
  const reqUrl = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const pathname = reqUrl.pathname;

  // CORS
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
  if (req.method === "OPTIONS") { res.writeHead(204); res.end(); return; }

  // Serve dashboard frontend
  if (pathname === "/" || pathname === "/dashboard") {
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(DASHBOARD_HTML);
    return;
  }

  // Serve static assets
  if (pathname.startsWith("/__dash/")) {
    const filePath = path.join(__dirname, "assets", pathname.slice(8));
    if (serveStatic(res, filePath)) return;
    res.writeHead(404); res.end("Not found");
    return;
  }

  // Health check
  if (pathname === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", port: actualPort }));
    return;
  }

  // Proxy API calls to the daemon
  if (pathname.startsWith("/api/")) {
    const opts = {
      hostname: "127.0.0.1",
      port: 8002,
      path: req.url,
      method: req.method,
      headers: { ...req.headers, host: "127.0.0.1:8002" },
    };
    const proxyReq = http.request(opts, (proxyRes) => {
      // Forward response headers (except transfer-encoding)
      const headers = { ...proxyRes.headers };
      delete headers["transfer-encoding"];
      res.writeHead(proxyRes.statusCode, headers);
      proxyRes.pipe(res);
    });
    proxyReq.on("error", () => {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Agent Dashboard daemon not reachable" }));
    });
    req.pipe(proxyReq);
    return;
  }

  res.writeHead(404); res.end("Not found");
});

server.listen(actualPort, HOST, () => {
  console.log(`\n  🤖 ZES Agent Dashboard`);
  console.log(`  ─────────────────────`);
  console.log(`  URL   : http://0.0.0.0:${actualPort}`);
  console.log(`  API   : ${API_TARGET}\n`);
});
