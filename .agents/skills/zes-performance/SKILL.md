---
name: zes-performance
description: "Benchmark, diagnose, and optimize ZES service performance: startup time, response latency, throughput."
---

# ZES Performance

Use when diagnosing slow services, high CPU, or optimizing ZES system performance.

## Workflow

1. **Establish baseline** before changing anything:
   ```bash
   # Service response time
   time curl -s http://localhost:8083/api/status > /dev/null
   
   # Process CPU/RSS
   ps -o pid,%cpu,rss,cmd -p $(pgrep -f dashboard_v3)
   
   # System load
   uptime && free -h
   ```

2. **Profile the bottleneck**:
   - **Dashboard**: Check Python process CPU, profile with `cProfile`
   - **MCP server**: Check Node.js event loop lag
   - **9Router**: Check proxy connection latency with `curl -w "%{time_total}"`
   - **Hermes**: Check cron job duration in logs

3. **Common ZES optimizations**:

   | Area | Tool | Target |
   |------|------|--------|
   | Dashboard | `python3 -m cProfile` | Reduce startup time |
   | MCP server | `node --prof` | Reduce Chrome CDP round-trips |
   | 9Router | `curl -w` | Reduce provider failover latency |
   | Hermes | cron log grep | Reduce job overlap |
   | Tor | `ss -tlnp` | Reduce connection pool size |

4. **Pick the next attack by return**:
   - High return: one service dominates restore time or RSS
   - High leverage: one config change improves all services
   - Quick win: caching or lazy-loading frequently-used data

5. **Verify**:
   ```bash
   # Same measurement as baseline
   time curl -s http://localhost:<port>/api/status > /dev/null
   ps -o pid,%cpu,rss,cmd -p $(pgrep -f <service>)
   ```

## Benchmark Script

```bash
#!/bin/bash
# Quick latency benchmark
for i in 1 2 3; do
  for url in \
    http://localhost:8083/api/status \
    http://localhost:5900/ \
    http://localhost:20128/; do
    echo -n "$url → "
    curl -so /dev/null -w "status=%{http_code} time=%{time_total}s\n" "$url"
  done
done
```
