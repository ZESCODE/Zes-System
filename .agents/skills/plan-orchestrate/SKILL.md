---
category: Core

name: plan-orchestrate
description: Read a plan document, decompose it into steps, design a per-step agent chain from the ECC catalogue, and emit ready-to-paste /orchestrate custom prompts. Generative only — never invokes /orchestrate itself. Use when the user has a multi-step plan and wants to drive it through orchestrate without composing chains by hand.
metadata:
  origin: ECC
---


# Plan Orchestrate

Bridge a plan document to `/orchestrate custom` by emitting one ready-to-paste invocation per step. The skill is generative only — it never executes `/orchestrate`. The user pastes each line when ready.

## When to Activate

- User has a multi-step plan document (PRD, RFC, implementation plan) and wants to drive it through `/orchestrate`.
- User says "orchestrate this plan", "give me orchestrate prompts for each step", "compose chains for this plan".
- A step-by-step plan exists but the user does not want to manually pick agents per step.

Skip when:
- The work is one ad-hoc step → call `/orchestrate custom` directly.
- The plan is unreadable or empty. Lack of explicit numbering alone is not a skip condition — see the "No clear steps" edge case below.

## Inputs

```
<plan-doc-path> [--lang=python|typescript|go|rust|cpp|java|kotlin|flutter|auto] [--scope=all|step:<n>|range:<a>-<b>] [--dry-run]
```

- `<plan-doc-path>` — required; relative or absolute path (`@docs/...` accepted).
- `--lang` — reviewer language variant; defaults to `auto` (detected from project).
- `--scope` — limits emitted steps; defaults to `all`.
- `--dry-run` — print decomposition + chain rationale only; do not emit final prompts.

## Authoritative `/orchestrate` shape (do not deviate)

```
{ORCH_CMD} custom "<agent1>,<agent2>,...,<agentN>" "<task description>"
```

Where `{ORCH_CMD}` is determined in Phase 0 (see below). The command string in the emitted output **always uses one concrete form** — never both, never a placeholder.

- `custom` is a sequential chain; each agent's HANDOFF feeds the next.
- Comma-separated agent list. No spaces preferred; one space tolerated.
- No `--mode` / `--gate` / `--agents=...` flags exist — never invent them.
- Agent names come from the catalogue in this skill. Embedded double quotes in the task description are escaped as `\"`.

## ECC install form and namespacing

Two install forms determine the prefix on **both** the slash command and every agent name. The two MUST stay in sync — one form per output, never mixed:

Let `<claude-home>` denote the Claude Code home directory: `~/.claude` on macOS/Linux, `%USERPROFILE%\.claude` on Windows. Resolve it the way the host platform resolves the user home directory (do not hardcode `~`).

| Form | Detection | `{ORCH_CMD}` | Agent name format |
|---|---|---|---|
| Plugin install (2.0.0+) | `<claude-home>/plugins/marketplaces/ecc/` exists | `/ecc:orchestrate` | `ecc:<name>` |
| Legacy bare install | Above absent; agent files under `<claude-home>/agents/` | `/orchestrate` | `<name>` |

Why this matters: under the plugin install, agents register as `ecc:tdd-guide`. Bare names force fuzzy matching, which fails intermittently under parallel calls. Under legacy, the prefixed forms are not registered and fail outright.

## Available agent catalogue (must pick from these)

General:
- `planner` — requirement restatement, risk decomposition, step planning
- `architect` — architecture, system design, refactor proposals
- `tdd-guide` — write tests → implement → 80%+ coverage
- `code-reviewer` — generic code review
- `security-reviewer` — security audit, OWASP, secret leakage
- `refactor-cleaner` — dead code, duplicates, knip-class cleanup
- `doc-updater` — documentation, codemap, README
- `docs-lookup` — third-party library API lookups (Context7)
- `e2e-runner` — end-to-end test orchestration
- `database-reviewer` — PostgreSQL schema, migration, performance
- `harness-optimizer` — local agent harness configuration
- `loop-operator` — long-running autonomous loops
- `chief-of-staff` — multi-channel triage (rarely a fit for plan steps)

Build error resolvers:
- `build-error-resolver` (generic) / `cpp-build-resolver` / `go-build-resolver` / `java-build-resolver` / `kotlin-build-resolver` / `rust-build-resolver` / `pytorch-build-resolver`

