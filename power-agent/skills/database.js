// Database Skill — SQLite + PostgreSQL queries
import { execSync } from "child_process";

export class DatabaseSkill {
  name = "db";
  description = "Execute SQL queries against SQLite or PostgreSQL databases";

  tools() {
    return [
      {
        name: "execute",
        description: "Execute a SQL query (SELECT returns rows, others return rowcount)",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string", description: "Database URL: sqlite:///path/to/db or postgresql://user:pass@host/db" },
            query: { type: "string", description: "SQL query to execute" }
          },
          required: ["url", "query"]
        }
      },
      {
        name: "list_tables",
        description: "List all tables in the database",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string", description: "Database URL" }
          },
          required: ["url"]
        }
      }
    ];
  }

  async execute(args) {
    try {
      const { url, query } = args;
      if (url.startsWith("sqlite://")) {
        const dbPath = url.replace("sqlite://", "");
        const isSelect = query.trim().toUpperCase().startsWith("SELECT");
        if (isSelect) {
          const cmd = `sqlite3 -json "${dbPath}" "${query.replace(/"/g, '\\"')}"`;
          const output = execSync(cmd, { timeout: 10000, encoding: "utf-8" });
          return { success: true, data: { rows: JSON.parse(output || "[]") } };
        } else {
          const cmd = `sqlite3 "${dbPath}" "${query.replace(/"/g, '\\"')}"`;
          execSync(cmd, { timeout: 10000 });
          return { success: true, data: { executed: true } };
        }
      } else if (url.startsWith("postgresql://")) {
        const isSelect = query.trim().toUpperCase().startsWith("SELECT");
        const cmd = `psql "${url}" -c "${query.replace(/"/g, '\\"')}" ${isSelect ? "--json" : ""} -t 2>&1`;
        const output = execSync(cmd, { timeout: 15000, encoding: "utf-8" });
        return { success: true, data: { result: output } };
      }
      return { success: false, error: "Unsupported database URL. Use sqlite:// or postgresql://" };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async list_tables(args) {
    const { url } = args;
    if (url.startsWith("sqlite://")) {
      return this.execute({ url, query: "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name" });
    }
    return this.execute({ url, query: "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name" });
  }
}
