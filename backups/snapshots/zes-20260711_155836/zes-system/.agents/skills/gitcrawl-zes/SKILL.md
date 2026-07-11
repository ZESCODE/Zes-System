# GitCrawl ZES

> Adapted from OpenClaw's gitcrawl for ZES System repos.

## When to Use

When searching ZES System git history for issues, commits, or patterns.

## Commands

```bash
# Recent changes
git log --oneline -20

# Search commits for a keyword
git log --all --oneline --grep="keyword"

# Search codebase
git grep "function_name"

# Blame a specific line
git blame -L start,end path/to/file.ts

# Diff between commits
git diff HEAD~5..HEAD --stat

# Staged/unstaged status
git status
```

## Repos

| Repo | Path | Purpose |
|------|------|---------|
| Zes-System | `~/Zes-System/` | Main system repo |
| ZES-project | `/storage/emulated/0/Download/ZES-project/` | Extension deployment |
| Codex chats | `~/.codex/sessions/` | Agent conversation history |