Code reviewers:
- `python-reviewer` / `typescript-reviewer` / `go-reviewer` / `rust-reviewer` / `cpp-reviewer` / `java-reviewer` / `kotlin-reviewer` / `flutter-reviewer`

A misspelled agent name fails `/orchestrate`. Cross-check against this list before emitting.

## How It Works

### Phase 0 — Detect ECC mode + language

1. Read `<plan-doc-path>`. If missing or empty, report and stop.
2. Detect ECC install form once and freeze it into `ECC_MODE`. Algorithm (run in order, stop at the first match):
   1. If `<claude-home>/plugins/marketplaces/ecc/` exists → `ECC_MODE=plugin`.
   2. Else if `<claude-home>/agents/` exists and contains at least one ECC agent file (e.g. `tdd-guide.md`, `code-reviewer.md`) → `ECC_MODE=legacy`.
   3. Else → default to `ECC_MODE=legacy` and emit a one-line warning at the top of the output: `> Warning: could not detect ECC install; defaulting to legacy form. If you use the plugin install, edit the prefixes manually.`
   4. If both markers exist (mixed install), `plugin` wins — the plugin namespace is the only one that resolves agent names without fuzzy matching.

   From this point on, every emitted line uses the matching prefix on **both** the slash command and every agent name. **Never emit both forms in the same output.**
3. Resolve `--lang`. When `auto`, run a polyglot-aware detection:
   - Probe markers: `pyproject.toml` / `uv.lock` / `requirements.txt` → python; `package.json` → typescript; `go.mod` → go; `Cargo.toml` → rust; `CMakeLists.txt` or top-level `*.cpp` → cpp; `pom.xml` / `build.gradle` (Java) → java; `build.gradle.kts` or top-level Kotlin → kotlin; `pubspec.yaml` → flutter.
   - **Polyglot tie-break**: if more than one marker matches, pick the language whose source files outnumber the others (count via `git ls-files`, excluding `vendor/`, `node_modules/`, `dist/`, `build/`, `.venv/`, generated files, and obvious test fixtures). On a tie or when no language exceeds 60% of source files, set `lang=unknown`.
   - No marker matched → set `lang=unknown`.
   - `lang=unknown` is a sentinel — it is **not** an agent name. Phase 2 rules 4 and 5 turn it into `code-reviewer` / `build-error-resolver` at chain composition time.
4. Detect a **PyTorch sub-profile**: when `lang=python` and any of `pyproject.toml` / `requirements.txt` / `uv.lock` declares a dependency on `torch`, set `pytorch=true`. This only affects `build` chain selection (Phase 2 rule below); the reviewer remains `python-reviewer`.
5. **Normalize any agent names declared in the plan**: if the plan text references agents by their plugin-prefixed form (e.g. `ecc:tdd-guide`), strip the prefix to get the bare catalogue name before validating or composing chains. Re-prefixing happens only at output time per `ECC_MODE` (Phase 4). Never let a pre-prefixed name flow into chain composition — it would double-prefix in plugin mode.

### Phase 1 — Decompose steps

Identify "step units" in priority order:

1. Explicit numbering: `## Step N` / `### Phase N` / `## N. ...` / top-level ordered list.
2. A "Step" column in a table.
3. `---`-separated blocks with verb-led headings.
4. Otherwise treat each H2 as one step.

Per step extract `id` (1-based), `title` (≤ 80 chars), `intent` (1–3 sentences), `tags`.

### Phase 2 — Tag and pick chain

Tag by intent (multi-tag allowed; chain built from primary + stacked secondaries):

Trigger words below are matched case-insensitively. Multilingual plans are supported by matching the word stems in any language as long as the meaning aligns with the listed English trigger words.

| Tag | Trigger words | Default chain |
|---|---|---|
| `design` | architecture, design, choose, evaluate, RFC | `planner,architect` |
| `plan` | plan, breakdown, milestone | `planner` |
| `impl` | implement, build, add, create, port | `tdd-guide,<lang>-reviewer` |
| `test` | test, coverage, e2e, integration | `tdd-guide,e2e-runner` |
| `refactor` | refactor, cleanup, dedupe, split | `architect,refactor-cleaner,<lang>-reviewer` |
| `migration` | migrate, upgrade, rewrite, port | `architect,tdd-guide,<lang>-reviewer` |
| `db` | schema, migration, index, SQL, Postgres, alembic, sqlmodel | `database-reviewer,<lang>-reviewer` |
| `security` | encrypt, auth, secret, OWASP, PII | `security-reviewer,<lang>-reviewer` |
| `build` | build, compile, lint failure, CI | `<lang>-build-resolver` (falls back to `build-error-resolver`) |
| `docs` | docs, readme, codemap, changelog | `doc-updater` |
| `lookup` | lookup, reference, API usage | `docs-lookup` |
| `review` | review, audit, verify | `<lang>-reviewer,code-reviewer` |
| `loop` | loop, autonomous, watchdog | `loop-operator` |

