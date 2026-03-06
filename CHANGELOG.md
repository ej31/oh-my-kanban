# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Session context auto-recovery after `/compact`**: When Claude Code restarts after running the `/compact` command, oh-my-kanban automatically recovers session context through the `SessionStart(compact)` hook
  - Recovers session objective, modified files list, and request statistics
  - Automatically fetches linked Plane Work Item details (title, description, recent comments)
  - Limits: Maximum 3 WI retrieval, 3,000 character total context (600 chars per WI description, 300 chars per WI comments)

### Changed

### Fixed

### Deprecated

### Removed

### Security

## [0.1.2] - 2024-03-06

### Added

- `npx oh-my-kanban` wizard setup command
- Linear TOML configuration fix

### Fixed

- Linear API configuration parsing

## [0.1.1] - 2024-03-05

### Changed

- License field converted to SPDX format

## [0.1.0] - Initial Release

### Added

- Plane project management support (CRUD operations for work items, cycles, modules, milestones, intake, initiatives, teamspaces, stickies, custom properties)
- Linear project management support (issues, teams, states, labels, projects, cycles)
- Multi-workspace profile management
- Configuration management (init, show, set, profile commands)
- Multiple output formats (table, JSON, plain text)
- Agent-friendly zero-interaction mode via environment variables
