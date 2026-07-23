// System Skill — Execute shell commands with safety guardrails
import { execSync } from "child_process";

const ALLOWED_COMMANDS = [
  "npm", "node", "pnpm", "git", "python3", "python", "cat", "ls",
  "echo", "tail", "head", "grep", "rg", "find", "wc", "date",
  "ps", "top", "free", "df", "du", "uname", "whoami", "id",
  "curl", "wget", "ping", "ss", "ip", "nslookup",
  "sv", "mkdir", "cp", "mv", "rm", "chmod", "chown",
  "tar", "gzip", "gunzip", "zip", "unzip", "less",
  "diff", "sort", "uniq", "cut", "tr", "tee",
  "which", "realpath", "readlink", "stat", "file"
];

function isCommandSafe(cmd) {
  const firstWord = cmd.trim().split(/\s+/)[0];
  return ALLOWED_COMMANDS.includes(firstWord);
}

export class SystemSkill {
  name = "sys";
  description = "Execute local shell commands with safety guardrails";

  tools() {
    return [
      {
        name: "exec",
        description: "Execute a shell command and return stdout + stderr (restricted to allowed commands)",
        inputSchema: {
          type: "object",
          properties: {
            command: { type: "string", description: "Shell command to execute" },
            timeout: { type: "number", description: "Timeout in milliseconds", default: 15000 }
          },
          required: ["command"]
        }
      },
      {
        name: "env",
        description: "Get value of an environment variable",
        inputSchema: {
          type: "object",
          properties: {
            name: { type: "string", description: "Environment variable name" }
          },
          required: ["name"]
        }
      },
      {
        name: "which",
        description: "Find the absolute path of an executable",
        inputSchema: {
          type: "object",
          properties: {
            name: { type: "string", description: "Command name to locate" }
          },
          required: ["name"]
        }
      }
    ];
  }

  async exec(args) {
    if (!isCommandSafe(args.command)) {
      return {
        success: false,
        error: "Command \"" + args.command.trim().split(/\s+/)[0] + "\" is not in the allowed commands list"
      };
    }
    try {
      const stdout = execSync(args.command, {
        encoding: "utf-8",
        timeout: args.timeout || 15000,
        maxBuffer: 10 * 1024 * 1024
      });
      return { success: true, data: { stdout, stderr: "" } };
    } catch (error) {
      return {
        success: true,
        data: { stdout: error.stdout || "", stderr: error.stderr || "", exitCode: error.status }
      };
    }
  }

  async env(args) {
    return { success: true, data: { name: args.name, value: process.env[args.name] || null } };
  }

  async which(args) {
    try {
      const stdout = execSync("which " + args.name, { encoding: "utf-8" }).trim();
      return { success: true, data: { path: stdout || null } };
    } catch {
      return { success: true, data: { path: null } };
    }
  }
}
