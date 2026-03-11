import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@clack/prompts', () => ({
  note: vi.fn(),
}));

import { escapeTomlValue, writeConfig } from '../config-writer.js';

describe('config writer', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('escapes TOML strings', () => {
    expect(escapeTomlValue('a"b\\c')).toBe('a\\"b\\\\c');
  });

  it('writes namespaced profile sections', async () => {
    const home = mkdtempSync(join(tmpdir(), 'omk-installer-home-'));
    vi.stubEnv('HOME', home);

    await writeConfig({
      profile: 'default',
      output: 'json',
      plane: {
        baseUrl: 'https://api.plane.so',
        apiKey: 'pl_key',
        workspaceSlug: 'team-a',
        projectId: 'proj-1',
      },
      linear: {
        apiKey: 'lin_key',
        teamId: 'lin-team',
      },
    });

    const saved = readFileSync(join(home, '.config', 'oh-my-kanban', 'config.toml'), 'utf8');
    expect(saved).toContain('[default]');
    expect(saved).toContain('[default.plane]');
    expect(saved).toContain('[default.linear]');
    expect(saved).toContain('workspace_slug = "team-a"');
    expect(saved).toContain('team_id = "lin-team"');
  });
});
