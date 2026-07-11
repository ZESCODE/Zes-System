// Background Service Worker — zesChrome
// Tab tracking, message routing, proxy to Dashboard (:8083)

const DASHBOARD_URL = 'http://localhost:8083';

let agentState = {
  active: false,
  currentTask: null,
  currentTabId: null
};

chrome.tabs.onActivated.addListener(({ tabId }) => {
  agentState.currentTabId = tabId;
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'GET_STATE':
      sendResponse(agentState);
      break;

    case 'TOGGLE_AGENT':
      agentState.active = !agentState.active;
      sendResponse({ active: agentState.active });
      break;

    case 'CAPTURE_SCREENSHOT':
      chrome.tabs.captureVisibleTab(agentState.currentTabId, { format: 'png' })
        .then(dataUrl => sendResponse({ screenshot: dataUrl }))
        .catch(err => sendResponse({ error: err.message }));
      return true;

    case 'EXECUTE_ACTION':
      executeAction(message.action, message.args)
        .then(result => sendResponse(result))
        .catch(err => sendResponse({ error: err.message }));
      return true;

    case 'CHAT_MESSAGE':
      proxyToDashboard('/api/agent/chat', {
        message: message.text,
        history: message.history || [],
        model: message.model || 'groq/llama-3.3-70b-versatile'
      })
        .then(res => sendResponse(res))
        .catch(err => sendResponse({ error: err.message }));
      return true;

    case 'PAGE_LOADED':
      console.log(`Page loaded: ${message.title} (${message.url})`);
      sendResponse({ received: true });
      return true;  // Keep port open for MV3 async response
  }
});

async function executeAction(action, args) {
  const tabId = agentState.currentTabId;
  if (!tabId) throw new Error('No active tab');

  if (action === 'click') {
    await chrome.scripting.executeScript({
      target: { tabId },
      func: (selector) => {
        const el = document.querySelector(selector);
        if (!el) throw new Error(`Element not found: ${selector}`);
        el.click();
        return { success: true };
      },
      args: [args.selector]
    });
  } else if (action === 'type') {
    await chrome.scripting.executeScript({
      target: { tabId },
      func: (selector, text) => {
        const el = document.querySelector(selector);
        if (!el) throw new Error(`Element not found: ${selector}`);
        el.value = text;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        return { success: true };
      },
      args: [args.selector, args.text]
    });
  } else if (action === 'extract') {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: (selector) => {
        if (selector === 'body') return document.body.innerText.slice(0, 10000);
        const el = document.querySelector(selector);
        return el ? el.innerText || el.value || el.textContent : null;
      },
      args: [args.selector || 'body']
    });
    return { text: results[0]?.result || '' };
  } else if (action === 'wait') {
    return await waitForElement(args.selector, args.timeout || 10000);
  }

  return { success: true };
}

async function waitForElement(selector, timeoutMs) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const results = await chrome.scripting.executeScript({
      target: { tabId: agentState.currentTabId },
      func: (sel) => !!document.querySelector(sel),
      args: [selector]
    });
    if (results[0]?.result) return { text: `Element appeared: ${selector}` };
    await new Promise(r => setTimeout(r, 500));
  }
  return { text: `Timeout waiting for: ${selector}` };
}

async function proxyToDashboard(path, body) {
  const res = await fetch(`${DASHBOARD_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Dashboard error: ${res.status}`);
  return res.json();
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});
