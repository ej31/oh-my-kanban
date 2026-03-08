---
name: omk-help
description: Provides guidance on using oh-my-kanban. When you enter a question, it answers with an FAQ.
---

# omk-help Skill Execution Guide

When a user executes `/omk-help` or `/omk-help [question]`, perform the following:

---

## No Arguments: Display Skill List

When executed without arguments, it displays the following skill list by category.

### Setup and Diagnostics

| Skill | Description |
| --- | --- |
| `/omk-setup` | Plane/Linear API setup wizard |
| `/omk-status` | Check hook installation status and active sessions |
| `/omk-doctor` | Integrated diagnosis of settings, API, and hooks |
| `/omk-help` | Display this help |

### WI Connection and Creation

| Skill | Description |
| --- | --- |
| `/omk-focus <WI-ID>` | Connect a specific WI to the current session |
| `/omk-create-task "<title>"` | Create a new WI and connect it to the session |
| `/omk-subtask "<title>"` | Create a subtask for the current WI |
| `/omk-done` | Mark the current WI as complete |
| `/omk-switch-task <WI-ID>` | Switch to another WI |
| `/oh-my-kanban:github-projects` | Manage GitHub Projects WIs with `gh` CLI (`/omk:gh` alias) |

### History and Notes

| Skill | Description |
| --- | --- |
| `/omk-note "<note>"` | Add a comment instantly to the current WI |
| `/omk-decision "<decision>"` | Record a decision as a comment |
| `/omk-handoff` | Create a handoff note |
| `/omk-snapshot` | Save a snapshot of the current session state |

### Query

| Skill | Description |
| --- | --- |
| `/omk-comments` | View recent comments for the current WI |
| `/omk-history [WI-ID]` | View WI activity history |
| `/omk-me` | My session summary |
| `/omk-sprint` | Current sprint progress |

### Advanced

| Skill | Description |
| --- | --- |
| `/omk-open` | Open the current WI in a browser |
| `/omk-context-sync` | Force synchronization of WI context |
| `/omk-disable-this-session` | Disable tracking for the current session |

If you have a question, enter it in the format `/omk-help [question]`.

---

## With Arguments: FAQ Answers

When the user enters a question, find and answer relevant items from the FAQ below.
If no relevant items are found, guide them to run `/omk-doctor` or check GitHub Issues.

### Installation and Setup

**Q: What should I do first?**
A: After installation, set up your Plane or Linear API key with the `/omk-setup` skill. Then, check the status with `/omk-status`.

**Q: Where do I get API keys?**
A: Plane -> Profile > API Tokens. Linear -> Settings > API > Personal API keys.

**Q: Where is the configuration file located?**
A: It is saved in `~/.config/oh-my-kanban/config.toml`. You can diagnose the file status with `/omk-doctor`.

**Q: What is `workspace_slug`?**
A: You can find it in the Plane URL in the form `https://<host>/<workspace_slug>/projects/...`.

**Q: I want to use different settings for multiple projects.**
A: Install `omk hooks install --local` in the project-specific `.claude/settings.json`, and specify `project_id` in `.omk/project.toml`.

### Hook Issues

**Q: How do I check if hooks are active?**
A: Run the `/omk-status` skill or the `omk hooks status` command.

**Q: Hooks are not working. Session context is not loading.**
A: Check in the following order:
1. Check hook installation status with `/omk-status`
2. If hooks are missing, reinstall with `omk hooks install`
3. Restart Claude Code completely
4. If still not working, perform a full diagnosis with `/omk-doctor`

**Q: How do I install hooks?**
A: Install interactively with the `/omk-setup` skill or directly run the `omk hooks install` command.

### WI Connection Issues

**Q: What is the format of a WI ID?**
A: Plane uses `<PROJECT>-<NUMBER>` (e.g., `DEV-42`), and Linear uses `<TEAM>-<NUMBER>` format.

**Q: Is there an `omk gh` command for GitHub Projects?**
A: No. GitHub-based WIs are managed through the `/oh-my-kanban:github-projects` or `/omk:gh` skill, using a combination of `gh issue` and `gh project`.

**Q: `omk focus` is not working. It says WI cannot be found.**
A: Check the following:
1. Check API connection status with `/omk-doctor`
2. Verify that the WI ID format is correct (e.g., `DEV-42`)
3. Check if `project_id` is set (`.omk/project.toml`)

**Q: What is a stale WI?**
A: It means a previously connected WI has been deleted or is inaccessible. Connect a new WI with `/omk-focus <new_WI_ID>` or disable tracking with `/omk-disable-this-session`.

**Q: Which WI is currently connected?**
A: Check the list of connected WIs for the current session with the `/omk-status` skill.

### Key Skill Usage

**Q: What is the difference between `omk-note` and `omk-decision`?**
A: `/omk-note` is for free-form notes, while `/omk-decision` leaves comments in a specialized format for recording decisions.

**Q: Does the WI status change automatically after running `omk-done`?**
A: Yes, it changes the connected WI to a 'Done' status. The 'Done' status must be configured in Plane.

**Q: How do I switch WIs during a session?**
A: Use the `/omk-switch-task <WI-ID>` skill to connect a new WI to the current session.

**Q: What if I can't find an answer?**
A: Run a full diagnosis with `/omk-doctor` or inquire on GitHub Issues.
GitHub Issues: https://github.com/ej31/oh-my-kanban/issues
