---
name: zes-transcript
description: "Add a redacted agent transcript section to GitHub PR or issue bodies during ZES system workflows."
---

# ZES Agent Transcript

Best-effort local-only provenance for ZES PR/issue bodies. Use during agent-created
GitHub PR or issue workflows before creating/updating the body.

## Contract

- Never use network. Session discovery reads local agent logs only.
- Never upload raw logs. Render sanitized Markdown first.
- Always ask the user before adding transcript logs to a GitHub PR/issue body.
- Offer a local HTML preview before insertion.
- Fail closed on unresolved secrets, private keys, browser/session/cookie details, or auth URLs.
- Drop system/developer prompts, raw tool outputs, reasoning, env, cookies, tokens, and broad local paths.
- Keep user prompts, assistant visible decisions, terse tool summaries, and test/proof outcomes.
- Remove session turns unrelated to the PR/issue work.
- Best effort only: PR/issue creation must continue if no safe transcript is found.

## Finding Session Logs

Session logs for ZES agent sessions are typically in:

```bash
# Codex session logs
ls ~/.codex/logs/ 2>/dev/null

# Hermes session logs  
ls ~/.hermes/logs/ 2>/dev/null

# Claude Code session logs
ls ~/.claude/sessions/ 2>/dev/null
```

## Transcript Format

```markdown
## Agent Transcript
<details>
<summary>Sanitized session transcript (click to expand)</summary>

**User prompt**: [sanitized]

**Assistant**: [key decisions and actions taken]

**Tools used**: [tool summaries without raw outputs]

**Proof**: [test results, command outputs — redacted]
</details>
```

## Rules

- Add the section only when inserting a real transcript
- Never add a placeholder transcript heading
- Use a collapsed `<details>` section
- Update existing markers instead of duplicating sections
