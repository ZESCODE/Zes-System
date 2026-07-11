// ZES Browser Agent — 9Router Agent Plugin
// Adds autonomous browser agent capability using 9Router via existing MCP tools

import { ToolRepair } from './tool-repair.js';

export class BrowserAgent {
  constructor(toolRegistry) {
    this.tools = toolRegistry;
    this.repair = new ToolRepair(toolRegistry);
    this.running = false;
    this.maxIterations = 30;
    this.defaultModel = 'groq/llama-3.3-70b-versatile';
  }

  async run(task, options = {}) {
    if (options.stream) {
      options.stream.push({
        type: 'step',
        timestamp: Date.now(),
        iteration: 0,
        message: `Starting task: ${task.slice(0, 100)}`,
      });
    }
    if (this.running) throw new Error('Agent already running');
    this.running = true;

    const model = options.model || 'groq/llama-3.3-70b-versatile';
    const apiUrl = 'http://localhost:20128/v1/chat/completions';
    const maxIter = options.maxIterations || this.maxIterations;
    const messages = [
      { role: 'system', content: this._systemPrompt() },
      { role: 'user', content: task }
    ];

    try {
      for (let i = 0; i < maxIter; i++) {
        // Capture current page state
        const state = await this._capturePageState();

        // Build the prompt with state
        const stateMsg = {
          role: 'user',
          content: `Page state:\nURL: ${state.url}\nTitle: ${state.title}\nVisible text:\n${state.text}\n\nWhat action should I take next? Respond with either COMPLETE (if the task is done) or the tool_name and args JSON.`
        };
        messages.push(stateMsg);

        // Call 9Router
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model,
            messages,
            temperature: 0.3,
            max_tokens: 512,
          })
        });

        if (!response.ok) throw new Error(`9Router error: ${response.status}`);
        const raw = await response.text();
        // 9Router may return trailing SSE data after JSON
        const jsonPart = raw.split("\n")[0];
        const data = JSON.parse(jsonPart);
        const text = (data.choices?.[0]?.message?.content || '').trim();
        messages.push({ role: 'assistant', content: text });

        // Parse response
        if (text.toUpperCase().startsWith('COMPLETE') || text.includes('"complete"')) {
          return { success: true, iterations: i + 1, summary: text };
        }

        const parsed = this._parseAction(text);
        if (!parsed) {
          messages.push({ role: 'user', content: 'Invalid response format. Respond with COMPLETE or a valid JSON like: {"tool":"click","args":{"selector":"..."}}' });
          continue;
        }

        // Use ToolRepair for fuzzy matching, field aliasing, and validation
        const repaired = this.repair.repair(parsed);
        if (!repaired) {
          const availableTools = this.tools.list().map(t => t.name).join(', ');
          messages.push({ role: 'user', content: `Unknown tool: "${parsed.tool || '(unknown)'}". Available: ${availableTools}. Respond with one of these tool names.` });
          continue;
        }

        // Execute the repaired tool
        const tool = this.tools.get(repaired.tool);
        const result = await tool.execute(repaired.args || {});
        const resultText = result?.content?.[0]?.text || JSON.stringify(result);
        messages.push({ role: 'user', content: `Tool ${repaired.tool} result: ${resultText.slice(0, 2000)}` });

        // Emit streaming event
        if (options && options.stream) {
          options.stream.push({
            type: 'toolCall',
            timestamp: Date.now(),
            tool: repaired.tool,
            args: repaired.args,
            result: resultText.slice(0, 500),
          });
        }
      }

      return { success: false, error: 'Max iterations reached' };
    } finally {
      this.running = false;
    }
  }

  _systemPrompt() {
    return `You are a browser automation agent. You control a web browser through available tools.

Available tools:
- browse: Navigate to a URL. Args: {url: string}
- click/ext_click: Click an element. Args: {selector: string}
- type/ext_type: Type text. Args: {selector: string, text: string}
- extract/ext_extract: Get page text. Args: {selector?: string}
- screenshot: Capture the viewport. Args: {}
- ext_getContext: Get page context. Args: {}
- list_tabs: List open tabs. Args: {}

Rules:
1. After each action, wait for the result before deciding next action
2. When the task is done, respond with COMPLETE followed by a brief summary
3. Respond with a JSON object exactly like: {"tool": "click", "args": {"selector": "#btn"}}
4. Extract text before filling forms to understand page structure
5. Use screenshot for visual verification when needed
6. Work step by step — one action at a time`;
  }

  _parseAction(text) {
    // Try to find JSON in the response
    const jsonMatch = text.match(/\{[\s\S]*"tool"[\s\S]*"args"[\s\S]*\}/);
    if (jsonMatch) {
      try { return JSON.parse(jsonMatch[0]); } catch {}
    }
    // Try bare JSON object
    try {
      const parsed = JSON.parse(text);
      if (parsed.tool) return parsed;
    } catch {}
    return null;
  }

  async _capturePageState() {
    try {
      const ctxTool = this.tools.get('ext_getContext');
      if (ctxTool) {
        const r = await ctxTool.execute({});
        const text = r?.content?.[0]?.text || '';
        const lines = text.split('\n');
        const url = lines.find(l => l.startsWith('URL:'))?.slice(4).trim() || '';
        const title = lines.find(l => l.startsWith('Title:'))?.slice(6).trim() || '';
        const textBody = lines.slice(2).join('\n');
        return { url, title, text: textBody };
      }
    } catch {}
    return { url: '', title: '', text: '' };
  }
}
