#!/usr/bin/env node
import http from "http";
const PORT = 5905, RHOST = "127.0.0.1", RPORT = 20128, RKEY = "sk-d25ec2e336a68df0-trhjvq-621c9b41";

function proxy(method, path, headers, body, res) {
  const opts = { hostname: RHOST, port: RPORT, path, method, headers: { "x-api-key": RKEY } };
  if (method === "POST") opts.headers["Content-Type"] = "application/json";
  if (body) opts.headers["Content-Length"] = Buffer.byteLength(body);
  if (headers["anthropic-version"]) opts.headers["anthropic-version"] = headers["anthropic-version"];
  const pr = http.request(opts, (pr2) => {
    if ((pr2.headers["content-type"]||"").includes("event-stream")) {
      res.writeHead(pr2.statusCode, {"Content-Type":"text/event-stream","Cache-Control":"no-cache","Connection":"keep-alive","Access-Control-Allow-Origin":"*"});
      pr2.pipe(res);
    } else {
      let d=""; pr2.on("data",c=>d+=c); pr2.on("end",()=>{res.writeHead(pr2.statusCode,{"Content-Type":"application/json"});res.end(d);});
    }
  });
  pr.on("error",e=>{res.writeHead(502);res.end(JSON.stringify({error:e.message}));});
  if (body) pr.write(body);
  pr.end();
}

http.createServer((req, res) => {
  res.setHeader("Access-Control-Allow-Origin","*");
  if (req.method==="OPTIONS") { res.writeHead(204); res.end(); return; }
  const path = new URL(req.url,`http://${req.headers.host}`).pathname;
  if (req.method==="GET") {
    if (path==="/v1/me"||path==="/me") { res.writeHead(200,{"Content-Type":"application/json"}); res.end(JSON.stringify({id:"zes",isAuthenticated:true})); return; }
    proxy("GET",path,req.headers,null,res); return;
  }
  let b=""; req.on("data",c=>b+=c); req.on("end",()=>proxy("POST",path,req.headers,b||undefined,res));
}).listen(PORT, "127.0.0.1", () => console.log(`Proxy on :${PORT} (127.0.0.1)`));
