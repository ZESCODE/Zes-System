// Email Skill — SMTP send + IMAP read via CLI (nodemailer/curl)
import { execSync } from "child_process";

export class EmailSkill {
  name = "email";
  description = "Send emails via SMTP and read inbox via IMAP";

  tools() {
    return [
      {
        name: "send",
        description: "Send an email via SMTP",
        inputSchema: {
          type: "object",
          properties: {
            to: { type: "string", description: "Recipient email address(es), comma separated" },
            subject: { type: "string", description: "Email subject" },
            body: { type: "string", description: "Plain text email body" },
            smtpHost: { type: "string", description: "SMTP server hostname", default: "smtp.gmail.com" },
            smtpPort: { type: "number", description: "SMTP port", default: 587 },
            username: { type: "string", description: "SMTP username" },
            password: { type: "string", description: "SMTP password or app password" }
          },
          required: ["to", "subject", "body", "username", "password"]
        }
      },
      {
        name: "read_inbox",
        description: "Read recent unseen emails from IMAP inbox",
        inputSchema: {
          type: "object",
          properties: {
            imapHost: { type: "string", description: "IMAP server hostname", default: "imap.gmail.com" },
            imapPort: { type: "number", description: "IMAP port", default: 993 },
            username: { type: "string", description: "IMAP username" },
            password: { type: "string", description: "IMAP password or app password" },
            limit: { type: "number", description: "Max emails to fetch", default: 10 }
          },
          required: ["username", "password"]
        }
      }
    ];
  }

  async send(args) {
    // Use curl for SMTP (avoids nodemailer dependency)
    // For proper SMTP, we recommend installing nodemailer: npm install nodemailer
    try {
      const { to, subject, body, smtpHost, smtpPort, username, password } = args;
      // Try using swaks CLI if available, else return instructions
      try {
        const cmd = `swaks --to "${to}" --from "${username}" --server "${smtpHost}:${smtpPort}" --auth LOGIN --auth-user "${username}" --auth-password "${password}" --header "Subject: ${subject}" --body "${body.replace(/"/g, '\\"')}"`;
        execSync(cmd, { timeout: 15000 });
        return { success: true, data: { sent: true } };
      } catch {
        return { success: false, error: "SMTP client not available. Install swaks (apt install swaks) or nodemailer." };
      }
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async read_inbox(args) {
    try {
      const { imapHost, imapPort, username, password, limit } = args;
      // Use node.js built-in via IMAP CLI tool
      try {
        const cmd = `curl -s --max-time 15 --user "${username}:${password}" "imaps://${imapHost}:${imapPort}/INBOX?UNSEEN" 2>/dev/null || echo "IMAP direct curl not supported"`;
        const output = execSync(cmd, { timeout: 20000, encoding: "utf-8" });
        return { success: true, data: { raw: output.slice(0, 5000), note: "Install nodemailer for structured inbox reading" } };
      } catch {
        return { success: false, error: "IMAP client not available. npm install nodemailer for full email support." };
      }
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}
