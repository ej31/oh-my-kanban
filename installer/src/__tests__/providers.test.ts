import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  validatePlaneApiKey,
  validatePlaneWorkspace,
} from '../providers/plane.js';
import {
  validateLinearApiKey,
  validateLinearTeamId,
} from '../providers/linear.js';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('plane validation helpers', () => {
  it('accepts a valid Plane API key response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }));
    await expect(validatePlaneApiKey('https://api.plane.so', 'pl_key')).resolves.toBe(true);
  });

  it('rejects an invalid Plane workspace response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }));
    await expect(validatePlaneWorkspace('https://api.plane.so', 'pl_key', 'team-a')).resolves.toBe(false);
  });
});

describe('linear validation helpers', () => {
  it('accepts a valid Linear API key response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: { viewer: { id: 'u1' } } }),
      }),
    );
    await expect(validateLinearApiKey('lin_key')).resolves.toBe(true);
  });

  it('rejects a missing Linear team', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: { team: null } }),
      }),
    );
    await expect(validateLinearTeamId('lin_key', 'team-1')).resolves.toBe(false);
  });
});
