---
name: zes-typescript-review
description: TypeScript/JavaScript review for ZES — Node services, agent UI, MCP servers, Express patterns.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---

# ZES TypeScript/JavaScript Review

Code review for JS/TS in ZES: agent-server.js, memory-store.js, kanban-store.js, MCP servers, Claude proxy.

## When to Activate

- Reviewing agent-server.js or agent UI changes
- Reviewing MCP server implementations
- Reviewing Claude proxy or bridge services

## Checklist

### 1. ES Module Patterns
- Use `import/export` (ESM), not `require()`
- Package.json includes `"type": "module"` for ESM projects
- File paths use `fileURLToPath(import.meta.url)` for __dirname

### 2. Express/HTTP Patterns
```javascript
// ✅ Good: async error handling
app.get('/api/status', async (req, res) => {
    try {
        const data = await getSystemStatus();
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});
```

### 3. Memory & State
- No global mutable state without synchronization
- Memory store uses atomic file writes (writeFileSync)
- Session/task data persisted to localStorage or JSON files

### 4. Security
- No eval() or new Function()
- Input sanitization for chat messages
- Proper Content-Type headers
- CORS headers only for localhost origins

