---
name: omk-doctor
description: Performs integrated diagnostics on oh-my-kanban configuration, API, and hooks, and provides recovery guidance.
---

# omk-doctor Skill Execution Instructions

When a user runs `/omk-doctor`, perform the diagnostics in the following order.

## Step 1: API and Configuration Diagnostics

Run the following command:

```bash
omk doctor
```

Example output:

```text
Starting oh-my-kanban diagnostics...

  - [PASS] Config file: Configuration loaded (profile: default)
  - [PASS] plane-sdk version: plane-sdk 0.3.1
  - [PASS] Plane API connection: Authentication successful
  - [SKIP] Linear API connection: Linear API not configured
```

**If the omk command is not found**: Advise the user to run `pip install oh-my-kanban` followed by `omk hooks install`.

## Step 2: Hook Installation Diagnostics

Run the following command:

```bash
omk hooks status
```

Check hook installation status (global/project/personal-local) and active session list.

## Step 3: Output Comprehensive Report

Combine the output from both commands and present the report in the following format:

```text
## omk-doctor Diagnostic Report

| Item | Status | Details |
|------|--------|---------|
| Config file | OK | Configuration loaded (profile: default) |
| plane-sdk | OK | plane-sdk 0.3.1 |
| Plane API | OK | Authentication successful |
| Linear API | WARN | Linear API not configured (normal if not in use) |
| Hook installation | OK | Global hooks active (4 events) |
| Active sessions | OK | 1 |
```

Status mapping:
- `[PASS]` -> **OK**
- `[SKIP]` -> **WARN** (not configured but not an error)
- `[FAIL]` -> **CRITICAL**
- Hooks not installed -> **CRITICAL**

## Step 4: Recovery Guidance

If WARN or CRITICAL items are found, provide the following recovery methods:

| Issue | Recovery Method |
|-------|----------------|
| Config file missing / parse error | Run `/omk-setup` skill |
| Plane API key auth failure (401) | Issue a new API token in Plane, then re-run `/omk-setup` |
| Plane server connection failure | Check `base_url`, verify network status |
| plane-sdk version compatibility error | `pip install --upgrade oh-my-kanban` |
| Linear API key error | Issue a new token in Linear Settings > API, then re-run `/omk-setup` |
| Hooks not installed | `omk hooks install` or re-run `/omk-setup` skill |

If all items are OK: Output "All diagnostics passed."
