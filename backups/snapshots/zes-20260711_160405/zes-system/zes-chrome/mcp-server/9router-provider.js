// 9Router Provider Plugin — modeled on OpenClaw's plugin-sdk provider pattern
// Formal model catalog, streaming, auth, and model list

const NINE_ROUTER_BASE = 'http://localhost:20128/v1';

export class NineRouterProvider {
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || NINE_ROUTER_BASE;
    this.defaultModel = options.defaultModel || 'groq/llama-3.3-70b-versatile';
    this.auth = options.auth || { type: 'none' };
    this._models = null;
  }

  // ── Model catalog ──────────────────────────────────────────

  get modelCatalog() {
    return {
      'groq/llama-3.3-70b-versatile': {
        api: 'openai-completions',
        contextTokens: 32768,
        description: 'Groq Llama 3.3 70B (fast, general purpose)',
        provider: 'groq',
      },
      'groq/llama-4-scout-17b': {
        api: 'openai-completions',
        contextTokens: 32768,
        description: 'Groq Llama 4 Scout 17B',
        provider: 'groq',
      },
      'gh/gpt-5.4-mini-free-auto': {
        api: 'openai-completions',
        contextTokens: 262144,
        description: 'GitHub Copilot GPT-5.4 Mini (free tier, auto-routed)',
        provider: 'github',
      },
      'deepseek/deepseek-v4-flash-free': {
        api: 'openai-completions',
        contextTokens: 262144,
        description: 'DeepSeek V4 Flash (free, large context)',
        provider: 'deepseek',
      },
      'anthropic/claude-sonnet-4-6': {
        api: 'openai-completions',
        contextTokens: 200000,
        description: 'Anthropic Claude Sonnet 4.6',
        provider: 'anthropic',
      },
      'openrouter/anthropic/claude-3.5': {
        api: 'openai-completions',
        contextTokens: 200000,
        description: 'OpenRouter Claude 3.5',
        provider: 'openrouter',
      },
      'nvidia/nemotron-4-340b': {
        api: 'openai-completions',
        contextTokens: 16384,
        description: 'NVIDIA Nemotron 4 340B',
        provider: 'nvidia',
      },
      'google/gemini-3.1-flash-lite': {
        api: 'openai-completions',
        contextTokens: 131072,
        description: 'Google Gemini 3.1 Flash Lite',
        provider: 'gemini',
      },
    };
  }

  // ── Chat completions ───────────────────────────────────────

  async chat(messages, options = {}) {
    const model = options.model || this.defaultModel;
    const body = {
      model,
      messages,
      temperature: options.temperature ?? 0.7,
      max_tokens: options.maxTokens ?? 4096,
      stream: options.stream ?? false,
    };

    const headers = { 'Content-Type': 'application/json' };
    this._applyAuthHeaders(headers);

    const res = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const errorText = await res.text().catch(() => res.statusText);
      throw new Error(`9Router ${res.status}: ${errorText.slice(0, 200)}`);
    }

    if (options.stream) {
      return this._handleStream(res);
    }

    const data = await res.json();
    return data.choices?.[0]?.message?.content || '';
  }

  async *_handleStream(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data === '[DONE]') return;
          try {
            const parsed = JSON.parse(data);
            const content = parsed.choices?.[0]?.delta?.content || '';
            if (content) yield content;
          } catch { /* skip malformed chunks */ }
        }
      }
    }
  }

  // ── Embeddings ─────────────────────────────────────────────

  async embed(input, model = '') {
    const body = {
      model: model || this.defaultModel,
      input: Array.isArray(input) ? input : [input],
    };
    const headers = { 'Content-Type': 'application/json' };
    this._applyAuthHeaders(headers);

    const res = await fetch(`${this.baseUrl}/embeddings`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`9Router embed ${res.status}`);
    const data = await res.json();
    return data.data?.map(d => d.embedding) || [];
  }

  // ── Models list ─────────────────────────────────────────────

  async listModels(refresh = false) {
    if (this._models && !refresh) return this._models;
    try {
      const headers = {};
      this._applyAuthHeaders(headers);
      const res = await fetch(`${this.baseUrl}/models`, { headers });
      if (res.ok) {
        const data = await res.json();
        this._models = (data.data || data).map(m => ({
          id: m.id,
          owned_by: m.owned_by || 'unknown',
        }));
        return this._models;
      }
    } catch {}
    // Fallback to catalog
    return Object.entries(this.modelCatalog).map(([id, config]) => ({
      id,
      owned_by: config.provider,
    }));
  }

  // ── Connection test ─────────────────────────────────────────

  async testConnection() {
    try {
      const res = await fetch(`${this.baseUrl}/models`);
      return res.ok;
    } catch {
      return false;
    }
  }

  // ── Auth helpers ──────────────────────────────────────────

  setApiKey(key) {
    this.auth = { type: 'api-key', key };
  }

  _applyAuthHeaders(headers) {
    if (this.auth.type === 'api-key' && this.auth.key) {
      headers['Authorization'] = `Bearer ${this.auth.key}`;
    }
    if (this.auth.type === 'header' && this.auth.header) {
      headers[this.auth.header.name] = this.auth.header.value;
    }
    if (this.auth.type === 'token') {
      const { x9rCliToken } = this._getCliToken();
      if (x9rCliToken) headers['x-9r-cli-token'] = x9rCliToken;
    }
  }

  _getCliToken() {
    try {
      const fs = require('fs');
      const path = require('path');
      const home = process.env.HOME || '/data/data/com.termux/files/home';
      const mid = fs.readFileSync(path.join(home, '.9router/machine-id'), 'utf8').trim();
      const secret = fs.readFileSync(path.join(home, '.9router/auth/cli-secret'), 'utf8').trim();
      const crypto = require('crypto');
      const token = crypto.createHash('sha256').update(mid + '9r-cli-auth' + secret).digest('hex').slice(0, 16);
      return { x9rCliToken: token };
    } catch {
      return {};
    }
  }
}

// ── Provider plugin factory ─────────────────────────────────

export function create9RouterProvider(options = {}) {
  return new NineRouterProvider(options);
}