Chain composition rules:
1. **Primary tag selection**: when a step matches multiple tags, the **first one in table order** (top of the table = highest priority) is the primary; the rest are secondaries. Composition rules 2 and 3 below handle specific multi-tag combinations explicitly; otherwise, append secondary chains in tag table order.
2. `impl` + `security` → `tdd-guide,<lang>-reviewer,security-reviewer`.
3. `impl` + `db` → `tdd-guide,database-reviewer,<lang>-reviewer`.
4. **Deduplicate** the resulting chain (preserve first occurrence). E.g. `review` + `lang=unknown` would yield `code-reviewer,code-reviewer` after rule 5; deduplication collapses it to `code-reviewer`.
5. `<lang>-reviewer` resolves to `code-reviewer` when `lang=unknown`.
6. `<lang>-build-resolver` resolves to `build-error-resolver` when `lang=unknown`. **Special case**: if Phase 0 set `pytorch=true`, use `pytorch-build-resolver` for `build` chains regardless of `<lang>`. There is no `python-build-resolver`; `--lang=python` without `pytorch=true` resolves to `build-error-resolver`.
7. **Zero-tag steps**: if no trigger word matches, set chain to `code-reviewer` and write `no tag matched; default review-only chain` under "Chain rationale".
8. Chain length ≤ 4 after deduplication. If exceeded, drop weakest tag (`lookup` and `docs` first).
9. Do not pair `planner` and `architect` in an `impl` chain (token waste). Pair them only on `design` steps.
10. Steps tagged `impl`, `refactor`, or `migration` end with a **reviewer-class** agent — any of `<lang>-reviewer`, `code-reviewer`, `security-reviewer`, or `database-reviewer`. The most domain-specific reviewer wins the tail position (e.g. rule 2's `impl+security` ends with `security-reviewer`; rule 3's `impl+db` ends with `<lang>-reviewer` because `database-reviewer` already gates the migration earlier in the chain). `test` and `build` steps are gated by their own validators (`e2e-runner` and the build resolver respectively) and do not require an additional reviewer.

### Phase 3 — Compress task description

Each emitted `<task description>` must:
- Be self-contained (the first agent does not need the plan document open).
- Start with `[Plan: <path>#step-<id>]`.
- Include 1–3 verifiable Acceptance criteria.
- Include a Scope guard (`Out of scope: ...`) **only if the plan declares one for this step**. Inherit verbatim. If the plan has no out-of-scope statement, omit the clause entirely — do not invent one.
- Be 200–600 characters; one line; embedded `"` escaped as `\"`; no literal newlines.

### Phase 4 — Output

Emit Markdown using **the form determined by `ECC_MODE`**. The output uses one form throughout — every `{ORCH_CMD}` and every agent name is rendered with the matching prefix from Phase 0. **Do not emit both forms; do not include "this is plugin form" / "strip the prefix" instructions in the rendered output.**

Concrete rendering rules:

- `{ORCH_CMD}` = `/ecc:orchestrate` under `plugin`, `/orchestrate` under `legacy`.
- `{AGENT(name)}` = `ecc:<name>` under `plugin`, `<name>` under `legacy`.
- The overview-table "Chain" column uses the same `{AGENT(name)}` rendering.
- Per-step bash blocks contain only the runnable command. **No `# plugin form` or `# legacy form` comments** — the form is implicit and uniform across the whole output.

Output structure:

````markdown
# Plan-Orchestrate Result

**Plan**: `<path>`
**Lang**: `<detected-or-given>`
**ECC mode**: `<plugin | legacy>`
**Steps**: <N>
**Scope**: <all | step:n | range:a-b>

## Steps overview

