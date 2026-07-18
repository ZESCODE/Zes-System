---
category: Dashboard

name: ZES-design
description: Design system — apply Polybot/DESIGN.md theme to UI components. Colors, typography, spacing, and blue glowing panel styling.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES Design System

Design language for all ZES UI components, based on Polybot theme.

## Theme
- Dark blue gradient background
- Blue glowing borders (not background)
- Glassmorphism cards with subtle transparency
- Cyan/blue accent colors

## DESIGN.md
See `system-status/DESIGN.md` for full design specification.

## shadcn/ui + Tailwind
All dashboard components use shadcn/ui primitives with Tailwind CSS.
- `src/components/ui/` — shadcn components
- `src/lib/utils.ts` — cn() helper for class merging

## Key Colors
| Token | Value |
|-------|-------|
| Background | `bg-blue-950/30` |
| Border | `border-cyan-500/40` |
| Glow | `shadow-cyan-500/20` |
| Text | `text-white/90` |
| Muted | `text-blue-200/60` |

## Panel Style
All panels share:
- 1px blue/cyan border
- Subtle glow shadow
- Rounded corners
- Glassmorphism backdrop-blur
