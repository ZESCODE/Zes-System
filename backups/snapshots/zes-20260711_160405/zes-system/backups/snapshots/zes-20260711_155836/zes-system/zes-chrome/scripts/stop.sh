#!/data/data/com.termux/files/usr/bin/bash
if [ -f /tmp/zeschrome-mcp.pid ]; then
    kill $(cat /tmp/zeschrome-mcp.pid) 2>/dev/null
    rm /tmp/zeschrome-mcp.pid
    echo "MCP Server stopped"
else
    echo "No MCP Server running"
fi
