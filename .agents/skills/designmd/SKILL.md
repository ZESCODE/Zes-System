---
category: Design

name: designmd
description: Use when building UI that needs a consistent design system, choosing colors/typography/spacing, or applying a DESIGN.md from designmd.ai to your codebase
---


# DESIGN.md — Design Systems for AI Coding

## Overview

[DESIGN.md](https://designmd.ai) is a marketplace of **100s of free design systems** that AI coding tools can read. Instead of describing your design preferences manually, download a `DESIGN.md` file that defines colors, typography, spacing, components, and patterns — then reference it in your `AGENTS.md` or project instructions.

## How It Works

```
User: "Build a dashboard with a dark theme"
You: [Finds matching DESIGN.md from designmd.ai]
     [Applies the design system to all generated code]
     [Ensures colors, spacing, fonts, and components follow the spec]
```

A `DESIGN.md` typically covers:
- **Brand** — Name, tagline, personality, voice & tone
- **Colors** — Primary, secondary, accent, neutral, semantic (success/warning/error)
- **Typography** — Font families, sizes, weights, line heights
- **Spacing** — Unit scale (4px/8px grid), layout margins, component padding
- **Components** — Buttons, inputs, cards, modals, navigation — styles and states
- **Patterns** — Page layouts, data display, forms, responsive behavior

## MCP Setup (Recommended)

The DESIGNmd MCP server adds only ~2K tokens to context. Works with any MCP-compatible tool.

```toml
# Add to .codex/config.toml
[mcp_servers.designmd]
command = "npx"
args = ["designmd-mcp"]
env = { "DESIGNMD_API_KEY" = "dk_your-key-here" }
```

Create a free API key at [designmd.ai](https://designmd.ai). Searching and browsing work without one; downloading, uploading, and deleting require a key.

## Design System Discovery

### Via MCP (when installed)

Ask your AI coding agent:

| Task | Prompt |
|------|--------|
| Search | "Search DESIGNmd for a dark fintech design system" |
| Browse | "Show me trending design systems on DESIGNmd" |
| Tags | "What tags are available on DESIGNmd?" |
| Download | "Download the Neon Fintech design system and save as DESIGN.md" |

### Via Website

Browse at [designmd.ai/explore](https://designmd.ai/explore)

### Via CLI

```bash
npx designmd-mcp search "dark fintech"
npx designmd-mcp download <design-id>
```

## Applying a DESIGN.md to Your Project

Once you've found a design system:

1. **Download it** — Save as `DESIGN.md` in your project root
2. **Reference it** — Add to `AGENTS.md`:
   ```markdown
   ## Design System
   This project follows the design system defined in DESIGN.md.
   All UI code must use the colors, typography, and components specified there.
   ```
3. **Use it** — When generating UI code, reference the DESIGN.md for all design tokens

### Example Workflow

```
You: I found "SaaS Starter" on designmd.ai — a clean light theme.
     Downloading as DESIGN.md...
     [Saves to ./DESIGN.md]
     
Now when building UI components:
- Use `--color-primary: #6366F1` (indigo) for primary actions
- Use `font-family: 'Inter', sans-serif` for body text  
- Use `rounded-lg` for card corners
- Follow the button component spec for all interactive elements
```

## When to Use This Skill

- **Starting a new UI project** — Find a design system that fits before writing code
- **Redesigning** — Find a modern design system to guide the refresh
- **Missing design spec** — User asks for a UI but doesn't specify design details
- **Consistency check** — Generated UI looks inconsistent; find a system to standardize

## When NOT to Use

- User explicitly provides their own design tokens or brand guidelines
- Working on backend-only code with no UI
- Project already has a `DESIGN.md` that's being actively followed

## Common Mistakes

- **Downloading without applying** — Having a DESIGN.md file but not referencing it in instructions
- **Not checking tags** — Use tags to filter by framework (React, Vue, Tailwind) or style (minimal, bold)
- **Overriding the design** — If you pick a design system, stick to it unless the user asks for changes
- **Multiple design systems** — Use one DESIGN.md per project; mixing creates inconsistency

## Integration with Other Skills

- **frontend-patterns** — Combine a DESIGN.md with frontend implementation patterns
- **react-patterns** — Apply design tokens to React component code
- **frontend-a11y** — Ensure design system meets accessibility requirements
- **browser-qa** — Verify the applied design renders correctly

## Quick Reference

```bash
# Search designs
npx designmd-mcp search "query"

# Get trending
npx designmd-mcp trending

# List tags
npx designmd-mcp tags

# Download design
npx designmd-mcp download <id>

# Save to project
curl -sL "https://designmd.ai/api/v1/designs/<id>/download" > DESIGN.md
```
