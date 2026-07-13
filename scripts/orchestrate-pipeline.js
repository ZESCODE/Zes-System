#!/usr/bin/env node
/**
 * ZES Agent Orchestration Pipeline
 * Runs a task through Planner → Architect → Code → Review → Test stages
 * Usage: node orchestrate-pipeline.js "task description" [--stage planner]
 */
import { execSync } from "child_process";

const STAGES = ["planner", "architect", "coder", "reviewer", "tester"];
const PIPELINE_DIR = process.env.HOME + "/Zes-System/.pipeline";
const LOG_FILE = PIPELINE_DIR + "/pipeline.log";

function log(msg) {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}`;
  console.log(line);
  try {
    const { mkdirSync, appendFileSync } = await import("fs");
    mkdirSync(PIPELINE_DIR, { recursive: true });
    appendFileSync(LOG_FILE, line + "\n");
  } catch (e) {}
}

function run(cmd) {
  try {
    return execSync(cmd, { encoding: "utf8", timeout: 120000, shell: true }).trim();
  } catch (e) {
    return `Error: ${(e.stderr || e.message || "").trim().slice(0, 500)}`;
  }
}

async function main() {
  const args = process.argv.slice(2);
  const task = args.filter(a => !a.startsWith("--")).join(" ") || "Explore system and suggest improvements";
  const startStage = args.find(a => a.startsWith("--stage"))?.split("=")[1] || "planner";
  const skipIndex = STAGES.indexOf(startStage);

  log(`=== Pipeline Start ===`);
  log(`Task: ${task}`);
  log(`Starting from: ${startStage}`);

  // Status file for dashboard polling
  const statusFile = PIPELINE_DIR + "/status.json";
  const { writeFileSync, mkdirSync } = await import("fs");
  mkdirSync(PIPELINE_DIR, { recursive: true });

  const stages = STAGES.slice(skipIndex);
  const results = {};

  for (const stage of stages) {
    log(`▶ Stage: ${stage}`);
    
    // Update status
    writeFileSync(statusFile, JSON.stringify({
      task, currentStage: stage, status: "running",
      startedAt: new Date().toISOString(),
      results
    }, null, 2));

    const prompt = getStagePrompt(stage, task, results);
    const output = run(`claude -p "${prompt.replace(/"/g, '\\"')}"`);
    results[stage] = { output: output.slice(0, 2000), completedAt: new Date().toISOString() };
    
    log(`✓ Stage ${stage} complete (${output.length} chars)`);
  }

  // Write final summary
  const summary = Object.entries(results).map(([s, r]) => 
    `## ${s.toUpperCase()}\n${r.output.slice(0, 500)}...`
  ).join("\n\n");

  writeFileSync(PIPELINE_DIR + "/summary.md", summary);
  writeFileSync(statusFile, JSON.stringify({
    task, currentStage: "complete", status: "done",
    completedAt: new Date().toISOString(),
    results
  }, null, 2));

  log("=== Pipeline Complete ===");
  console.log("\n📋 Summary written to ~/Zes-System/.pipeline/summary.md");
}

function getStagePrompt(stage, task, previousResults) {
  const prompts = {
    planner: `You are a ZES Planner. Analyze this task and create a step-by-step plan:\n\nTASK: ${task}\n\nOutput: numbered plan with clear steps, requirements, and dependencies.`,
    architect: `You are a ZES Architect. Based on the plan below, design the architecture:\n\nTASK: ${task}\nPLAN: ${(previousResults.planner?.output || "No plan").slice(0, 1000)}\n\nOutput: architecture decisions, component design, data flow, interfaces.`,
    coder: `You are a ZES Developer. Implement the architecture below:\n\nTASK: ${task}\nARCHITECTURE: ${(previousResults.architect?.output || "No architecture").slice(0, 1000)}\n\nOutput: complete code implementation with files, imports, and logic.`,
    reviewer: `You are a ZES Code Reviewer. Review the code implementation:\n\nTASK: ${task}\nCODE: ${(previousResults.coder?.output || "No code").slice(0, 1000)}\n\nOutput: code review with issues found, security concerns, and recommendations.`,
    tester: `You are a ZES QA Engineer. Create and run tests for the implementation:\n\nTASK: ${task}\nCODE: ${(previousResults.coder?.output || "No code").slice(0, 500)}\nREVIEW: ${(previousResults.reviewer?.output || "No review").slice(0, 500)}\n\nOutput: test results, edge cases, and quality assessment.`
  };
  return prompts[stage] || prompts.planner;
}

main().catch(console.error);
