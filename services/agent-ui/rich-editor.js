/**
 * ZES Rich Editor — Enhanced chat input for Agent UI (:8084)
 * Adds: tab completion, command palette, slash command autocomplete, code formatting
 */
(function() {
  'use strict';

  const SLASH_COMMANDS = [
    { cmd: '/plan', desc: 'Create implementation plan', icon: '📋' },
    { cmd: '/tdd', desc: 'Test-driven development', icon: '🧪' },
    { cmd: '/code-review', desc: 'Review code for issues', icon: '🔍' },
    { cmd: '/build-fix', desc: 'Fix build errors', icon: '🔧' },
    { cmd: '/verify', desc: 'Run full verification', icon: '✅' },
    { cmd: '/refactor', desc: 'Refactor code', icon: '🔄' },
    { cmd: '/test', desc: 'Generate/run tests', icon: '🧪' },
    { cmd: '/docs', desc: 'Generate documentation', icon: '📝' },
    { cmd: '/debug', desc: 'Debug runtime issues', icon: '🐛' },
    { cmd: '/help', desc: 'Show all commands', icon: '❓' },
    { cmd: '/architect', desc: 'Design system architecture', icon: '🏗️' },
    { cmd: '/pact', desc: 'Check phase gate pacts', icon: '📜' },
  ];

  let chatInput = null;
  let sendBtn = null;
  let suggestionsDropdown = null;
  let activeSuggestionIndex = -1;

  // ─── Inject styles ────────────────────────────────────────────
  function injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .zes-suggestions {
        position: absolute;
        bottom: 100%;
        left: 0;
        right: 0;
        background: #1e293b;
        border: 1px solid rgba(249,115,22,0.3);
        border-radius: 10px;
        margin-bottom: 4px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 100;
        box-shadow: 0 -8px 24px rgba(0,0,0,0.3);
      }
      .zes-suggestion-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        cursor: pointer;
        font-size: 13px;
        color: #cbd5e1;
        transition: background 0.1s;
        border-bottom: 1px solid rgba(255,255,255,0.04);
      }
      .zes-suggestion-item:last-child { border-bottom: none; }
      .zes-suggestion-item.active, .zes-suggestion-item:hover {
        background: rgba(249,115,22,0.15);
        color: #f97316;
      }
      .zes-suggestion-item .cmd { font-family: monospace; font-weight: 600; color: #f97316; min-width: 100px; }
      .zes-suggestion-item .desc { color: #64748b; font-size: 12px; }
      .zes-suggestion-item .icon { font-size: 16px; }
      .zes-input-wrapper { position: relative; flex: 1; display: flex; }
      .zes-code-btn {
        position: absolute;
        right: 4px;
        bottom: 4px;
        background: transparent;
        border: 1px solid rgba(255,255,255,0.1);
        color: #64748b;
        border-radius: 6px;
        padding: 2px 6px;
        font-size: 10px;
        cursor: pointer;
        z-index: 5;
      }
      .zes-code-btn:hover { border-color: #f97316; color: #f97316; }
    `;
    document.head.appendChild(style);
  }

  // ─── Create suggestions dropdown ──────────────────────────────
  function createSuggestions() {
    suggestionsDropdown = document.createElement('div');
    suggestionsDropdown.className = 'zes-suggestions';
    suggestionsDropdown.style.display = 'none';
    chatInput.parentElement.style.position = 'relative';
    chatInput.parentElement.appendChild(suggestionsDropdown);
  }

  // ─── Show suggestions ─────────────────────────────────────────
  function showSuggestions(filter) {
    if (!filter.startsWith('/')) {
      suggestionsDropdown.style.display = 'none';
      return;
    }

    const matching = SLASH_COMMANDS.filter(s => s.cmd.startsWith(filter));
    if (matching.length === 0 || matching.length === 1 && matching[0].cmd === filter) {
      suggestionsDropdown.style.display = 'none';
      return;
    }

    suggestionsDropdown.innerHTML = matching.map((s, i) => 
      `<div class="zes-suggestion-item ${i === activeSuggestionIndex ? 'active' : ''}" data-index="${i}">
        <span class="icon">${s.icon}</span>
        <span class="cmd">${s.cmd}</span>
        <span class="desc">${s.desc}</span>
      </div>`
    ).join('');

    suggestionsDropdown.style.display = 'block';

    // Click handlers
    suggestionsDropdown.querySelectorAll('.zes-suggestion-item').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.dataset.index);
        if (idx >= 0 && idx < matching.length) {
          chatInput.value = matching[idx].cmd + ' ';
          suggestionsDropdown.style.display = 'none';
          chatInput.focus();
          // Trigger input event for auto-resize
          chatInput.dispatchEvent(new Event('input'));
        }
      });
    });
  }

  // ─── Handle keyboard events ───────────────────────────────────
  function handleKeydown(e) {
    const val = chatInput.value;
    const isSuggesting = suggestionsDropdown.style.display === 'block';
    const matching = val.startsWith('/') ? SLASH_COMMANDS.filter(s => s.cmd.startsWith(val)) : [];

    // Tab completion
    if (e.key === 'Tab' && val.startsWith('/')) {
      e.preventDefault();
      if (matching.length > 0) {
        chatInput.value = matching[0].cmd + ' ';
        suggestionsDropdown.style.display = 'none';
        chatInput.dispatchEvent(new Event('input'));
      }
      return;
    }

    // Arrow keys for suggestions
    if (isSuggesting) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        activeSuggestionIndex = Math.min(activeSuggestionIndex + 1, matching.length - 1);
        updateActiveSuggestion();
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        activeSuggestionIndex = Math.max(activeSuggestionIndex - 1, 0);
        updateActiveSuggestion();
        return;
      }
      if (e.key === 'Enter' && activeSuggestionIndex >= 0 && activeSuggestionIndex < matching.length) {
        e.preventDefault();
        chatInput.value = matching[activeSuggestionIndex].cmd + ' ';
        suggestionsDropdown.style.display = 'none';
        activeSuggestionIndex = -1;
        chatInput.dispatchEvent(new Event('input'));
        return;
      }
      if (e.key === 'Escape') {
        suggestionsDropdown.style.display = 'none';
        activeSuggestionIndex = -1;
        return;
      }
    }

    // Enter to send (without Shift)
    if (e.key === 'Enter' && !e.shiftKey && val.trim()) {
      e.preventDefault();
      sendBtn.click();
    }
  }

  function updateActiveSuggestion() {
    const items = suggestionsDropdown.querySelectorAll('.zes-suggestion-item');
    items.forEach((el, i) => {
      el.classList.toggle('active', i === activeSuggestionIndex);
      if (i === activeSuggestionIndex) {
        el.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  // ─── Handle input events ──────────────────────────────────────
  function handleInput() {
    const val = chatInput.value;
    activeSuggestionIndex = -1;
    showSuggestions(val);
    
    // Enable/disable send button
    if (sendBtn) sendBtn.disabled = !val.trim();
  }

  // ─── Insert code block ────────────────────────────────────────
  function insertCodeBlock() {
    const start = chatInput.selectionStart;
    const end = chatInput.selectionEnd;
    const selected = chatInput.value.substring(start, end);
    const before = chatInput.value.substring(0, start);
    const after = chatInput.value.substring(end);
    
    if (selected) {
      chatInput.value = before + '```\n' + selected + '\n```' + after;
    } else {
      chatInput.value = before + '```\n\n```' + after;
      chatInput.selectionStart = chatInput.selectionEnd = before.length + 4;
    }
    chatInput.focus();
    chatInput.dispatchEvent(new Event('input'));
  }

  // ─── Init ─────────────────────────────────────────────────────
  function init() {
    chatInput = document.getElementById('chat-input') || document.querySelector('textarea');
    sendBtn = document.getElementById('send-btn') || document.querySelector('button[onclick*="send"]');

    if (!chatInput) {
      setTimeout(init, 500);
      return;
    }

    injectStyles();
    createSuggestions();

    // Override default Enter behavior
    chatInput.addEventListener('keydown', handleKeydown);
    chatInput.addEventListener('input', handleInput);

    // Set placeholder
    chatInput.placeholder = 'Message Agent... (/plan, /tdd, /help) · Tab to complete';

    // Add code block button
    const codeBtn = document.createElement('button');
    codeBtn.className = 'zes-code-btn';
    codeBtn.textContent = '</>';
    codeBtn.title = 'Insert code block';
    codeBtn.addEventListener('click', insertCodeBlock);
    chatInput.parentElement.appendChild(codeBtn);

    // Expose helper for global sendSlash
    window.sendSlash = function(cmd) {
      chatInput.value = '/' + cmd + ' ';
      chatInput.dispatchEvent(new Event('input'));
      setTimeout(() => {
        if (sendBtn && !sendBtn.disabled) sendBtn.click();
      }, 50);
    };

    console.log('[ZES Rich Editor] Loaded');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
