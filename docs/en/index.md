---
layout: home
title: oh-my-kanban
titleTemplate: Plane + Claude Code Auto WI Integration

hero:
  name: oh-my-kanban
  text: Plane + Claude Code Integration
  tagline: Work Items update automatically while you code.
  actions:
    - theme: brand
      text: Get Started
      link: /en/getting-started
    - theme: alt
      text: GitHub
      link: https://github.com/ej31/oh-my-kanban

features:
  - icon: ⚡
    title: Automatic Session Tracking
    details: Plane Work Items are automatically updated with comments when Claude Code sessions start and end.
  - icon: 🔗
    title: WI Linking
    details: Use /oh-my-kanban:focus to link the current Work Item to your session.
  - icon: 📊
    title: Progress Visibility
    details: Drift detection, subtask completion nudges, and teammate comment polling keep you informed.
  - icon: 🛡️
    title: Fail-Open Design
    details: Hook failures never block Claude Code. Safe fail-open architecture by design.
---

## Quick Start

```bash
# Install from Claude Code marketplace
# Run inside Claude Code:
/install-github-app ej31/oh-my-kanban

# Or install directly
omk hooks install
```

## Core Principles

1. **WIs are records** — Sessions don't "own" WIs. Sessions "contribute" to WIs.
2. **No junk WIs** — Keep it visually clean and valuable long-term.
3. **No features without purpose** — "We might need it later" is an anti-pattern.
4. **Fail-open with transparency** — All hooks fail open, but failures are always surfaced.
