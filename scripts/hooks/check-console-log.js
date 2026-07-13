#!/usr/bin/env node
"use strict";
/**
 * check-console-log — Post-tool hook that checks for stray console.log/print statements.
 * Adapted from ECC's check-console-log pattern for ZES code review.
 */
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const IGNORE_PATTERNS = [
  "console.error", "console.warn", "console.time",
  "console.timeEnd", "console.trace"
];
const SUSPECT_PATTERNS = [
  { pattern: "console.log", label: "console.log" },
  { pattern: "print(", label: "print()" },
  { pattern: "print ", label: "print statement" },
];

let input = "";
process.stdin.on("data", (c) => { input += c; });
process.stdin.on("end", () => {
  try {
    const event = JSON.parse(input);

    if (event.event === "PostToolUse" || event.event === "PostMessage") {
      // Check recent files in Zes-System
      const checks = [];
      try {
        const output = execSync(
          `cd ~/Zes-System && git diff --name-only HEAD~1 2>/dev/null || find . -name "*.py" -o -name "*.js" | head -20`,
          { encoding: "utf8", timeout: 5000, shell: true }
        );
        const files = output.trim().split("\n").filter(Boolean);
        for (const file of files.slice(0, 10)) {
          if (!fs.existsSync(file)) continue;
          const content = fs.readFileSync(file, "utf8");
          for (const sp of SUSPECT_PATTERNS) {
            if (content.includes(sp.pattern)) {
              const lines = content.split("\n");
              for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes(sp.pattern) && !IGNORE_PATTERNS.some(p => lines[i].includes(p))) {
                  checks.push(`${file}:${i + 1}: ${lines[i].trim().slice(0, 80)}`);
                }
              }
            }
          }
        }
      } catch (e) {}

      if (checks.length > 0) {
        console.error(JSON.stringify({
          level: "warn",
          message: `📋 Found ${checks.length} suspect log/print statement(s):\n${checks.join("\n")}`
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