| # | Title | Tags | Chain |
|---|---|---|---|
| 1 | ... | impl, db | `{AGENT(tdd-guide)},{AGENT(database-reviewer)},{AGENT(python-reviewer)}` |
| ... | | | |

---

## Step 1 — <title>

**Intent**: <1–3 sentences>
**Tags**: <a, b>
**Chain rationale**: <why this chain; which agent closes the loop>

```bash
{ORCH_CMD} custom "{AGENT(tdd-guide)},{AGENT(database-reviewer)},{AGENT(python-reviewer)}" "[Plan: docs/foo.md#step-1] <compressed task description>; Acceptance: <1–3 items>; Out of scope: <…>"
```
````

> The `{ORCH_CMD}` and `{AGENT(...)}` notation above describes the substitution this skill performs at runtime. The actual emitted Markdown contains the resolved strings, never the placeholders.

Append a final "Batch execution" block aggregating every step's command in order so the user can paste them all at once. **Skip the Batch block in overview-only mode** (see "Large plan" edge case): when only the overview table is being emitted, there are no per-step commands to aggregate.

### Phase 5 — Self-check (run before emitting)

- [ ] Every agent in every chain comes from the catalogue (after stripping any `ecc:` prefix that appeared in the plan; see Phase 0 step 5).
- [ ] Resolved `{ORCH_CMD}` and every resolved `{AGENT(...)}` use the **same** form (`plugin` or `legacy`) — never mixed in one output.
- [ ] No `# plugin form` / `# legacy form` annotations and no "strip the prefix" instructions remain in the rendered output.
- [ ] No invented `--mode` / `--gate` / `--agents=...` fields.
- [ ] Each task description is single-line, double-quoted, with embedded `"` escaped.
- [ ] Each task description begins with `[Plan: <path>#step-<id>]` and includes Acceptance (1–3 items). The `Out of scope:` clause is present only when inherited from the plan.
- [ ] No duplicate agent in any chain after Phase 2 dedup.
- [ ] Chain length ≤ 4.
- [ ] Steps tagged `impl`/`refactor`/`migration` end with a reviewer-class agent (`<lang>-reviewer`, `code-reviewer`, `security-reviewer`, or `database-reviewer`). `test` and `build` are exempt — see Phase 2 rule 10.
- [ ] Zero-tag steps emit `code-reviewer` with the rationale `no tag matched; default review-only chain`.
- [ ] Overview table lists every step in the plan, regardless of `--scope`.
- [ ] Per-step detail block count matches the resolved `--scope` (full plan when `--scope=all`; one block for `step:n`; range size for `range:a-b`). In overview-only mode, no per-step blocks and no Batch block are emitted.

## Edge cases

- **No clear steps**: prefer H2/H3 splitting; if still ambiguous, report "no structured steps detected" with the document outline and ask the user to confirm running by outline.
- **Large plan (>1500 lines)**: enter **overview-only mode** — emit only the overview table and ask the user to narrow with `--scope` before re-running for details. In this mode, skip per-step detail blocks and skip the Batch execution block.
- **Step too broad** (e.g. "complete all backend work"): do not force a single chain. Suggest splitting into N.a and N.b and propose a split.
- **Plan declares agents** (rare): first **strip any `ecc:` prefix** to get the bare catalogue name (Phase 0 step 5), then validate against the catalogue. Replace invalid agents and explain under "Chain rationale". The bare name is re-prefixed at output time per `ECC_MODE`.
- **Polyglot project where `--lang=auto` cannot pick a winner**: set `lang=unknown`; reviewer resolves to `code-reviewer` and build resolver to `build-error-resolver`. Mention the fallback under "Chain rationale".

## Examples

### Example 1 — Plugin mode, Python plan

Input:
```
plan-orchestrate @docs/plan/example-feature.md --lang=python
```

Excerpt of expected output:
````markdown
## Step 2 — Encrypt sensitive UserProfile fields

**Intent**: Introduce an `EncryptedString` SQLAlchemy type and AES-GCM encrypt `birth_datetime` / `location` before persistence; load the key from an environment variable.
**Tags**: impl, security, db
**Chain rationale**: Security-sensitive write path, so `security-reviewer` closes the chain; `database-reviewer` validates the alembic migration; `python-reviewer` covers typing and PEP 8.

