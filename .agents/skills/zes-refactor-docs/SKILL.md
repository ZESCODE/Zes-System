---
name: zes-refactor-docs
description: "Refactor ZES system documentation with source-audited preservation, restructuring, and verification."
---

# ZES Refactor Docs

## Overview

Use this skill when the user gives a target ZES docs page and asks to
rewrite, refactor, reorganize, split, shorten, or improve it.

## Inputs

Required:
- A target docs page path (under `Zes-System/docs/`).

Optional:
- Desired page type: overview, guide, reference, or troubleshooting.
- Specific goals (shorter, more accurate, align with current behavior).
- Related source files, configs, commands, tests.

## Working Contract

Refactor the target page to be more useful, concise, and comprehensive within
its stated scope.

Do not treat a rewrite as permission to discard behavior facts. Preserve,
verify, move, or explicitly retire existing material.

## Workflow

1. Read the current page fully.
2. Check related source files, configs, and commands for accuracy drift.
3. Identify what to keep, move, rewrite, or remove.
4. Restructure:
   - Shorter main page → move details to sub-pages
   - Split large pages → one focused topic per page
   - Add missing sections → troubleshooting, examples, prerequisites
5. Verify:
   - Every command example works when run
   - Every port/service reference is current
   - Every environment variable name is correct
6. Update cross-references in other docs pages.

## Style

- Use clear, active language
- Prefer code blocks for commands and configs
- Keep one idea per paragraph
- Link to related pages rather than duplicating content
