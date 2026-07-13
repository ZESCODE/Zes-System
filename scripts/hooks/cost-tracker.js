#!/usr/bin/env node
"use strict";
/**
 * cost-tracker — Tracks API call costs for 9Router provider usage.
 * Adapted from ECC's cost-tracker pattern for ZES system.
 */
const fs = require("fs");
const path = require("path");

const COST_FILE = path.join(
  process.env.HOME || "/data/data/com.termux/files/home",
  ".hook-cost-tracker.json"
);

// Estimated costs per million tokens for common ZES providers
const MODEL_COSTS = {
  "llama-3.3-70b": { input: 0.59, output: 0.79 },
  "llama-3.3-70b-versatile": { input: 0.59, output: 0.79 },
  "claude-sonnet-4.6": { input: 3.00, output: 15.00 },
  "gemini-2.5-flash": { input: 0.15, output: 0.60 },
  "deepseek-chat": { input: 0.27, output: 1.10 },
  "qwen2.5-coder-32b": { input: 0.35, output: 0.40 },
};

function loadCosts() {
  try {
    if (fs.existsSync(COST_FILE)) {
      return JSON.parse(fs.readFileSync(COST_FILE, "utf8"));
    }
  } catch (e) {}
  return { totalCost: 0, calls: 0, sessions: [], dailyCosts: {} };
}

function saveCosts(data) {
  try {
    fs.writeFileSync(COST_FILE, JSON.stringify(data, null, 2));
  } catch (e) {}
}

let input = "";
process.stdin.on("data", (c) => { input += c; });
process.stdin.on("end", () => {
  try {
    const event = JSON.parse(input);
    const costs = loadCosts();

    if (event.event === "PostToolUse") {
      const model = (event.model || "unknown").toLowerCase();
      const costKey = Object.keys(MODEL_COSTS).find(k => model.includes(k));
      let estimated = 0;
      if (costKey && event.tokens) {
        const rates = MODEL_COSTS[costKey];
        const inTokens = (event.tokens.input || 0) / 1000000;
        const outTokens = (event.tokens.output || 0) / 1000000;
        estimated = (inTokens * rates.input) + (outTokens * rates.output);
      }

      if (estimated > 0) {
        costs.totalCost = (costs.totalCost || 0) + estimated;
        costs.calls = (costs.calls || 0) + 1;
        const today = new Date().toISOString().slice(0, 10);
        costs.dailyCosts[today] = (costs.dailyCosts[today] || 0) + estimated;

        costs.sessions.push({
          time: new Date().toISOString(),
          model: event.model || "unknown",
          cost: estimated,
          tokens: event.tokens || {},
        });
        if (costs.sessions.length > 100) costs.sessions = costs.sessions.slice(-100);
        saveCosts(costs);
      }
    }

    if (event.event === "PreToolUse") {
      const costs = loadCosts();
      if (costs.totalCost > 0) {
        console.error(JSON.stringify({
          level: "info",
          message: `💰 Session cost: $${costs.totalCost.toFixed(4)} (${costs.calls} calls)`
        }));
      }
    }

    process.stdout.write(JSON.stringify({ allow: true }) + "\n");
  } catch (e) {
    process.stdout.write(JSON.stringify({ allow: true }) + "\n");
  }
});
