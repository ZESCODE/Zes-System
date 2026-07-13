# Hermes Agent Upgrade (v0.14.0 → v0.18.2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade Hermes AI Agent from v0.14.0 to v0.18.2 on the ZES Termux system

**Architecture:** The current install is an editable pip install (`pip install -e ~/hermes-agent-full/`). We'll replace it with a fresh PyPI install including Termux-specific extras, preserving config at `~/.hermes/` and all state.

**Tech Stack:** Python 3.13, pip, hermes-agent PyPI package, runsv service management

**Current state:**
- Hermes v0.14.0 at `~/hermes-agent-full/` (pip editable install)
- Config at `~/.hermes/config.yaml` (547 lines)
- Gateway running as runsv service `hermes-gateway` (PID 6826)
- Service auto-starts via `startall.sh`

---

### Task 1: Backup Current Hermes State

**Files:** Config files at `~/.hermes/`

- [x] **Step 1: Create backup with hermes CLI**

Run: `hermes backup -o ~/hermes-backup-v0.14.0.zip`
Expected: Creates zip file with config, state.db, auth, cron, sessions, skills

- [x] **Step 2: Also manually backup config**

Run: `cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.v0.14.0`

### Task 2: Stop the Hermes Gateway Service

**Files:** runsv service at `/data/data/com.termux/files/usr/var/service/hermes-gateway/`

- [x] **Step 1: Stop the gateway service**

Run: `sv stop hermes-gateway`
Expected: Service stops, gateway process exits

- [x] **Step 2: Verify gateway stopped**

Run: `hermes gateway status`
Expected: Shows gateway not running

### Task 3: Install Hermes Agent v0.18.2

**Files:** `~/hermes-agent-full/` (will be replaced), Python site-packages

- [x] **Step 1: Remove the old editable install**

Run: `pip uninstall hermes-agent -y`

- [x] **Step 2: Download the constraints file for v0.18.2**

Run: `curl -sL https://raw.githubusercontent.com/NousResearch/hermes-agent/refs/tags/v0.18.2/constraints-termux.txt -o /tmp/constraints-termux-v0.18.2.txt`

- [x] **Step 3: Install hermes-agent v0.18.2 with termux extras**

Run: `pip install hermes-agent[termux]==0.18.2 -c /tmp/constraints-termux-v0.18.2.txt`

- [x] **Step 4: Verify installation**

Run: `hermes --version`
Expected: `Hermes Agent v0.18.2 ...`

### Task 4: Run Post-Install Migration & Doctor

**Files:** `~/.hermes/config.yaml`

- [x] **Step 1: Run hermes doctor with --fix**

Run: `hermes doctor --fix`
Expected: Checks config, dependencies, and fixes any auto-fixable issues

- [x] **Step 2: Run config migration if needed**

Run: `hermes migrate --help` to check for available migrations

### Task 5: Restart Gateway Service

**Files:** runsv service

- [x] **Step 1: Start the gateway service**

Run: `sv start hermes-gateway`
Expected: Service starts

- [x] **Step 2: Verify gateway is running**

Run: `sv status hermes-gateway` and `hermes gateway status`
Expected: Both show running

### Task 6: Verify Functionality

- [x] **Step 1: Test basic hermes CLI works**

Run: `hermes status`
Expected: Shows system status

- [x] **Step 2: Test gateway health**

Run: `hermes gateway status`
Expected: Shows gateway running with details

- [x] **Step 3: Test model connectivity via 9Router**

Run: `hermes chat --message "Hello, respond with one word: OK" --yes --model gh/claude-sonnet-4.6`
Expected: Gets response from the model

- [x] **Step 4: Check startall.sh still works**

Run: `grep 'hermes-gateway' ~/startall.sh`
Expected: Service listed

### Task 7: Cleanup

- [ ] **Step 1: Remove old source directory**

Run: `rm -rf ~/hermes-agent-full`
(Only if no other references exist — the new install is from PyPI)

- [ ] **Step 2: Remove temp constraints file**

Run: `rm /tmp/constraints-termux-v0.18.2.txt`
