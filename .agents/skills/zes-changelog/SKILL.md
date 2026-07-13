---
name: zes-changelog
description: "Regenerate ZES system changelog sections from git history before releases."
---

# ZES Changelog Update

Use this for release changelog rewrites. Run before tagging a new ZES release.

## Workflow

1. Start on main branch:
   ```bash
   git fetch --tags origin
   git pull --ff-only
   git status -sb
   ```

2. Audit history:
   ```bash
   git log --first-parent --date=iso-strict --pretty=format:'%h%x09%ad%x09%s' <last-tag>..HEAD
   git log --first-parent --grep='(#' --date=short --pretty=format:'%h%x09%ad%x09%s' <last-tag>..HEAD
   ```

3. Rewrite the target section in `CHANGELOG.md`:
   - `### Highlights`: 3-5 bullets, broad user wins first
   - `### Changes`: new capabilities and behavior changes
   - `### Fixes`: user-facing fixes first, grouped by impact

4. Preserve attribution:
   - Keep `#issue`, `(#PR)`, `Fixes #...`, and `Thanks @...`
   - Every human-authored merged PR gets credit
   - Never thank bots

5. Sort by user impact:
   - Service reliability and data safety first
   - New features and integrations
   - Performance and observability
   - Docs and internal details last

6. Validate:
   ```bash
   git diff --check
   git commit -m "docs(changelog): refresh YYYY-MM-DD notes"
   ```
