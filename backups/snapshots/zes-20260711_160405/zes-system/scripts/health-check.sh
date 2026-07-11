#!/bin/bash
# ZES System Health Check
echo "=== ZES System Health Check ==="
echo ""

# Check services
echo "--- Services ---"
for svc in codex ttyd socat hermes opencode tor sshd; do
  if command -v sv &>/dev/null; then
    sv status $svc 2>/dev/null | grep -q "run:" && echo "  🟢 $svc" || echo "  🔴 $svc"
  fi
done

# Check ports
echo ""
echo "--- Ports ---"
for pair in "Codex:5900" "Hermes:8787" "9Router:20128" "OpenCode:9876" "Dashboard:8083" "Tor:9050" "Browser:9222"; do
  name="${pair%%:*}"
  port="${pair##*:}"
  python3 -c "import socket; s=socket.socket(); s.settimeout(0.3); r=s.connect_ex(('127.0.0.1',$port)); print('  🟢' if r==0 else '  🔴', '$name', ':$port'); s.close()" 2>/dev/null
done

# Check 9router
echo ""
echo "--- 9Router Providers ---"
python3 -c "
import os,hashlib,json,urllib.request
d=os.path.expanduser('~/.9router')
mid=open(d+'/machine-id').read().strip()
sec=open(d+'/auth/cli-secret').read().strip()
tok=hashlib.sha256((mid+'9r-cli-auth'+sec).encode()).hexdigest()[:16]
r=urllib.request.Request('http://localhost:20128/api/providers')
r.add_header('x-9r-cli-token',tok)
data=json.loads(urllib.request.urlopen(r,timeout=3).read())
active=sum(1 for c in data.get('connections',[]) if c.get('isActive'))
print(f'  {len(data.get(\"connections\",[]))} connections, {active} active')
" 2>/dev/null || echo "  ❌ 9Router not responding"

# Check Gmail
echo ""
echo "--- Gmail ---"
if command -v gmail-tool &>/dev/null; then
  gmail-tool status 2>/dev/null | head -3
fi
