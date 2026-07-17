/**
 * ZES Kanban Store — Task management linked to agent conversations
 * Extends memory-store.js with kanban board functionality
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const KANBAN_FILE = join(__dirname, "zes-kanban.json");
const COLUMNS = ["backlog", "in-progress", "review", "done"];

class KanbanStore {
  constructor() {
    this.data = this._load();
  }

  _load() {
    try {
      if (existsSync(KANBAN_FILE)) {
        return JSON.parse(readFileSync(KANBAN_FILE, "utf8"));
      }
    } catch (e) {
      console.error("Kanban load error:", e.message);
    }
    return { 
      columns: { 
        "backlog": [], 
        "in-progress": [], 
        "review": [], 
        "done": [] 
      },
      nextId: 1
    };
  }

  _save() {
    try {
      const dir = dirname(KANBAN_FILE);
      if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
      writeFileSync(KANBAN_FILE, JSON.stringify(this.data, null, 2));
    } catch (e) {
      console.error("Kanban save error:", e.message);
    }
  }

  // ── Task CRUD ──────────────────────────────────────────────────

  // Add a task with file/session linking
  addTask(title, description = "", source = "agent", conversationId = "", files = []) {
    const task = {
      id: `task-${this.data.nextId++}`,
      title: title.slice(0, 200),
      description: description.slice(0, 2000),
      source,
      conversationId,
      files: Array.isArray(files) ? files : [files].filter(Boolean),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      priority: "medium",
      tags: [],
      status: "open",
    };
    this.data.columns["backlog"].unshift(task);
    this._save();
    return task;
  }

  // Move task between columns
  moveTask(taskId, toColumn) {
    if (!COLUMNS.includes(toColumn)) return null;
    let task = null;
    for (const col of COLUMNS) {
      const idx = this.data.columns[col].findIndex(t => t.id === taskId);
      if (idx !== -1) {
        task = this.data.columns[col].splice(idx, 1)[0];
        break;
      }
    }
    if (task) {
      task.updatedAt = new Date().toISOString();
      task.column = toColumn;
      this.data.columns[toColumn].unshift(task);
      this._save();
    }
    return task;
  }

  // Update task
  updateTask(taskId, updates) {
    for (const col of COLUMNS) {
      const task = this.data.columns[col].find(t => t.id === taskId);
      if (task) {
        Object.assign(task, updates, { updatedAt: new Date().toISOString() });
        this._save();
        return task;
      }
    }
    return null;
  }

  // Delete a task
  deleteTask(taskId) {
    for (const col of COLUMNS) {
      const idx = this.data.columns[col].findIndex(t => t.id === taskId);
      if (idx !== -1) {
        const task = this.data.columns[col].splice(idx, 1)[0];
        this._save();
        return task;
      }
    }
    return null;
  }

  // ── Query ──────────────────────────────────────────────────────

  // Get all tasks
  getAll() {
    return this.data.columns;
  }

  // Get all tasks as a flat list
  getAllFlat() {
    const all = [];
    for (const col of COLUMNS) {
      for (const task of this.data.columns[col]) {
        all.push({ ...task, column: col });
      }
    }
    return all;
  }

  // Get a task by ID
  getTask(taskId) {
    for (const col of COLUMNS) {
      const task = this.data.columns[col].find(t => t.id === taskId);
      if (task) {
        return { ...task, column: col };
      }
    }
    return null;
  }

  // Get tasks by file path
  getTasksByFile(filePath) {
    return this.getAllFlat().filter(t =>
      t.files?.some(f => filePath.includes(f) || f.includes(filePath))
    );
  }

  // Get tasks by conversation ID
  getTasksByConversation(conversationId) {
    return this.getAllFlat().filter(t => t.conversationId === conversationId);
  }

  // ── File & Session Linking (Nimbalyst pattern) ─────────────────

  // Link files to a task
  linkFiles(taskId, files) {
    const task = this.getTask(taskId);
    if (!task) return null;
    const currentFiles = new Set(task.files || []);
    for (const f of (Array.isArray(files) ? files : [files])) {
      if (f) currentFiles.add(f);
    }
    return this.updateTask(taskId, { files: [...currentFiles] });
  }

  // Unlink a file from a task
  unlinkFile(taskId, filePath) {
    const task = this.getTask(taskId);
    if (!task) return null;
    return this.updateTask(taskId, {
      files: (task.files || []).filter(f => f !== filePath)
    });
  }

  // Link conversation to task
  linkConversation(taskId, conversationId) {
    return this.updateTask(taskId, { conversationId });
  }

  // Get all files referenced across tasks
  getAllFiles() {
    const files = new Set();
    for (const task of this.getAllFlat()) {
      for (const f of (task.files || [])) {
        files.add(f);
      }
    }
    return [...files];
  }

  // ── Auto-tasks ─────────────────────────────────────────────────

  // Auto-create task from agent conversation summary
  autoCreateTask(summary, convId, files = []) {
    if (!summary || summary.length < 20) return null;
    const title = summary.split("\n")[0].slice(0, 80);
    // Extract mentioned files from summary
    const filePattern = /[\w\-./]+?\.(py|js|sh|json|md|html|css|yaml|yml|conf)/g;
    const mentionedFiles = [...new Set((summary.match(filePattern) || []))];
    const allFiles = [...new Set([...files, ...mentionedFiles])];
    return this.addTask(title, summary.slice(0, 300), "agent", convId, allFiles);
  }

  // ── Kanban board helpers ───────────────────────────────────────

  // Summary statistics
  getStats() {
    const all = this.getAllFlat();
    return {
      total: all.length,
      byColumn: Object.fromEntries(COLUMNS.map(c => [c, this.data.columns[c].length])),
      byPriority: {
        high: all.filter(t => t.priority === "high").length,
        medium: all.filter(t => t.priority === "medium").length,
        low: all.filter(t => t.priority === "low").length,
      },
      fileCount: this.getAllFiles().length,
    };
  }

  // Search tasks
  search(query) {
    const q = query.toLowerCase();
    return this.getAllFlat().filter(t =>
      t.title.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      t.tags?.some(tag => tag.toLowerCase().includes(q)) ||
      t.files?.some(f => f.toLowerCase().includes(q))
    );
  }
}

export const kanban = new KanbanStore();
