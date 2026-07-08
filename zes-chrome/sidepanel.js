// zesChrome Side Panel — Chat, Agent Control, Services, History

let chatHistory = [];
let agentActive = false;

document.addEventListener('DOMContentLoaded', () => {
  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
    });
  });

  // Chat send
  const sendBtn = document.getElementById('sendBtn');
  const chatInput = document.getElementById('chatInput');
  sendBtn.addEventListener('click', () => sendMessage());
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Agent toggle
  document.getElementById('toggleAgentBtn').addEventListener('click', async () => {
    const result = await chrome.runtime.sendMessage({ type: 'TOGGLE_AGENT' });
    agentActive = result.active;
    updateAgentUI();
  });

  // Service connect buttons
  document.querySelectorAll('.connect-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      chrome.tabs.create({
        url: `http://localhost:8083/auth/${btn.dataset.service}`
      });
    });
  });

  // Settings button
  document.getElementById('settingsBtn').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:8083/#settings' });
  });

  // Load initial state
  loadState();
});

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, 'user');
  input.value = '';
  const thinkingId = addMessage('Thinking...', 'system');

  try {
    const response = await chrome.runtime.sendMessage({
      type: 'CHAT_MESSAGE',
      text,
      history: chatHistory.slice(-10),
      model: 'groq/llama-3.3-70b-versatile'
    });

    document.getElementById(thinkingId)?.remove();

    if (response.error) {
      addMessage(`Error: ${response.error}`, 'system');
    } else {
      addMessage(response.text || response.message || JSON.stringify(response), 'assistant');
    }
  } catch (err) {
    document.getElementById(thinkingId)?.remove();
    addMessage(`Error: ${err.message}`, 'system');
  }
}

function addMessage(text, role) {
  const messages = document.getElementById('messages');
  const id = `msg-${Date.now()}`;
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.id = id;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  chatHistory.push({ role, content: text });
  return id;
}

async function loadState() {
  try {
    const state = await chrome.runtime.sendMessage({ type: 'GET_STATE' });
    agentActive = state.active;
    updateAgentUI();

    if (state.currentTabId) {
      const tab = await chrome.tabs.get(state.currentTabId);
      document.getElementById('currentTab').textContent = tab?.title || 'Unknown';
    }
  } catch (err) {
    console.error('Failed to load state:', err);
  }
}

function updateAgentUI() {
  const indicator = document.getElementById('agentStatusIndicator');
  const btn = document.getElementById('toggleAgentBtn');
  if (agentActive) {
    indicator.textContent = '● Active';
    indicator.style.color = 'var(--success)';
    btn.textContent = 'Deactivate';
  } else {
    indicator.textContent = '● Idle';
    indicator.style.color = 'var(--muted)';
    btn.textContent = 'Activate Agent';
  }
}
