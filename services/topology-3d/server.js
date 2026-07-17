#!/usr/bin/env node
const http = require("http");
const fs = require("fs");
const path = require("path");
const PORT = 19996;
const FILE = path.join(__dirname, "index.html");
http.createServer((req, res) => {
  if (req.url === "/" || req.url === "/index.html") {
    const html = fs.readFileSync(FILE, "utf-8");
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(html);
  } else {
    res.writeHead(404); res.end("Not found");
  }
}).listen(PORT, "127.0.0.1", () => {
  console.log("ZES 3D Topology at http://127.0.0.1:" + PORT + "/");
});
