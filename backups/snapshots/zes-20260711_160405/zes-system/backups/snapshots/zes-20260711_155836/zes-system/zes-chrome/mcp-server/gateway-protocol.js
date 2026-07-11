// Gateway Protocol — typed agent events between Codex ↔ Chrome
// Ported from OpenClaw's gateway-protocol pattern (TypeBox-style schemas)

// ── Event types ─────────────────────────────────────────────

export const EventTypes = {
  AGENT_START: 'agent.start',
  AGENT_STEP: 'agent.step',
  AGENT_TOOL_CALL: 'agent.toolCall',
  AGENT_TOOL_RESULT: 'agent.toolResult',
  AGENT_ERROR: 'agent.error',
  AGENT_COMPLETE: 'agent.complete',
  AGENT_DONE: 'agent.done',
  PAGE_STATE: 'page.state',
  PAGE_NAVIGATED: 'page.navigated',
  SYSTEM_INFO: 'system.info',
  PING: 'ping',
  PONG: 'pong',
};

const EVENT_TYPE_VALUES = new Set(Object.values(EventTypes));

// ── Event creation ─────────────────────────────────────────

export function createEvent(type, data = {}) {
  if (!EVENT_TYPE_VALUES.has(type)) {
    throw new Error(`Unknown event type: ${type}`);
  }
  return {
    type,
    timestamp: Date.now(),
    id: `evt_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`,
    data,
  };
}

export function createAgentStart(task, model) {
  return createEvent(EventTypes.AGENT_START, { task, model });
}

export function createAgentStep(iteration, message) {
  return createEvent(EventTypes.AGENT_STEP, { iteration, message });
}

export function createToolCall(tool, args) {
  return createEvent(EventTypes.AGENT_TOOL_CALL, { tool, args });
}

export function createToolResult(tool, result, durationMs) {
  return createEvent(EventTypes.AGENT_TOOL_RESULT, { tool, result, durationMs });
}

export function createAgentComplete(iterations, summary) {
  return createEvent(EventTypes.AGENT_COMPLETE, { iterations, summary });
}

export function createAgentError(error) {
  return createEvent(EventTypes.AGENT_ERROR, { error });
}

// ── Validation ────────────────────────────────────────────────

/**
 * Validate an event object against the protocol schema.
 * Returns { valid, error }.
 */
export function validateEvent(event) {
  if (!event || typeof event !== 'object') {
    return { valid: false, error: 'event must be an object' };
  }
  if (!event.type) {
    return { valid: false, error: 'event missing required field: type' };
  }
  if (!EVENT_TYPE_VALUES.has(event.type)) {
    return { valid: false, error: `unknown event type: ${event.type}` };
  }
  if (!event.timestamp || typeof event.timestamp !== 'number') {
    return { valid: false, error: 'event missing/invalid timestamp' };
  }
  return { valid: true, error: null };
}

// ── SSE formatting ──────────────────────────────────────────

export function formatSSE(event) {
  return `event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`;
}

// ── Event bus ────────────────────────────────────────────────

export class EventBus {
  constructor() {
    this._listeners = new Map();
  }

  on(type, handler) {
    if (!this._listeners.has(type)) this._listeners.set(type, []);
    this._listeners.get(type).push(handler);
    return () => this.off(type, handler);
  }

  off(type, handler) {
    const handlers = this._listeners.get(type);
    if (handlers) {
      const i = handlers.indexOf(handler);
      if (i >= 0) handlers.splice(i, 1);
    }
  }

  emit(type, data = {}) {
    const event = createEvent(type, data);
    const handlers = this._listeners.get(type);
    if (handlers) {
      for (const handler of handlers) {
        try { handler(event); } catch (err) {
          console.error(`[EventBus] handler error for ${type}:`, err);
        }
      }
    }
    // Also notify wildcard listeners
    const all = this._listeners.get('*');
    if (all) {
      for (const handler of all) {
        try { handler(event); } catch (err) {
          console.error(`[EventBus] wildcard handler error:`, err);
        }
      }
    }
    return event;
  }
}
