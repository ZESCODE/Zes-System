#!/data/data/com.termux/files/usr/bin/bash
echo "Starting zesChrome MCP Server on :5901..."
cd ~/Zes-System/zes-chrome/mcp-server
node server.js &
echo $! > /tmp/zeschrome-mcp.pid
echo "MCP Server started (PID: $(cat /tmp/zeschrome-mcp.pid))"