```bash
/ecc:orchestrate custom "ecc:tdd-guide,ecc:database-reviewer,ecc:python-reviewer,ecc:security-reviewer" "[Plan: docs/plan/example-feature.md#step-2] Implement EncryptedString SQLAlchemy type and migrate UserProfile.birth_datetime/location columns; key from ENV APP_DB_KEY; Acceptance: encrypt/decrypt roundtrip tests pass; alembic upgrade/downgrade clean on empty DB; no plaintext in DB after migrate; Out of scope: cross-tenant profile sharing logic"
```
````

### Example 2 — Legacy mode, same step

If `ECC_MODE=legacy` were detected, the same step would be emitted as a single uniform command (no plugin-prefixed forms anywhere in the output):

```bash
/orchestrate custom "tdd-guide,database-reviewer,python-reviewer,security-reviewer" "[Plan: docs/plan/example-feature.md#step-2] ..."
```

The two examples above illustrate **the two possible outputs** for two different environments. A single skill invocation produces only one of them, end to end.

## Notes

- Generative only. Never invoke `/orchestrate` from inside this skill.
- Match the language of the plan document for task descriptions (agent names always remain English).
- Do not insert "Co-Authored-By" lines or emoji in the output unless the user explicitly asks.

---
### Merged from ZES-plan-canvas

---
name: plan-canvas
description: Open plans and HTML artifacts in a local browser canvas where the human annotates elements, chats, and approves or requests changes without leaving the page. Use when presenting a plan for review, or when feedback like "move this, change that" is easier pointed at than typed.
metadata:
  origin: ECC
---

# Plan Canvas

Review loop for plans and visual artifacts: you write the artifact, the human
reviews it in the browser — annotating the exact element they mean, chatting,
and delivering an **Approve plan / Request changes** verdict — while you block
on a single CLI call that returns their feedback as JSON.

