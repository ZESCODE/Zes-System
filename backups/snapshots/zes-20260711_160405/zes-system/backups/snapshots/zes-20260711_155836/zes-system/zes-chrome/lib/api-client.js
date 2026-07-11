// API Client — talks to Dashboard (:8083) and 9Router

export class ApiClient {
  static BASE = 'http://localhost:8083';

  static async fetch(path, options = {}) {
    const res = await fetch(`${this.BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  }

  static chat(message, history = []) {
    return this.fetch('/api/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, history })
    });
  }

  static getModels() {
    return this.fetch('/api/models');
  }

  static getServices() {
    return this.fetch('/api/services');
  }

  static getHistory() {
    return this.fetch('/api/agent/history');
  }

  static authService(service) {
    return this.fetch('/api/services/auth', {
      method: 'POST',
      body: JSON.stringify({ service })
    });
  }
}
