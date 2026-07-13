#!/usr/bin/env node
"use strict";
/**
 * block-no-verify — Pre-tool hook that warns if verification suite hasn't been run recently.
 * Inspired by ECC's block-no-verify pattern. Adapted for ZES system.
 */
const fs = require("fs");
const path = require("path");
const STATE_FILE = path.join(process.env.HOME || "/data/data/com.termux/files/home", ".hook-verify-state.json");
const MAX_AGE_MS = 30 * 60 * 1000; // 30 min

function getState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
    }
  } catch (e) {}
  return { lastVerify: 0, lastVerifyResult: "never" };
}

function setState(s) {
  try {
    fs.writeFileSync(STATE_FILE, JSON.stringify(s));
  } catch (e) {}
}

let input = "";
process.stdin.on("data", (c) => { input += c; });
process.stdin.on("end", () => {
  try {
    const event = JSON.parse(input);
    const state = getState();
    const now = Date.now();

    if (event.event === "PostToolUse") {
      // After any tool use, check if very old
      if (now - state.lastVerify > MAX_AGE_MS * 2) {
        console.error(JSON.stringify({
          level: "warn",
          message: `⚠️ No verification in ${Math.round((now - state.lastVerify) / 60000)}m. Run \`python3 ~/Zes-System/scripts/run-tests.py\``
        }));
      }
      process.stdout.write(JSON.stringify({ allow: true }) + "\n");
      return;
    }

    process.stdout.write(JSON.stringify({ allow: true }) + "\n");
  } catch (e) {
    process.stdout.write(JSON.stringify({ allow: true }) + "\n");
  }
});
