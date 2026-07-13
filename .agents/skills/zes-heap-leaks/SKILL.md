---
name: zes-heap-leaks
description: "Investigate memory growth in ZES services: Node.js processes, Python daemons, MCP server, Hermes gateway."
---

# ZES Heap Leaks

Use this skill when ZES services show growing RSS, OOM kills, or degraded
performance over time.

## Workflow

1. Identify the affected process:
   ```bash
   ps aux | grep -E "node|python|codex|claude" | sort -k4 -rn
   ```

2. Check RSS trend:
   ```bash
   # Take 3 readings, 30s apart
   for i in 1 2 3; do
     ps -o pid,rss,%mem,cmd -p <PID>
     sleep 30
   done
   ```

3. For Node.js services (Dashboard, MCP, Hermes):
   ```bash
   # Enable heap snapshots
   node --heapsnapshot-signal=SIGUSR2 app.js
   # Send signal every few minutes
   kill -USR2 <PID>  # writes heap-<timestamp>.heapsnapshot
   ```

4. For Python services (dashboard8083):
   ```bash
   pip install tracemalloc 2>/dev/null || true
   python3 -c "
   import tracemalloc
   tracemalloc.start()
   # ... after some runtime
   snapshot = tracemalloc.take_snapshot()
   top = snapshot.statistics('lineno')
   for stat in top[:20]:
     print(stat)
   "
   ```

5. Classify the growth:
   - **Module/import leaks**: Restart service and check if RSS resets
   - **Handle leaks**: Check open file descriptors: `ls -la /proc/<PID>/fd/ | wc -l`
   - **Memory fragmentation**: Check `/proc/<PID>/smaps` for large anonymous mappings

6. Fix the right layer:
   - Add periodic restart to runsv service config (`sv restart` in cron)
   - Fix unclosed connections, file handles, or timer leaks
   - Reduce module import overhead by lazy-loading

## Common ZES Leak Patterns

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Dashboard RSS grows | Python HTTP server leak | Add weekly restart via cron |
| MCP server RSS grows | Chrome CDP connection leak | Fix cleanup in `BROWSER.close()` |
| Hermes RSS grows | Cron job state accumulation | Check job cleanup in scheduler |
| 9Router RSS grows | Connection pool bloat | Check proxy connection recycling |

## Verification

```bash
# Before fix
ps -o pid,rss,%mem -p <PID>
# After fix - confirm RSS stabilizes
watch -n 30 "ps -o pid,rss,%mem -p <PID>"
```
