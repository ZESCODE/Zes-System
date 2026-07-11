// Tool Call Repair — ported from OpenClaw's tool-call-repair/
// Fixes malformed LLM tool calls: fuzzy names, missing fields, wrong types

import { SchemaValidator } from './schema-validate.js';

// Common LLM misspellings of tool names
const FUZZY_TOOL_MAP = {
  'clik': 'click',
  'clcik': 'click',
  'clck': 'click',
  'clic': 'click',
  'clike': 'click',
  'tyep': 'type',
  'typ': 'type',
  'typpe': 'type',
  'type_text': 'type',
  'navigate': 'browse',
  'nav': 'browse',
  'goto': 'browse',
  'go': 'browse',
  'nvagiate': 'browse',
  'navegate': 'browse',
  'extract_text': 'extract',
  'get_text': 'extract',
  'page_text': 'extract',
  'screnshot': 'screenshot',
  'screen_shot': 'screenshot',
  'screen': 'screenshot',
  'capture': 'screenshot',
  'get_context': 'ext_getContext',
  'context': 'ext_getContext',
  'page_context': 'ext_getContext',
  'list_tabs': 'list_tabs',
  'tabs': 'list_tabs',
  'open_tabs': 'list_tabs',
  'ext_click': 'ext_click',
  'ext_type': 'ext_type',
  'ext_extract': 'ext_extract',
  'browes': 'browse',
  'browze': 'browse',
};

export class ToolRepair {
  constructor(toolRegistry) {
    this.tools = toolRegistry;
    this.validator = new SchemaValidator();
    this._stats = { repaired: 0, passed: 0, failed: 0 };

    // Register schemas from the tool registry
    for (const tool of this.tools.list()) {
      if (tool.inputSchema) {
        this.validator.register(tool.name, tool.inputSchema);
      }
    }
  }

  getStats() { return { ...this._stats }; }

  /**
   * Repair a tool call object.
   * Accepts various LLM output formats and normalizes them.
   * Returns { tool, args, repaired } or null if unrepairable.
   */
  repair(call) {
    if (!call || typeof call !== 'object') {
      this._stats.failed++;
      return null;
    }

    // Step 1: Extract tool name from various formats
    let toolName = call.tool || call.name || call.action || call.function;
    if (!toolName && call.type === 'function') {
      toolName = call.function?.name;
    }
    if (!toolName) {
      this._stats.failed++;
      return null;
    }

    // Step 2: Fuzzy match tool name
    const fixedName = FUZZY_TOOL_MAP[toolName.toLowerCase()] || toolName;
    const tool = this.tools.get(fixedName);
    if (!tool) {
      this._stats.failed++;
      return null;
    }

    // Step 3: Extract args from various formats
    let args = call.args || call.arguments || call.parameters || call.function?.arguments || {};

    // If args is a string, try JSON parse
    if (typeof args === 'string') {
      try { args = JSON.parse(args); } catch { args = { selector: args, text: args }; }
    }

    if (typeof args !== 'object' || args === null) {
      args = {};
    }

    // Ensure string coercion for common fields
    for (const key of ['selector', 'text', 'url']) {
      if (key in args && typeof args[key] !== 'string') {
        args[key] = String(args[key]);
      }
    }

    // Handle aliased field names LLMs often use
    if (args.selector === undefined) {
      if (args.css) args.selector = args.css;
      else if (args.query) args.selector = args.query;
      else if (args.element) args.selector = args.element;
      else if (args.id) args.selector = '#' + args.id;
      else if (args.class) args.selector = '.' + args.class;
      else if (args.name) args.selector = `[name="${args.name}"]`;
    }
    if (args.url === undefined) {
      if (args.link) args.url = args.link;
      else if (args.href) args.url = args.href;
      else if (args.target) args.url = args.target;
    }
    if (args.text === undefined) {
      if (args.value) args.text = args.value;
      else if (args.content) args.text = args.content;
      else if (args.input) args.text = args.input;
    }

    // Only keep relevant keys for the tool
    const relevantKeys = ['selector', 'text', 'url', 'fullPage'];
    const cleanArgs = {};
    for (const k of relevantKeys) {
      if (k in args) cleanArgs[k] = args[k];
    }

    // Step 4: Validate
    const validation = this.validator.validate(normalizedName, cleanArgs);
    const wasRepaired = toolName !== normalizedName || JSON.stringify(args) !== JSON.stringify(cleanArgs);

    if (validation.valid) {
      if (wasRepaired) this._stats.repaired++;
      else this._stats.passed++;
      return { tool: normalizedName, args: cleanArgs, repaired: wasRepaired };
    }

    // Step 5: If validation failed, try one more fix pass
    // Add missing required fields with defaults
    const schema = tool.inputSchema;
    if (schema && schema.required && schema.properties) {
      for (const req of schema.required) {
        if (!(req in cleanArgs) && schema.properties[req]) {
          const propSchema = schema.properties[req];
          if (propSchema.type === 'string' && propSchema.default !== undefined) {
            cleanArgs[req] = propSchema.default;
          }
        }
      }
    }

    this._stats.repaired++;
    return { tool: normalizedName, args: cleanArgs, repaired: true };
  }
}
