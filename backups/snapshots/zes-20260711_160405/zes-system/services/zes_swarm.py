#!/usr/bin/env python3
"""ZES Swarm Orchestrator — multi-agent workflows via 9Router (not Ollama).
Run: python3 zes_swarm.py [--port 5030]
"""
from __future__ import annotations
import argparse, json, os, requests, sys
from dataclasses import dataclass, asdict
from typing import Any
from http.server import HTTPServer, BaseHTTPRequestHandler

ROUTER_BASE = "http://localhost:20128/v1"
TOKEN_CMD = "python3 -c \"import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])\""

def get_token():
    import subprocess
    r = subprocess.run(["bash", "-c", TOKEN_CMD], capture_output=True, text=True)
    return r.stdout.strip()

@dataclass
class Agent:
    name: str
    role: str
    model: str
    system_prompt: str

REGISTRY = {
    "planner": Agent("planner", "Plans and decomposes tasks", "gh/claude-sonnet-4.6",
        "You are a strategic planner. Break down complex requests into actionable steps."),
    "coder": Agent("coder", "Writes and reviews code", "deepseek-v4-flash",
        "You are a senior software engineer. Write clean, correct code."),
    "reviewer": Agent("reviewer", "Reviews and critiques outputs", "gh/claude-sonnet-4.5",
        "You are a code reviewer. Find bugs, suggest improvements."),
    "writer": Agent("writer", "Writes documentation", "groq/llama-3.3-70b",
        "You are a technical writer. Produce clear documentation."),
    "summarizer": Agent("summarizer", "Summarizes contexts", "gemini/gemini-2.5-flash",
        "Summarize key points clearly and concisely."),
}

def call_9router(model: str, prompt: str, system: str) -> str:
    token = get_token()
    headers = {"x-9r-cli-token": token, "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 4096
    }
    try:
        resp = requests.post(f"{ROUTER_BASE}/chat/completions", json=payload, headers=headers, timeout=120)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        return f"[Error {resp.status_code}: {resp.text[:200]}]"
    except Exception as e:
        return f"[Error: {e}]"

class SwarmHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_json({"swarm": "ZES Swarm Orchestrator", "agents": list(REGISTRY.keys()), "routes": ["/api/swarm/run", "/api/swarm/agents"]})
        elif self.path == "/api/swarm/agents":
            self.send_json({k: {"name": v.name, "role": v.role, "model": v.model} for k, v in REGISTRY.items()})
        elif self.path.startswith("/api/swarm/run/"):
            agent_id = self.path.split("/")[-1]
            query = self.path.split("?q=")[-1] if "?q=" in self.path else ""
            import urllib.parse
            query = urllib.parse.unquote(query)
            agent = REGISTRY.get(agent_id)
            if not agent:
                self.send_json({"error": f"Agent '{agent_id}' not found"}, 404)
                return
            result = call_9router(agent.model, query or "Execute your role on the current task.", agent.system_prompt)
            self.send_json({"agent": agent_id, "model": agent.model, "result": result})
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        if self.path == "/api/swarm/chain":
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len)) if content_len else {}
            steps = body.get("steps", ["planner", "coder", "reviewer"])
            task = body.get("task", "")
            results = {}
            for aid in steps:
                agent = REGISTRY.get(aid)
                if not agent:
                    continue
                context = f"Task: {task}\nPrevious output:\n{json.dumps(results, indent=2)}" if results else task
                result = call_9router(agent.model, context, agent.system_prompt)
                results[aid] = result
            self.send_json({"task": task, "chain": steps, "results": results})
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5030)
    args = parser.parse_args()
    srv = HTTPServer(("0.0.0.0", args.port), SwarmHandler)
    print(f"🔄 ZES Swarm Orchestrator → http://localhost:{args.port}")
    print(f"   Agents: {', '.join(REGISTRY.keys())}")
    print(f"   Chain: POST /api/swarm/chain")
    srv.serve_forever()

if __name__ == "__main__":
    main()
