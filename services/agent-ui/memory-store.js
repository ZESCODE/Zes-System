/**
 * ZES Agent Memory Store — Persistent JSON-based memory
 * Stores conversation summaries, learned facts, and user preferences.
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const MEMORY_FILE = join(__dirname, "zes-memory.json");
const MAX_HISTORY = 100;

class MemoryStore {
  constructor() {
    this.data = this._load();
  }

  _load() {
    try {
      if (existsSync(MEMORY_FILE)) {
        return JSON.parse(readFileSync(MEMORY_FILE, "utf8"));
      }
    } catch (e) {
      console.error("Memory load error:", e.message);
    }
    return {
      conversations: [], facts: [], preferences: {},
      lastSession: null, relations: [], version: 2
    };
  }

  _save() {
    try {
      writeFileSync(MEMORY_FILE, JSON.stringify(this.data, null, 2));
    } catch (e) {
      console.error("Memory save error:", e.message);
    }
  }

  // ── Conversation Management ─────────────────────────────────────

  // Store a conversation summary with enhanced metadata
  addConversation(summary, messages = []) {
    const relatedFiles = this._extractRelatedFiles(summary);
    const relatedServices = this._extractTopics(summary);
    this.data.conversations.unshift({
      id: Date.now().toString(36),
      timestamp: new Date().toISOString(),
      summary: summary.slice(0, 500),
      messageCount: messages.length,
      topics: relatedServices,
      relatedFiles,
      priority: this._scorePriority(summary, messages.length),
      lastAccessed: new Date().toISOString(),
    });
    // Auto-consolidate if over limit
    if (this.data.conversations.length > MAX_HISTORY) {
      this._consolidateConversations();
    }
    this._save();
  }

  // Auto-summarize old conversations by keeping only high-priority ones
  _consolidateConversations() {
    // Sort by priority (score), keep top MAX_HISTORY
    this.data.conversations.sort((a, b) => (b.priority || 0) - (a.priority || 0));
    this.data.conversations = this.data.conversations.slice(0, MAX_HISTORY);
    // Merge very similar conversations
    const merged = [];
    for (const conv of this.data.conversations) {
      const similar = merged.find(m =>
        m.topics?.some(t => conv.topics?.includes(t)) &&
        Math.abs(new Date(m.timestamp) - new Date(conv.timestamp)) < 3600000
      );
      if (similar) {
        similar.messageCount += conv.messageCount;
        similar.summary = similar.summary.slice(0, 200) + " | " + conv.summary.slice(0, 200);
        similar.priority = Math.max(similar.priority || 0, conv.priority || 0);
      } else {
        merged.push(conv);
      }
    }
    this.data.conversations = merged.slice(0, MAX_HISTORY);
  }

  // ── Fact Management ────────────────────────────────────────────

  // Store a learned fact with priority scoring
  addFact(fact, category = "general", source = "") {
    const existing = this.data.facts.find(f =>
      f.text.toLowerCase().includes(fact.toLowerCase().slice(0, 30)) ||
      fact.toLowerCase().includes(f.text.toLowerCase().slice(0, 30))
    );
    if (existing) {
      existing.count = (existing.count || 1) + 1;
      existing.lastSeen = new Date().toISOString();
      existing.priority = Math.min(10, (existing.priority || 1) + 1);
      if (source && !existing.sources?.includes(source)) {
        existing.sources = [...(existing.sources || []), source].slice(-5);
      }
    } else {
      this.data.facts.unshift({
        id: Date.now().toString(36),
        text: fact.slice(0, 500),
        category,
        source,
        created: new Date().toISOString(),
        lastSeen: new Date().toISOString(),
        count: 1,
        priority: 1,
      });
    }
    // Consolidate when too many
    if (this.data.facts.length > 200) {
      this._consolidateFacts();
    }
    this._save();
  }

  // Consolidate facts: remove old low-priority, merge duplicates
  _consolidateFacts() {
    // Remove very old, low-priority, single-occurrence facts
    const cutoff = Date.now() - 30 * 24 * 3600 * 1000; // 30 days
    this.data.facts = this.data.facts.filter(f =>
      (f.priority || 1) > 1 ||
      (f.count || 1) > 1 ||
      new Date(f.lastSeen || f.created).getTime() > cutoff
    );
    // Sort by priority, keep top 150
    this.data.facts.sort((a, b) => (b.priority || 0) - (a.priority || 0));
    this.data.facts = this.data.facts.slice(0, 150);
  }

  // ── Query & Retrieval ─────────────────────────────────────────

  // Get relevant facts with priority weighting
  getRelevantFacts(query) {
    const q = query.toLowerCase();
    const words = q.split(/\s+/).filter(w => w.length > 3);
    return this.data.facts
      .map(f => {
        let score = 0;
        if (f.text.toLowerCase().includes(q)) score += 5;
        words.forEach(w => { if (f.text.toLowerCase().includes(w)) score += 2; });
        if (f.category && q.includes(f.category.toLowerCase())) score += 3;
        score += (f.priority || 1) * 0.5;
        score += Math.log((f.count || 1) + 1);
        return { ...f, _score: score };
      })
      .filter(f => f._score > 1)
      .sort((a, b) => b._score - a._score)
      .slice(0, 10);
  }

  // Get recent conversations
  getRecentConversations(limit = 5) {
    return this.data.conversations.slice(0, limit);
  }

  // ── Relationship Tracking ──────────────────────────────────────

  // Link a file or service to a conversation
  addRelation(type, sourceId, targetId, label = "related") {
    if (!this.data.relations) this.data.relations = [];
    this.data.relations.push({
      type, sourceId, targetId, label,
      timestamp: new Date().toISOString(),
    });
    if (this.data.relations.length > 500) {
      this.data.relations = this.data.relations.slice(-300);
    }
    this._save();
  }

  // Get relations for a specific entity
  getRelations(entityId) {
    return (this.data.relations || []).filter(r =>
      r.sourceId === entityId || r.targetId === entityId
    ).slice(0, 20);
  }

  // ── Preferences ─────────────────────────────────────────────────

  setPreference(key, value) {
    this.data.preferences[key] = value;
    this._save();
  }

  getPreference(key, def = null) {
    return this.data.preferences[key] ?? def;
  }

  // ── Context Building ───────────────────────────────────────────

  // Get context for system prompt with priority-aware retrieval
  getContext(query = "") {
    const facts = this.getRelevantFacts(query);
    const recent = this.getRecentConversations(3);
    const prefs = this.data.preferences;
    return { facts, recentConversations: recent, preferences: prefs };
  }

  // Build a structured memory summary for system prompt injection
  getMemorySummary() {
    const facts = this.data.facts
      .sort((a, b) => (b.priority || 0) - (a.priority || 0))
      .slice(0, 15);
    const recent = this.data.conversations
      .sort((a, b) => new Date(b.lastAccessed || b.timestamp) - new Date(a.lastAccessed || a.timestamp))
      .slice(0, 3);
    const prefs = this.data.preferences;

    let summary = "";
    if (facts.length) {
      summary += "## Things I've learned (by importance):\n";
      facts.forEach(f => {
        const icon = f.priority >= 5 ? "🔴" : f.priority >= 3 ? "🟡" : "🟢";
        summary += `- ${icon} ${f.text}\n`;
      });
    }
    if (recent.length) {
      summary += "\n## Recent activity:\n";
      recent.forEach(c => {
        const files = c.relatedFiles?.length ? ` [${c.relatedFiles.join(", ")}]` : "";
        summary += `- ${c.summary.slice(0, 200)}${files}\n`;
      });
    }
    if (Object.keys(prefs).length) {
      summary += "\n## User preferences:\n";
      Object.entries(prefs).forEach(([k, v]) => { summary += `- ${k}: ${v}\n`; });
    }
    return summary || "No prior knowledge yet. I am learning about the ZES system.";
  }

  // ── Utilities ──────────────────────────────────────────────────

  // Forget a specific memory by ID
  forget(type, id) {
    if (this.data[type]) {
      this.data[type] = this.data[type].filter(i => i.id !== id);
      this._save();
      return true;
    }
    return false;
  }

  // Clear all memories
  clear() {
    this.data = {
      conversations: [], facts: [], preferences: {},
      lastSession: null, relations: [], version: 2
    };
    this._save();
  }

  // Get memory statistics
  getStats() {
    return {
      facts: this.data.facts.length,
      conversations: this.data.conversations.length,
      preferences: Object.keys(this.data.preferences).length,
      relations: (this.data.relations || []).length,
      topFacts: this.data.facts
        .sort((a, b) => (b.priority || 0) - (a.priority || 0))
        .slice(0, 3)
        .map(f => ({ text: f.text.slice(0, 80), priority: f.priority, count: f.count })),
    };
  }

  // Score conversation priority (for consolidation decisions)
  _scorePriority(summary, msgCount) {
    let score = 0;
    const text = summary.toLowerCase();
    // System-critical topics get higher priority
    if (text.includes("restart") || text.includes("backup") || text.includes("deploy")) score += 5;
    if (text.includes("security") || text.includes("error") || text.includes("fail")) score += 4;
    if (text.includes("config") || text.includes("provider") || text.includes("model")) score += 3;
    if (text.includes("9router") || text.includes("dashboard") || text.includes("hermes")) score += 2;
    // Longer conversations are more important
    score += Math.min(msgCount, 20) * 0.5;
    return Math.round(score);
  }

  // Extract related file paths from text
  _extractRelatedFiles(text) {
    const filePattern = /[\w\-./]+?\.(py|js|sh|json|md|html|css|yaml|yml|conf)/g;
    return [...new Set((text.match(filePattern) || []).slice(0, 5))];
  }

  // Extract topics from text
  _extractTopics(text) {
    const topics = [
      "system", "service", "backup", "mcp", "provider", "model",
      "dashboard", "9router", "hermes", "claude", "tor", "security",
      "deploy", "config", "skill", "agent", "test", "eval", "restart",
      "monitor", "chrome", "vscode", "ttyd", "terminal", "network",
    ];
    return topics.filter(t => text.toLowerCase().includes(t)) || ["general"];
  }
}export const memory = new MemoryStore();
