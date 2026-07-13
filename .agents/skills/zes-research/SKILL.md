---
name: zes-research
description: Multi-source research using MCP tools — search the web, synthesize findings, produce cited reports. Use when ZES agents need current information.
---

# ZES Deep Research

Produce thorough, cited research from web sources for ZES agents. Use when you need current information about providers, tools, or technologies.

## When to Activate

- Researching AI provider capabilities, pricing, or availability
- Investigating new tools or libraries for ZES
- Looking up documentation for 9Router, Hermes, or MCP
- Competitive analysis of AI services
- Current events or technology evaluation
- User asks "research", "deep dive", or "what's the current state of"

## MCP Requirements

At least one web search MCP tool:
- **firecrawl** — `firecrawl_search`, `firecrawl_scrape`  
- **exa** — `web_search_exa`, `web_search_advanced_exa`

Configure in ZES MCP server or directly in Claude Code config.

If neither is available, fall back to `curl` + browser-based search via `zeschrome-mcp`.

## Workflow

### Step 1: Understand the Goal

Ask 1 quick clarifying question if the topic is vague:
> "What's your goal — learning, making a decision, or writing something?"

If clear — proceed directly.

### Step 2: Plan the Research

Break the topic into 3-5 research sub-questions. Example for "Which AI provider is best for ZES inference?":
1. What are the available free-tier providers via 9Router?
2. What's the latency and reliability of each?
3. Are there rate limits or model constraints?
4. What do the provider health check results show?
5. What are the costs (if any)?

### Step 3: Execute Multi-Source Search

For EACH sub-question, search and synthesize:

```bash
# Search with fallback to curl
curl -s "https://api.duckduckgo.com/?q=groq+vs+cerebras+latency+benchmark&format=json" | head -50
```

When using `zeschrome-mcp` for search:
```
1. Navigate to search engine
2. Search for the specific sub-question
3. Extract relevant content from results
4. Move to next sub-question
```

### Step 4: Synthesize Findings

Write a structured report:

```markdown
# Research: [Topic]

## Summary
2-3 sentence overview of findings.

## Findings

### [Sub-Question 1]
- Key finding with source
- Key finding with source

### [Sub-Question 2]
- Key finding with source

## Recommendations
What should ZES do based on this research?

## Sources
- [URL 1] — description
- [URL 2] — description
```

## ZES Research Topics

| Topic | Why | Sources |
|-------|-----|---------|
| 9Router provider status | Which providers are reliable | 9Router API + web docs |
| MCP SDK updates | Latest protocol changes | modelcontextprotocol.io |
| Claude Code features | New capabilities for ZES | Anthropic docs |
| Termux updates | Android Linux environment | termux.dev |
| AI model benchmarks | Cost/latency comparisons | Community benchmarks |

## Fallback: No MCP Search

If no search MCP is available:
```bash
# Use curl for web content
curl -sL "https://en.wikipedia.org/wiki/$TOPIC" | python3 -c "
import sys, html, re
text = html.unescape(sys.stdin.read())
text = re.sub('<[^>]+>', ' ', text)
text = re.sub(r'\s+', ' ', text).strip()
print(text[:3000])
"
```

## Best Practices

1. **Ask clarifying questions** before broad research
2. **Break into sub-questions** — better results than one vague query
3. **Cite sources** — include URLs for every claim
4. **Synthesize** — don't just dump search results
5. **Recommend** — end with actionable suggestions for ZES
6. **Compare** — when choosing between options, make a table
7. **Respect rate limits** — space out requests to avoid blocking

**Remember**: Research is only useful if it leads to a decision. Always end with a recommendation.
