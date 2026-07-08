// zesChrome Popup — Quick actions and status

document.addEventListener('DOMContentLoaded', async () => {
  const state = await chrome.runtime.sendMessage({ type: 'GET_STATE' });

  // Agent toggle
  const toggle = document.getElementById('agentToggle');
  toggle.checked = state.active;
  toggle.addEventListener('change', async () => {
    await chrome.runtime.sendMessage({ type: 'TOGGLE_AGENT' });
  });

  // Check service statuses
  checkStatuses();

  // Open side panel
  document.getElementById('openSidePanel').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      await chrome.sidePanel.open({ tabId: tab.id });
      window.close();
    }
  });

  // Capture screenshot
  document.getElementById('captureScreenshot').addEventListener('click', async () => {
    const result = await chrome.runtime.sendMessage({ type: 'CAPTURE_SCREENSHOT' });
    if (result.screenshot) {
      const w = window.open('');
      w.document.write(`<img src="${result.screenshot}" style="max-width:100%">`);
    }
  });

  // Open dashboard
  document.getElementById('openDashboard').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:8083' });
  });
});

async function checkStatuses() {
  // MCP server on :5901
  try {
    const r = await fetch('http://localhost:5901/health');
    if (r.ok) document.getElementById('mcpStatus').classList.add('online');
  } catch {}

  // Dashboard on :8083
  try {
    const r = await fetch('http://localhost:8083/');
    if (r.ok) document.getElementById('dashboardStatus').classList.add('online');
  } catch {}

  // 9Router on :20128
  try {
    const r = await fetch('http://localhost:20128/');
    if (r.ok || r.status === 307) document.getElementById('modelStatus').classList.add('online');
  } catch {}
}
