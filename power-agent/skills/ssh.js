// SSH Skill — Remote command execution via SSH
import { execSync } from "child_process";
import fs from "fs";

export class SSHSkill {
  name = "ssh";
  description = "Execute commands on remote servers via SSH";

  tools() {
    return [
      {
        name: "exec",
        description: "Run a command on a remote server via SSH",
        inputSchema: {
          type: "object",
          properties: {
            host: { type: "string", description: "Remote hostname or IP" },
            username: { type: "string", description: "SSH username" },
            command: { type: "string", description: "Command to execute" },
            port: { type: "number", description: "SSH port", default: 22 },
            keyFile: { type: "string", description: "Path to SSH private key (optional)" },
            password: { type: "string", description: "SSH password (optional, use keyFile for security)" }
          },
          required: ["host", "username", "command"]
        }
      },
      {
        name: "upload",
        description: "Upload a local file to a remote server via SCP",
        inputSchema: {
          type: "object",
          properties: {
            host: { type: "string", description: "Remote hostname or IP" },
            username: { type: "string", description: "SSH username" },
            localPath: { type: "string", description: "Absolute path to local file" },
            remotePath: { type: "string", description: "Destination path on remote" },
            port: { type: "number", description: "SSH port", default: 22 },
            keyFile: { type: "string", description: "Path to SSH private key (optional)" }
          },
          required: ["host", "username", "localPath", "remotePath"]
        }
      }
    ];
  }

  _buildSSHArgs(args) {
    let sshArgs = `-p ${args.port || 22} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR`;
    if (args.keyFile) {
      if (!fs.existsSync(args.keyFile)) throw new Error(`Key file not found: ${args.keyFile}`);
      sshArgs += ` -i "${args.keyFile}"`;
    }
    if (args.password) {
      // Use sshpass if password provided
      return `sshpass -p "${args.password}" ssh ${sshArgs}`;
    }
    return `ssh ${sshArgs}`;
  }

  async exec(args) {
    try {
      const { host, username, command, password } = args;
      if (password) {
        // Check sshpass availability
        try { execSync("which sshpass", { timeout: 3000 }); } catch {
          return { success: false, error: "sshpass not installed. apt install sshpass or use key-based auth" };
        }
      }
      const sshBase = this._buildSSHArgs(args);
      const fullCmd = `${sshBase} "${username}@${host}" "${command.replace(/"/g, '\\"')}"`;
      const output = execSync(fullCmd, { timeout: 60000, encoding: "utf-8" });
      return { success: true, data: { stdout: output } };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async upload(args) {
    try {
      const { host, username, localPath, remotePath, password } = args;
      if (!fs.existsSync(localPath)) return { success: false, error: `Local file not found: ${localPath}` };
      if (password) {
        try { execSync("which sshpass", { timeout: 3000 }); } catch {
          return { success: false, error: "sshpass not installed" };
        }
      }
      const sshBase = this._buildSSHArgs(args);
      const scpCmd = sshBase.replace(/^ssh/, "scp").replace(/sshpass/, "sshpass");
      const fullCmd = `${scpCmd} "${localPath}" "${username}@${host}:${remotePath}"`;
      execSync(fullCmd, { timeout: 60000 });
      return { success: true, data: { uploaded: remotePath } };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}
