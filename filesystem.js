// Filesystem Skill — Read, write, list, manage files
import fs from "fs";
import fsp from "fs/promises";
import path from "path";

const ALLOWED_ROOTS = [
  process.env.HOME || "/data/data/com.termux/files/home",
  "/data/data/com.termux/files/home/Zes-",
  "/data/data/com.termux/files/home/.zes",
  "/data/data/com.termux/files/home/.codex"
];

function isPathSafe(targetPath) {
  const resolved = path.resolve(targetPath);
  return ALLOWED_ROOTS.some(root => resolved.startsWith(root));
}

export class FileSystemSkill {
  name = "fs";
  description = "Read, write, and manage files in the filesystem";

  tools() {
    return [
      {
        name: "read",
        description: "Read file contents as text (UTF-8)",
        inputSchema: {
          type: "object",
          properties: {
            path: { type: "string", description: "Absolute path to the file" }
          },
          required: ["path"]
        }
      },
      {
        name: "write",
        description: "Write text content to a file (creates directories if needed)",
        inputSchema: {
          type: "object",
          properties: {
            path: { type: "string", description: "Absolute path to write to" },
            content: { type: "string", description: "Text content to write" }
          },
          required: ["path", "content"]
        }
      },
      {
        name: "list",
        description: "List directory contents with file names, sizes, and modification times",
        inputSchema: {
          type: "object",
          properties: {
            dir: { type: "string", description: "Absolute directory path" },
            pattern: { type: "string", description: "Glob pattern to filter (e.g. *.tsx)" }
          },
          required: ["dir"]
        }
      },
      {
        name: "delete",
        description: "Delete a file or empty directory",
        inputSchema: {
          type: "object",
          properties: {
            path: { type: "string", description: "Path to delete" }
          },
          required: ["path"]
        }
      },
      {
        name: "exists",
        description: "Check if a file or directory exists",
        inputSchema: {
          type: "object",
          properties: {
            path: { type: "string", description: "Path to check" }
          },
          required: ["path"]
        }
      },
      {
        name: "search",
        description: "Search for files matching a glob pattern",
        inputSchema: {
          type: "object",
          properties: {
            pattern: { type: "string", description: "Glob pattern (e.g. **/*.tsx)" },
            root: { type: "string", description: "Root directory to search from" }
          },
          required: ["pattern"]
        }
      },
      {
        name: "mkdir",
        description: "Create a directory (including parent directories)",
        inputSchema: {
          type: "object",
          properties: {
            path: { type: "string", description: "Absolute path for the new directory" }
          },
          required: ["path"]
        }
      }
    ];
  }

  async read(args) {
    if (!isPathSafe(args.path)) throw new Error("Access denied: path not in allowed roots");
    const content = await fsp.readFile(args.path, "utf-8");
    return { success: true, data: { content, size: content.length } };
  }

  async write(args) {
    if (!isPathSafe(args.path)) throw new Error("Access denied: path not in allowed roots");
    await fsp.mkdir(path.dirname(args.path), { recursive: true });
    await fsp.writeFile(args.path, args.content, "utf-8");
    return { success: true, data: { written: args.content.length, path: args.path } };
  }

  async list(args) {
    if (!isPathSafe(args.dir)) throw new Error("Access denied: path not in allowed roots");
    const entries = await fsp.readdir(args.dir, { withFileTypes: true });
    const items = [];
    for (const entry of entries) {
      if (args.pattern) {
        const match = entry.name.endsWith(args.pattern.replace("*", ""));
        if (!match) continue;
      }
      try {
        const stat = await fsp.stat(path.join(args.dir, entry.name));
        items.push({
          name: entry.name,
          isDir: entry.isDirectory(),
          size: stat.size,
          modified: stat.mtime.toISOString()
        });
      } catch {}
    }
    return { success: true, data: items };
  }

  async delete(args) {
    if (!isPathSafe(args.path)) throw new Error("Access denied: path not in allowed roots");
    await fsp.rm(args.path, { recursive: true, force: true });
    return { success: true, data: { deleted: args.path } };
  }

  async exists(args) {
    try {
      await fsp.access(args.path);
      const stat = await fsp.stat(args.path);
      return { success: true, data: { exists: true, isDir: stat.isDirectory(), isFile: stat.isFile() } };
    } catch {
      return { success: true, data: { exists: false } };
    }
  }

  async search(args) {
    if (args.root && !isPathSafe(args.root)) throw new Error("Access denied: path not in allowed roots");
    // Use a simple recursive search instead of glob
    const root = args.root || process.env.HOME;
    const pattern = args.pattern;
    const results = [];
    
    async function walk(dir) {
      if (results.length >= 200) return;
      try {
        const entries = await fsp.readdir(dir, { withFileTypes: true });
        for (const entry of entries) {
          if (results.length >= 200) return;
          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory() && !entry.name.startsWith(".") && !entry.name.startsWith("node_modules")) {
            await walk(fullPath);
          } else if (entry.isFile()) {
            // Simple glob matching
            const regex = new RegExp("^" + pattern.replace(/\*/g, ".*").replace(/\?/g, ".") + "$");
            if (regex.test(entry.name)) {
              results.push(fullPath);
            }
          }
        }
      } catch {}
    }
    
    await walk(root);
    return { success: true, data: results };
  }

  async mkdir(args) {
    if (!isPathSafe(args.path)) throw new Error("Access denied: path not in allowed roots");
    await fsp.mkdir(args.path, { recursive: true });
    return { success: true, data: { created: args.path } };
  }
}