Inspired by [lavish-axi](https://github.com/kunchenguid/lavish-axi); rebuilt
ECC-native around the `/plan` confirmation gate, with zero dependencies.

## When to Use

- You just wrote a plan artifact (`.claude/plans/*.plan.md` from `/plan`) and
  need the CONFIRM/approve decision — the canvas verdict replaces a typed
  "yes/proceed".
- The user should *point at* what to change: reviewing designs, comparisons,
  reports, or any local `.md` / `.html` artifact.
- The user asks for `/plan-canvas`, a visual review, or "open it in the browser".

Do NOT use for: code review of diffs (`/code-review`), running web apps, or
remote URLs. The canvas serves local artifact files only.

## How It Works

Invoke the CLI as `ecc-plan-canvas` — the bin shipped by the `ecc-universal`
package (on PATH after a global/plugin install; `node "$CLAUDE_PLUGIN_ROOT/scripts/plan-canvas.js"`
also works for plugin installs). Run it from the project you are reviewing in;
it works from any working directory. It manages a detached loopback server
(`127.0.0.1:4517`) shared by all sessions, keyed by artifact path — no session
ids to track.

The workflow is a plain CLI-plus-JSON loop, so it is model- and harness-agnostic:
any agent that can run a shell command and read stdout drives it the same way
(Claude Code, Codex, Cursor, Gemini, OpenCode, Copilot). Trigger it however your
harness surfaces skills — e.g. `/plan-canvas` in Claude Code, `$plan-canvas` in
Codex — or just run the `ecc-plan-canvas` commands directly.

```bash
# 1. Open the artifact in the user's browser (returns immediately)
ecc-plan-canvas open .claude/plans/feature.plan.md

# 2. Block until the human responds. Leave running; re-run if interrupted —
#    queued feedback is never lost. Run in the background if your harness
#    time-limits foreground commands.
ecc-plan-canvas await .claude/plans/feature.plan.md
```

`await` prints JSON when the human acts:

```json
{
  "status": "feedback",
  "items": [
    { "kind": "annotation", "text": "Split this into two phases",
      "anchor": { "selector": "h2:nth-of-type(3)", "tag": "h2", "snippet": "Phase 2: Migration" } },
    { "kind": "verdict", "verdict": "request-changes" }
  ]
}
```

- `kind: "chat"` — freeform message; answer in the canvas, not the terminal.
- `kind: "annotation"` — feedback anchored to an element (`anchor.selector`,
  `anchor.snippet` show what they pointed at; `anchor.textRange.text` when
  they highlighted a passage).
- `kind: "verdict"` — `approve` means the plan is CONFIRMED: stop polling,
  end the session, and start implementing. `request-changes` means revise the
  artifact (the canvas live-reloads it) and keep the loop going.

**3. Respond in the canvas**, then keep listening — one command does both:

```bash
ecc-plan-canvas await <file> --reply "Split Phase 2 as requested — take a look."
```

**4. End** when review concludes: `ecc-plan-canvas end <file>`.

## Diagrams (Mermaid)

When part of the plan is a flow, architecture, sequence, state machine, ER
model, or dependency graph, author it as a fenced ` ```mermaid ` block instead
of ASCII art or a wall of prose — the canvas renders it as a themed diagram the
human can point at. Reach for it when a picture reads faster than a paragraph;
skip it for simple lists or tables.

````markdown
```mermaid
flowchart LR
  A[Market resolves] --> B{Watchers?}
  B -->|yes| C[Enqueue jobs] --> D[Fan-out worker]
```
````

Diagrams render in the ECC dark theme with the accent palette. Mermaid loads in
the browser from a pinned CDN; if that is unavailable (offline), the block
degrades to showing its source, so the review is never blocked. Point a local
mirror at `ECC_PLAN_CANVAS_MERMAID_URL` for air-gapped use.

## Rules

- Markdown artifacts render in ECC's plan template (including Mermaid blocks);
  `.html` artifacts render as-is with the annotation layer injected. For HTML
  authoring guidance use the `frontend-design-direction` and `artifact-design`
  skills.
- Edit the artifact file to revise — the canvas live-reloads on save. Never
  re-run `open` to refresh.
- `{"status": "ended", "endedBy": "user"}` (or `sessionEnded: true` on a
  feedback batch) means the user closed the review: stop polling, deliver
  remaining updates in chat, and do not reopen. A plain `open` on that
  session is refused; pass `--reopen` only when the user asks to resume.
- Sibling assets (images, CSS) must sit next to the artifact and be
  referenced by relative path.
- The server is loopback-only and exits after 30 idle minutes
  (`ECC_PLAN_CANVAS_IDLE_MS`); `stop` shuts it down explicitly. State lives
  in `~/.claude/plan-canvas/` (`ECC_PLAN_CANVAS_STATE_DIR`).

## Examples

**Plan approval flow** — `/plan` writes
`.claude/plans/notifications.plan.md` and must WAIT for confirmation:

```bash
ecc-plan-canvas open .claude/plans/notifications.plan.md
ecc-plan-canvas await .claude/plans/notifications.plan.md
# → {"status":"feedback","items":[{"kind":"verdict","verdict":"approve"}]}
ecc-plan-canvas end .claude/plans/notifications.plan.md
# plan is confirmed — begin implementation
```

**Revision loop** — feedback arrives, you edit the file, reply, keep listening:

```bash
# await returned annotations → edit the .plan.md (canvas live-reloads)
ecc-plan-canvas await <file> --reply "Reworked the risk table."
# → blocks again until the next response
```

## Anti-Patterns

- Polling with `--timeout-ms` in a loop — it exists for tests. Leave the
  plain `await` running instead.
- Reopening after a user-initiated end "just to show" something.
- Pasting the whole plan into chat *and* opening a canvas — pick the canvas
  and keep the terminal summary to one line.
- Parsing the canvas chat from state files — everything you need arrives via
  `await`.

---
### Merged from ZES-plan

---
name: zes-plan
description: Implementation planning for ZES system — assess impact, risks, and write step-by-step plans before touching code.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---

# ZES Planning

Systematic implementation planning for ZES infrastructure changes.

## When to Activate

- Before implementing new features
- Before refactoring services
- Before changing service architecture
- Before adding new integrations

## Planning Process

### 1. Requirements Restatement
Restate the request in ZES system context. Identify which services, ports, and configs are affected.

### 2. Risk Assessment
- **Service disruption risk**: Will this restart/change affect running services?
- **Security risk**: Does this expose new ports or require new credentials?
- **Data loss risk**: Does this modify backup/state files?
- **Rollback plan**: How to revert if something goes wrong?

### 3. Step-by-Step Plan
```
Phase 1: Preparation (backup configs, notify if needed)
Phase 2: Implementation (specific files to change)
Phase 3: Verification (run evals, check services)
Phase 4: Documentation (update AGENTS.md, README)
```

### 4. Approval Gate
Present plan to user for confirmation before executing.

