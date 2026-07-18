---
category: Dashboard

name: ZES-dashboard
description: Build and maintain the ZES System Dashboard — React 19 + shadcn/ui + Vite 8 + Tailwind CSS v4. Service status, memory viewer, design studio, kanban board.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES Dashboard

Unified web dashboard for controlling and monitoring the ZES system.

## Stack
- React 19.2.7
- shadcn/ui 4.13.0
- Vite 8.1.1
- Tailwind CSS 4.3.2
- Lucide React icons

## Pages
- Home — System summary
- Services — Service status + controls
- Memory — ZES memory viewer
- Kanban — Task board (shared with Hermes)
- Design Studio — Theme editor
- Settings — Configuration

## Commands
```bash
cd ~/Documents/Codex/2026-07-12/system-status
npm run dev    # http://localhost:5173
npm run build  # Production build
```

## Design System
- `DESIGN.md` — Polybot theme variables
- `src/components/ui/` — shadcn components
- Blue glowing borders (Polybot theme)
