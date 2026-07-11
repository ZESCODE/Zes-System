# Infrastructure Overview

## Current State (July 2026)

### OS
- **Host:** Android aarch64 (Termux)
- **Container:** Debian via proot-distro (for glibc binaries)
- **Init:** runit (runsv) for service supervision

### Networking
- All services on localhost (127.0.0.1)
- Tor SOCKS5 proxy on :9050 for anonymized routing
- Headless Chromium on :9222 for browser automation

### 9Router (v0.5.20)
- 18 AI providers configured
- Single endpoint: http://localhost:20128/v1
- OpenAI-compatible API format
- Auto-fallback between providers on rate limits

### Codex
- Routes through 9Router (not directly to OpenAI)
- Model: groq/llama-3.3-70b-versatile (fastest inference)
- Subagent: gh/gpt-5.4-mini-free-auto (GitHub Copilot free tier)
- 7 personal skills + superpowers plugin loaded
