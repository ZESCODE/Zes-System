#!/usr/bin/env python3
"""ZES Context Feeder — watches workspace files and feeds context to agents."""
import json, os, time, hashlib
from pathlib import Path

WORKSPACE = Path.home() / ".zes" / "workspace"
STATE_FILE = Path.home() / ".zes" / "context_state.json"

def get_files():
    snapshots = {}
    if not WORKSPACE.exists(): return snapshots
    for f in WORKSPACE.rglob("*"):
        if f.is_file() and f.stat().st_size < 100000:
            snapshots[str(f)] = hashlib.md5(f.read_bytes()).hexdigest()
    return snapshots

def diff(old, new):
    changes = []
    for path, h in new.items():
        if path not in old:
            changes.append({"path": path, "change": "added"})
        elif old[path] != h:
            changes.append({"path": path, "change": "modified"})
    for path in old:
        if path not in new:
            changes.append({"path": path, "change": "deleted"})
    return changes

if __name__ == "__main__":
    os.makedirs(WORKSPACE.parent, exist_ok=True)
    old = get_context()
    print(f"📡 Context feeder watching {WORKSPACE}")
    while True:
        time.sleep(30)
        new = get_context()
        changes = diff(old, new)
        if changes:
            with open(STATE_FILE, "w") as f:
                json.dump({"changes": changes, "timestamp": time.time()}, f, indent=2)
            print(f"  Changes: {len(changes)}")
        old = new
