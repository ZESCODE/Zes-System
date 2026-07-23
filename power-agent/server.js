// ZES MCP Power Agent — Unified multi-skill server (v2.0)
// Connects to MCP clients via stdio transport
// Skills: cdp, fs, api, sys, email, db, pdf, spreadsheet, ocr, slack, ssh

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema
} from "@modelcontextprotocol/sdk/types.js";
import { SkillRegistry } from "./registry.js";

// ── Import all skills ──────────────────────────────────────
import { CDPSkill } from "./skills/cdp.js";
import { FileSystemSkill } from "./skills/filesystem.js";
import { RESTAPISkill } from "./skills/rest-api.js";
import { SystemSkill } from "./skills/system.js";
import { EmailSkill } from "./skills/email.js";
import { DatabaseSkill } from "./skills/database.js";
import { PDFGenerationSkill } from "./skills/pdf-gen.js";
import { SpreadsheetSkill } from "./skills/spreadsheet.js";
import { OCRSkill } from "./skills/ocr.js";
import { SlackSkill } from "./skills/slack.js";
import { SSHSkill } from "./skills/ssh.js";

// ── Initialize Registry ────────────────────────────────────

const registry = new SkillRegistry();
registry.register("cdp", new CDPSkill());
registry.register("fs", new FileSystemSkill());
registry.register("api", new RESTAPISkill());
registry.register("sys", new SystemSkill());
registry.register("email", new EmailSkill());
registry.register("db", new DatabaseSkill());
registry.register("pdf", new PDFGenerationSkill());
registry.register("spreadsheet", new SpreadsheetSkill());
registry.register("ocr", new OCRSkill());
registry.register("slack", new SlackSkill());
registry.register("ssh", new SSHSkill());

const SKILLS = registry.list();

// ── Create MCP Server ──────────────────────────────────────

const server = new Server(
  {
    name: "zes-power-agent",
    version: "2.0.0",
    description: "Unified MCP server: 12 skills — CDP browser, FS, REST API, System, Email, DB, PDF, Spreadsheet, OCR, Slack, SSH"
  },
  {
    capabilities: {
      tools: {},
      resources: {}
    }
  }
);

// ── Resources: List available skills ───────────────────────

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "power-agent://skills",
        name: "Available Skills",
        description: "List of registered skills and their methods",
        mimeType: "application/json"
      }
    ]
  };
});

// ── Tools: List all skill tools ────────────────────────────

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools = registry.toolDefinitions();
  return { tools };
});

// ── Tools: Execute skill methods ───────────────────────────

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const parts = name.split("_");
  const skillName = parts[0];
  const methodName = parts.slice(1).join("_");

  if (!SKILLS.includes(skillName)) {
    return {
      isError: true,
      content: [{ type: "text", text: "Unknown skill: " + skillName + ". Available skills: " + SKILLS.join(", ") }]
    };
  }

  try {
    const result = await registry.execute(skillName, methodName, args || {});

    if (result.contentType === "image") {
      return {
        content: [{
          type: "image",
          data: result.data,
          mimeType: "image/png"
        }]
      };
    }

    return {
      content: [{ type: "text", text: JSON.stringify(result.data ?? result, null, 2) }]
    };
  } catch (error) {
    return {
      isError: true,
      content: [{ type: "text", text: error.message }]
    };
  }
});

// ── Start Server ───────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ZES Power Agent MCP server v2.0 running on stdio");
  console.error("Skills: " + SKILLS.join(", "));
  console.error("Tools: " + registry.toolDefinitions().length + " registered");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
