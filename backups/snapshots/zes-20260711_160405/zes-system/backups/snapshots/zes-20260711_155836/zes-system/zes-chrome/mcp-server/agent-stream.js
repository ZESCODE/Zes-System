// Agent Stream — streaming events pattern from OpenClaw's agent-core
// Enables event-driven agent loop with subscribe/push/end lifecycle

/**
 * Create an event stream for agent lifecycle events.
 * Events: toolCall, toolResult, step, error, done
 */
export function createAgentStream() {
  const listeners = [];
  let ended = false;
  let finalResult = null;

  return {
    push(event) {
      if (!ended) {
        for (const fn of listeners) {
          try { fn(event); } catch (err) { console.error('[AgentStream] listener error:', err); }
        }
      }
      return this;
    },

    subscribe(fn) {
      listeners.push(fn);
      return () => {
        const i = listeners.indexOf(fn);
        if (i >= 0) listeners.splice(i, 1);
      };
    },

    unsubscribe(fn) {
      const i = listeners.indexOf(fn);
      if (i >= 0) listeners.splice(i, 1);
    },

    end(result) {
      if (ended) return;
      ended = true;
      finalResult = result;
      this.push({ type: 'done', timestamp: Date.now(), result });
    },

    getResult() { return finalResult; },
    get ended() { return ended; },
  };
}

/**
 * Run an agent with streaming event output.
 * Returns { stream, promise } — subscribe to stream for progress, await promise for result.
 */
export function runAgentStream(task, agent, options = {}) {
  const stream = createAgentStream();
  const { onEvent, signal } = options;

  if (onEvent) stream.subscribe(onEvent);

  const promise = (async () => {
    try {
      stream.push({
        type: 'start',
        timestamp: Date.now(),
        task,
        model: options.model || agent.defaultModel || 'groq/llama-3.3-70b-versatile',
      });

      const result = await agent.run(task, {
        ...options,
        stream,
        signal,
      });

      stream.end(result);
      return result;
    } catch (err) {
      stream.push({ type: 'error', timestamp: Date.now(), error: err.message });
      stream.end({ success: false, error: err.message });
      throw err;
    }
  })();

  return { stream, promise };
}

/**
 * Create an SSE-compatible response from an agent stream.
 * Returns a generator that yields SSE-formatted strings.
 */
export async function* agentStreamToSSE(stream, task) {
  yield `event: start\ndata: ${JSON.stringify({ type: 'start', task })}\n\n`;

  const events = [];
  stream.subscribe((event) => {
    events.push(event);
  });

  const result = await stream.promise;

  for (const event of events) {
    if (event.type === 'done') continue;
    yield `event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`;
  }

  yield `event: done\ndata: ${JSON.stringify(result)}\n\n`;
}
