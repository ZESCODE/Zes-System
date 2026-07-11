// zesChrome Content Script — runs on every page
// Reports page context and handles element interaction

(() => {
  'use strict';

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.action) {
      case 'GET_PAGE_CONTEXT':
        sendResponse(getPageContext());
        break;
      case 'FIND_ELEMENT':
        sendResponse(findElement(message.selector));
        break;
      case 'GET_FORM_FIELDS':
        sendResponse(getFormFields());
        break;
    }
    return true;
  });

  function getPageContext() {
    return {
      title: document.title,
      url: window.location.href,
      text: document.body.innerText.slice(0, 10000),
      forms: Array.from(document.forms).map(f => ({
        id: f.id,
        fields: Array.from(f.elements).map(e => ({
          name: e.name, type: e.type,
          placeholder: e.placeholder, id: e.id, required: e.required
        }))
      })),
      stats: {
        links: document.querySelectorAll('a').length,
        buttons: document.querySelectorAll('button, [role=button]').length,
        inputs: document.querySelectorAll('input, textarea, select').length
      }
    };
  }

  function findElement(selector) {
    const el = document.querySelector(selector);
    if (!el) return { found: false };
    const rect = el.getBoundingClientRect();
    return {
      found: true, tag: el.tagName,
      text: el.textContent?.slice(0, 200),
      rect: {
        x: rect.x, y: rect.y,
        width: rect.width, height: rect.height
      },
      visible: rect.width > 0 && rect.height > 0
    };
  }

  function getFormFields() {
    return Array.from(document.querySelectorAll('input, textarea, select')).map(el => {
      const label = document.querySelector(`label[for="${el.id}"]`);
      const parentLabel = el.closest('label');
      return {
        id: el.id, name: el.name, type: el.type,
        placeholder: el.placeholder,
        label: label?.textContent || parentLabel?.textContent || '',
        value: el.value, required: el.required
      };
    });
  }

  // Report page load to background
  chrome.runtime.sendMessage({
    type: 'PAGE_LOADED',
    url: window.location.href,
    title: document.title
  }).catch(() => {});  // Suppress port closure error
})();
