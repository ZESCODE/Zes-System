#!/usr/bin/env node
/**
 * ZES Cross-Harness Agent Deployment
 * Export ZES agents to Cursor, Gemini CLI, Zed, and CodeBuddy formats
 * 
 * Usage: node deploy-agent.js <agent-name> [--format cursor|gemini|zed|codebuddy|all]
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join, dirname } from "path";

const HOME = process.env.HOME;
const AGENTS_DIR = join(HOME, "Zes-System", ".agents", "agents");
const SKILLS_DIR = join(HOME, "Zes-System", ".agents", "skills");
const EXPORT_DIR = join(HOME, "Zes-System", ".pipeline", "exports");

// Harness output formats
const FORMATS = {
  cursor: {
    rules_dir: join(HOME, ".cursor", "rules"),
    skills_dir: join(HOME, ".cursor", "skills"),
    format: "cursor",
    extension: ".mdc"
  },
  gemini: {
    rules_dir: join(HOME, ".gemini"),
    skills_dir: join(HOME, ".gemini"),
    format: "gemini",
    extension: ".md"
  },
  codebuddy: {
    rules_dir: join(HOME, ".codebuddy"),
    skills_dir: join(HOME, ".codebuddy", "skills"),
    format: "codebuddy",
    extension: ".md"
  }
};

function listAgents() {
  if (!existsSync(AGENTS_DIR)) return [];
  return readFileSync(AGENTS_DIR, "utf8").split("\n")
    .filter(l => l.trim() && !l.startsWith("."))
    .map(l => l.replace(/\.md$/, "").trim());
}

function deployAgent(agentName, format, targetDir) {
  const srcFile = join(AGENTS_DIR, agentName + ".md");
  if (!existsSync(srcFile)) {
    console.error(`Agent "${agentName}" not found in ${AGENTS_DIR}`);
    return false;
  }

  const content = readFileSync(srcFile, "utf8");
  const destDir = FORMATS[format]?.rules_dir || targetDir;
  mkdirSync(destDir, { recursive: true });

  // Convert format
  let output;
  switch (format) {
    case "cursor":
      output = `---
description: ZES Agent: ${agentName}
globs: *.py,*.js,*.ts,*.sh,*.json,*.md
---
# ${agentName}

${content}

> Auto-deployed from ZES System at ${new Date().toISOString()}
`;
      break;
    case "gemini":
      output = `# ${agentName}\n\n${content}\n\n---\n*Exported from ZES at ${new Date().toISOString()}*`;
      break;
    case "codebuddy":
      output = `# ${agentName}\n\n${content}\n\n---\n*ZES Cross-Harness Deployment at ${new Date().toISOString()}*`;
      break;
    default:
      output = content;
  }

  const ext = FORMATS[format]?.extension || ".md";
  const destFile = join(destDir, `${agentName}${ext}`);
  writeFileSync(destFile, output);
  console.log(`  ✓ Deployed "${agentName}" → ${destFile}`);
  return true;
}

function main() {
  const args = process.argv.slice(2);
  const agentName = args.find(a => !a.startsWith("--"));
  const formatFlag = args.find(a => a.startsWith("--format="));
  const format = formatFlag ? formatFlag.split("=")[1] : "all";
  const targetDir = args.includes("--dir") ? args[args.indexOf("--dir") + 1] : null;

  if (!agentName) {
    const agents = listAgents();
    console.log("📋 Available ZES Agents:");
    agents.forEach(a => console.log(`  • ${a}`));
    console.log("\nUsage: node deploy-agent.js <agent-name> [--format cursor|gemini|codebuddy|all] [--dir /path/to/export]");
    return;
  }

  console.log(`🚀 Deploying agent "${agentName}"...`);
  
  const formats = format === "all" ? Object.keys(FORMATS) : [format];
  let deployed = 0;

  for (const fmt of formats) {
    if (FORMATS[fmt]) {
      console.log(`  📦 Format: ${fmt}`);
      if (deployAgent(agentName, fmt, targetDir)) deployed++;
    }
  }

  console.log(`\n✅ Deployed to ${deployed} harness(es)`);
}

main();
