import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('node:child_process', () => ({
  execSync: vi.fn(),
  spawnSync: vi.fn(),
}));

vi.mock('@clack/prompts', () => ({
  log: { warn: vi.fn() },
  note: vi.fn(),
  spinner: vi.fn(() => ({
    start: vi.fn(),
    stop: vi.fn(),
  })),
}));

import { execSync, spawnSync } from 'node:child_process';

import { checkPythonVersion, findPip, findPython, installPackage } from '../python.js';

const mockExecSync = vi.mocked(execSync);
const mockSpawnSync = vi.mocked(spawnSync);

beforeEach(() => {
  vi.clearAllMocks();
  process.argv = ['node', 'index.js'];
  delete process.env.OMK_INSTALL_PACKAGE;
});

describe('findPython', () => {
  it('returns python3 when available', () => {
    mockExecSync.mockReturnValueOnce('/usr/bin/python3\n' as never);
    expect(findPython()).toBe('python3');
  });

  it('returns null when no python command is available', () => {
    mockExecSync.mockImplementation(() => {
      throw new Error('not found');
    });
    expect(findPython()).toBeNull();
  });
});

describe('findPip', () => {
  it('returns pip3 when available', () => {
    mockExecSync.mockReturnValueOnce('/usr/bin/pip3\n' as never);
    expect(findPip('python3')).toBe('pip3');
  });

  it('falls back to python -m pip', () => {
    mockExecSync.mockImplementation(() => {
      throw new Error('not found');
    });
    mockSpawnSync.mockReturnValueOnce({ status: 0 } as never);
    expect(findPip('python3')).toBe('python3 -m pip');
  });
});

describe('checkPythonVersion', () => {
  it('accepts python 3.10+', () => {
    mockSpawnSync.mockReturnValueOnce({
      status: 0,
      stdout: 'Python 3.12.1\n',
      stderr: '',
      error: undefined,
    } as never);
    expect(() => checkPythonVersion('python3')).not.toThrow();
  });

  it('rejects python 3.9', () => {
    mockSpawnSync.mockReturnValueOnce({
      status: 0,
      stdout: 'Python 3.9.1\n',
      stderr: '',
      error: undefined,
    } as never);
    expect(() => checkPythonVersion('python3')).toThrow('Python 3.10+ is required');
  });
});

describe('installPackage', () => {
  it('skips installation with --skip-install', async () => {
    process.argv = ['node', 'index.js', '--skip-install'];
    await expect(installPackage('pip3', 'python3')).resolves.toBeUndefined();
    expect(mockSpawnSync).not.toHaveBeenCalled();
  });

  it('resolves when pip install succeeds', async () => {
    mockSpawnSync.mockReturnValueOnce({ status: 0, stderr: '', stdout: '' } as never);
    await expect(installPackage('pip3', 'python3')).resolves.toBeUndefined();
  });
});
