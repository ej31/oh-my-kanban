// python.ts 단위 테스트
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// node:child_process 모킹
vi.mock('node:child_process', () => ({
  execSync: vi.fn(),
  spawnSync: vi.fn(),
}));

// @clack/prompts 모킹
vi.mock('@clack/prompts', () => ({
  spinner: vi.fn(() => ({
    start: vi.fn(),
    stop: vi.fn(),
  })),
  log: {
    warn: vi.fn(),
  },
  note: vi.fn(),
}));

import { execSync, spawnSync } from 'node:child_process';
import * as clack from '@clack/prompts';
import {
  findPython,
  findPip,
  checkPythonVersion,
  installPackage,
} from '../python.js';

const mockExecSync = vi.mocked(execSync);
const mockSpawnSync = vi.mocked(spawnSync);

beforeEach(() => {
  vi.clearAllMocks();
  // --skip-install 플래그 없는 상태로 초기화
  process.argv = ['node', 'index.js'];
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ─────────────────────────────────────────────
// findPython
// ─────────────────────────────────────────────
describe('findPython', () => {
  it('python3가 있으면 "python3" 반환', () => {
    mockExecSync.mockReturnValueOnce('/usr/bin/python3\n' as any);
    expect(findPython()).toBe('python3');
  });

  it('python3 없고 python 있으면 "python" 반환', () => {
    mockExecSync
      .mockImplementationOnce(() => { throw new Error('not found'); })
      .mockReturnValueOnce('/usr/bin/python\n' as any);
    expect(findPython()).toBe('python');
  });

  it('모든 후보가 없으면 null 반환', () => {
    mockExecSync.mockImplementation(() => { throw new Error('not found'); });
    expect(findPython()).toBeNull();
  });
});

// ─────────────────────────────────────────────
// findPip
// ─────────────────────────────────────────────
describe('findPip', () => {
  it('pip3가 있으면 "pip3" 반환', () => {
    mockExecSync.mockReturnValueOnce('/usr/bin/pip3\n' as any);
    expect(findPip('python3')).toBe('pip3');
  });

  it('pip3 없고 pip 있으면 "pip" 반환', () => {
    mockExecSync
      .mockImplementationOnce(() => { throw new Error('not found'); })
      .mockReturnValueOnce('/usr/bin/pip\n' as any);
    expect(findPip('python3')).toBe('pip');
  });

  it('pip3/pip 없고 python -m pip 동작하면 "python3 -m pip" 반환', () => {
    mockExecSync.mockImplementation(() => { throw new Error('not found'); });
    mockSpawnSync.mockReturnValueOnce({ status: 0 } as any);
    expect(findPip('python3')).toBe('python3 -m pip');
  });

  it('모두 없고 uv 있으면 "uv pip" 반환', () => {
    mockExecSync
      .mockImplementationOnce(() => { throw new Error('not found'); }) // pip3
      .mockImplementationOnce(() => { throw new Error('not found'); }) // pip
      .mockReturnValueOnce('/usr/local/bin/uv\n' as any);             // uv
    mockSpawnSync.mockReturnValueOnce({ status: 1 } as any);           // python -m pip 실패
    expect(findPip('python3')).toBe('uv pip');
  });

  it('모두 없으면 null 반환', () => {
    mockExecSync.mockImplementation(() => { throw new Error('not found'); });
    mockSpawnSync.mockReturnValueOnce({ status: 1 } as any);
    expect(findPip('python3')).toBeNull();
  });
});

// ─────────────────────────────────────────────
// checkPythonVersion
// ─────────────────────────────────────────────
describe('checkPythonVersion', () => {
  it('Python 3.12는 통과', () => {
    mockSpawnSync.mockReturnValueOnce({ status: 0, stdout: 'Python 3.12.0\n', stderr: '', error: undefined } as any);
    expect(() => checkPythonVersion('python3')).not.toThrow();
  });

  it('Python 3.10는 통과', () => {
    mockSpawnSync.mockReturnValueOnce({ status: 0, stdout: 'Python 3.10.0\n', stderr: '', error: undefined } as any);
    expect(() => checkPythonVersion('python3')).not.toThrow();
  });

  it('Python 3.9는 에러', () => {
    mockSpawnSync.mockReturnValueOnce({ status: 0, stdout: 'Python 3.9.7\n', stderr: '', error: undefined } as any);
    expect(() => checkPythonVersion('python3')).toThrow('3.10 이상');
  });

  it('Python 2.7은 에러', () => {
    mockSpawnSync.mockReturnValueOnce({ status: 0, stdout: 'Python 2.7.18\n', stderr: '', error: undefined } as any);
    expect(() => checkPythonVersion('python3')).toThrow('3.10 이상');
  });

  it('버전 파싱 실패 시 에러', () => {
    mockSpawnSync.mockReturnValueOnce({ status: 0, stdout: 'unknown output\n', stderr: '', error: undefined } as any);
    expect(() => checkPythonVersion('python3')).toThrow('파싱 실패');
  });

  it('spawnSync 에러 시 에러', () => {
    mockSpawnSync.mockReturnValueOnce({ status: 1, stdout: '', stderr: '', error: new Error('exec failed') } as any);
    expect(() => checkPythonVersion('python3')).toThrow('버전 확인 실패');
  });
});

// ─────────────────────────────────────────────
// installPackage
// ─────────────────────────────────────────────
describe('installPackage', () => {
  it('--skip-install 플래그 있으면 설치 건너뜀', async () => {
    process.argv = ['node', 'index.js', '--skip-install'];
    await installPackage('pip3', 'python3');
    expect(mockSpawnSync).not.toHaveBeenCalled();
  });

  it('pip install 성공 시 정상 완료', async () => {
    mockSpawnSync.mockReturnValueOnce({ status: 0, stderr: '', stdout: '' } as any);
    await expect(installPackage('pip3', 'python3')).resolves.toBeUndefined();
  });

  it('PEP 668 감지 + pipx 있으면 pipx로 폴백 성공', async () => {
    // pip install 실패 (PEP 668)
    mockSpawnSync.mockReturnValueOnce({
      status: 1,
      stderr: 'error: externally-managed-environment',
      stdout: '',
    } as any);
    // which pipx 성공
    mockExecSync.mockReturnValueOnce('/usr/bin/pipx\n' as any);
    // pipx install 성공
    mockSpawnSync.mockReturnValueOnce({ status: 0, stderr: '', stdout: '' } as any);

    await expect(installPackage('pip3', 'python3')).resolves.toBeUndefined();
  });

  it('PEP 668 감지 + pipx 없으면 에러 + 안내 출력', async () => {
    mockSpawnSync.mockReturnValueOnce({
      status: 1,
      stderr: 'externally managed environment detected',
      stdout: '',
    } as any);
    mockExecSync.mockImplementationOnce(() => { throw new Error('pipx not found'); });

    await expect(installPackage('pip3', 'python3')).rejects.toThrow('PEP 668');
    expect(clack.note).toHaveBeenCalled();
  });

  it('일반 pip 실패 시 에러 던짐', async () => {
    mockSpawnSync.mockReturnValueOnce({
      status: 1,
      stderr: 'ERROR: some other pip error',
      stdout: '',
    } as any);

    await expect(installPackage('pip3', 'python3')).rejects.toThrow('pip install 실패');
  });
});
