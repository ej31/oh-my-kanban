/**
 * python 탐지 단위 테스트
 *
 * detectPython() 함수가 python3/python 실행 파일을 올바르게 탐지하는지 검증한다.
 * child_process.execSync를 vi.mock으로 모킹하여 실제 시스템 환경에 의존하지 않는다.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

// child_process 전체를 mock
vi.mock('child_process', () => ({
  execSync: vi.fn(),
}));

import { execSync } from 'child_process';
import { detectPython } from '../../src/python.js';

const mockExecSync = vi.mocked(execSync);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('detectPython', () => {
  it('python3가 존재할 때 python3 경로를 반환한다', () => {
    mockExecSync.mockImplementation((cmd: unknown) => {
      const command = cmd as string;
      if (command.includes('python3')) {
        return '/usr/bin/python3' as unknown as Buffer;
      }
      throw new Error('not found');
    });

    const result = detectPython();
    expect(result).toBe('python3');
  });

  it('python3가 없고 python이 있을 때 python을 반환한다', () => {
    mockExecSync.mockImplementation((cmd: unknown) => {
      const command = cmd as string;
      if (command.includes('python3')) {
        throw new Error('python3: command not found');
      }
      if (command.includes('python')) {
        return '/usr/bin/python' as unknown as Buffer;
      }
      throw new Error('not found');
    });

    const result = detectPython();
    expect(result).toBe('python');
  });

  it('python3, python 모두 없을 때 null을 반환한다', () => {
    mockExecSync.mockImplementation(() => {
      throw new Error('command not found');
    });

    const result = detectPython();
    expect(result).toBeNull();
  });
});
