#!/usr/bin/env node
/**
 * ZES Claude Proxy v2 — Enhanced streaming proxy for Claude Code -> 9Router
 * Features: streaming error recovery, timeout handling, auth passthrough, retry
 */
import http from "http";

const PORT = 5905;
const RHOST = "127.0.0.1";
const RPORT = 20128;
const DEFAULT_KEY = "sk-d25ec2e336a68df0-trhjvq-621c9b41";
const TIMEOUT = 60000;

function proxy(method, path, headers, body, res, retries) {
  if (retries === undefined) retries = 1;
  const apiKey = headers["x-api-key"] || (headers["authorization"] || "").replace("Bearer ", "") || DEFAULT_KEY;
  
  const opts = {
    hostname: RHOST, port: RPORT, path, method,
    timeout: TIMEOUT,
    headers: { "x-api-key": apiKey }
  };
  if (method === "POST") opts.headers["Content-Type"] = "application/json";
  if (body) opts.headers["Content-Length"] = Buffer.byteLength(body);
  if (headers["anthropic-version"]) opts.headers["anthropic-version"] = headers["anthropic-version"];

  const pr = http.request(opts, (pr2) => {
    const isStream = (pr2.headers["content-type"] || "").includes("event-stream")
      || (pr2.headers["transfer-encoding"] || "").includes("chunked");
    
    if (isStream) {
      res.writeHead(pr2.statusCode, {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "X-Accel-Buffering": "no",
      });
      pr2.on("data", chunk => { try { res.write(chunk); } catch(e) {} });
      pr2.on("end", () => { try { res.end(); } catch(e) {} });
      pr2.on("error", (e) => {
        try { res.write("data: " + JSON.stringify({error: "Stream error: " + e.message}) + "\n\n"); res.end(); } catch(ex) {}
      });
    } else {
      let d = "";
      pr2.on("data", c => d += c);
      pr2.on("end", () => {
        const ct = pr2.headers["content-type"] || "application/json";
        res.writeHead(pr2.statusCode, { "Content-Type": ct, "Access-Control-Allow-Origin": "*" });
        res.end(d);
      });
    }
  });

  pr.on("timeout", () => {
    pr.destroy();
    if (!res.headersSent) {
      res.writeHead(504, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Upstream timeout", timeout: TIMEOUT }));
    }
  });

  pr.on("error", (e) => {
    if (retries > 0 && (e.code === "ECONNRESET" || e.code === "ECONNREFUSED")) {
      proxy(method, path, headers, body, res, retries - 1);
      return;
    }
    if (!res.headersSent) {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Proxy error: " + e.message, code: e.code }));
    }
  });

  if (body) pr.write(body);
  pr.end();
}

http.createServer((req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  if (req.method === "OPTIONS") { res.writeHead(204); res.end(); return; }

  const url = new URL(req.url, "http://" + (req.headers.host || "localhost"));
  const path = url.pathname;

  if (req.method === "GET") {
    if (path === "/v1/me" || path === "/me") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ id: "zes", isAuthenticated: true }));
      return;
    }
    proxy("GET", path, req.headers, null, res);
    return;
  }

  let b = "";
  req.on("data", c => { b += c; if (b.length > 1e7) req.destroy(); });
  req.on("end", () => proxy("POST", path, req.headers, b || undefined, res));
}).listen(PORT, "127.0.0.1", () => {
  console.log("ZES Claude Proxy v2 on :" + PORT + " -> 9Router :" + RPORT);
  console.log("  Timeout: " + (TIMEOUT/1000) + "s · Retries: 1");
});
