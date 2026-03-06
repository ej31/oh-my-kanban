// config-writer.ts 단위 테스트
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { homedir } from 'node:os';
import { join } from 'node:path';

// node:fs 모킹
vi.mock('node:fs', () => ({
  existsSync: vi.fn(),
  mkdirSync: vi.fn(),
  readFileSync: vi.fn(),
  writeFileSync: vi.fn(),
  copyFileSync: vi.fn(),
}));

// @clack/prompts 모킹
vi.mock('@clack/prompts', () => ({
  note: vi.fn(),
}));

import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
  copyFileSync,
} from 'node:fs';
import * as clack from '@clack/prompts';
import { writeConfig, type PlaneConfig, type LinearConfig } from '../config-writer.js';

const mockExistsSync = vi.mocked(existsSync);
const mockMkdirSync = vi.mocked(mkdirSync);
const mockReadFileSync = vi.mocked(readFileSync);
const mockWriteFileSync = vi.mocked(writeFileSync);
const mockCopyFileSync = vi.mocked(copyFileSync);

const CONFIG_DIR = join(homedir(), '.config', 'oh-my-kanban');
const CONFIG_FILE = join(CONFIG_DIR, 'config.toml');
const CONFIG_BAK_FILE = join(CONFIG_DIR, 'config.toml.bak');

const samplePlane: PlaneConfig = {
  base_url: 'https://plane.example.com',
  api_key: 'plane-api-key-1234567890',
  workspace_slug: 'my-workspace',
};

const sampleLinear: LinearConfig = {
  linear_api_key: 'lin_api_1234567890abcdef',
  linear_team_id: 'TEAM123',
};

beforeEach(() => {
  vi.clearAllMocks();
  // 기본: 디렉터리 없음, 파일 없음
  mockExistsSync.mockReturnValue(false);
  mockReadFileSync.mockReturnValue('' as any);
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ─────────────────────────────────────────────
// 프로필 이름 검증
// ─────────────────────────────────────────────
describe('프로필 이름 검증', () => {
  it('유효하지 않은 프로필 이름은 에러', async () => {
    await expect(
      writeConfig(samplePlane, undefined, 'invalid name!')
    ).rejects.toThrow('유효하지 않은 프로필 이름');
  });

  it('영문/숫자/언더스코어/하이픈은 유효', async () => {
    mockExistsSync.mockReturnValue(false);
    await expect(
      writeConfig(samplePlane, undefined, 'my-profile_01')
    ).resolves.toBeUndefined();
  });
});

// ─────────────────────────────────────────────
// 디렉터리 생성
// ─────────────────────────────────────────────
describe('디렉터리 생성', () => {
  it('CONFIG_DIR 없으면 mkdirSync 호출', async () => {
    mockExistsSync.mockReturnValue(false);
    await writeConfig(samplePlane);
    expect(mockMkdirSync).toHaveBeenCalledWith(CONFIG_DIR, { recursive: true });
  });

  it('CONFIG_DIR 있으면 mkdirSync 미호출', async () => {
    // CONFIG_DIR exists, CONFIG_FILE does not
    mockExistsSync.mockImplementation((p) => p === CONFIG_DIR);
    await writeConfig(samplePlane);
    expect(mockMkdirSync).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────
// 백업
// ─────────────────────────────────────────────
describe('기존 파일 백업', () => {
  it('기존 config.toml 있으면 .bak으로 복사', async () => {
    mockExistsSync.mockImplementation((p) => p === CONFIG_FILE || p === CONFIG_DIR);
    mockReadFileSync.mockReturnValue('' as any);
    await writeConfig(samplePlane);
    expect(mockCopyFileSync).toHaveBeenCalledWith(CONFIG_FILE, CONFIG_BAK_FILE);
  });

  it('기존 파일 없으면 copyFileSync 미호출', async () => {
    mockExistsSync.mockReturnValue(false);
    await writeConfig(samplePlane);
    expect(mockCopyFileSync).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────
// TOML 내용 생성
// ─────────────────────────────────────────────
describe('TOML 내용 생성', () => {
  it('Plane 설정으로 올바른 TOML 섹션 생성', async () => {
    mockExistsSync.mockReturnValue(false);
    await writeConfig(samplePlane, undefined, 'default');

    const written = mockWriteFileSync.mock.calls[0][1] as string;
    expect(written).toContain('[default]');
    expect(written).toContain(`base_url = "${samplePlane.base_url}"`);
    expect(written).toContain(`api_key = "${samplePlane.api_key}"`);
    expect(written).toContain(`workspace_slug = "${samplePlane.workspace_slug}"`);
  });

  it('Linear 설정으로 올바른 TOML 섹션 생성', async () => {
    mockExistsSync.mockReturnValue(false);
    await writeConfig(undefined, sampleLinear, 'default');

    const written = mockWriteFileSync.mock.calls[0][1] as string;
    expect(written).toContain('[default]');
    expect(written).toContain(`linear_api_key = "${sampleLinear.linear_api_key}"`);
    expect(written).toContain(`linear_team_id = "${sampleLinear.linear_team_id}"`);
  });

  it('특수문자 포함 값은 TOML 이스케이프 적용', async () => {
    mockExistsSync.mockReturnValue(false);
    const specialPlane: PlaneConfig = {
      base_url: 'https://plane.example.com/path?a=1&b=2',
      api_key: 'key"with"quotes',
      workspace_slug: 'slug\\with\\backslash',
    };
    await writeConfig(specialPlane, undefined, 'default');

    const written = mockWriteFileSync.mock.calls[0][1] as string;
    expect(written).toContain('key\\"with\\"quotes');
    expect(written).toContain('slug\\\\with\\\\backslash');
  });

  it('기존 프로필 섹션을 교체 (중복 방지)', async () => {
    const existingContent = '[default]\nbase_url = "https://old.example.com"\napi_key = "old-key"\nworkspace_slug = "old-workspace"\n';
    mockExistsSync.mockImplementation((p) => p === CONFIG_FILE || p === CONFIG_DIR);
    mockReadFileSync.mockReturnValue(existingContent as any);

    await writeConfig(samplePlane, undefined, 'default');

    const written = mockWriteFileSync.mock.calls[0][1] as string;
    expect(written).not.toContain('old-key');
    expect(written).toContain(samplePlane.api_key);
    // [default] 섹션이 하나만 존재
    expect((written.match(/\[default\]/g) ?? []).length).toBe(1);
  });

  it('다른 프로필은 유지하면서 해당 프로필만 교체', async () => {
    const existingContent = '[other]\nbase_url = "https://other.example.com"\napi_key = "other-key"\nworkspace_slug = "other"\n\n[default]\nbase_url = "https://old.example.com"\napi_key = "old-key"\nworkspace_slug = "old"\n';
    mockExistsSync.mockImplementation((p) => p === CONFIG_FILE || p === CONFIG_DIR);
    mockReadFileSync.mockReturnValue(existingContent as any);

    await writeConfig(samplePlane, undefined, 'default');

    const written = mockWriteFileSync.mock.calls[0][1] as string;
    expect(written).toContain('[other]');
    expect(written).toContain('other-key');
    expect(written).not.toContain('old-key');
    expect(written).toContain(samplePlane.api_key);
  });
});

// ─────────────────────────────────────────────
// 완료 출력
// ─────────────────────────────────────────────
describe('완료 출력', () => {
  it('성공 후 clack.note 호출', async () => {
    mockExistsSync.mockReturnValue(false);
    await writeConfig(samplePlane);
    expect(clack.note).toHaveBeenCalled();
  });

  it('API 키가 마스킹되어 출력됨', async () => {
    mockExistsSync.mockReturnValue(false);
    await writeConfig(samplePlane);
    const noteArg = vi.mocked(clack.note).mock.calls[0][0] as string;
    expect(noteArg).not.toContain(samplePlane.api_key);
    expect(noteArg).toContain('****');
  });
});

// ─────────────────────────────────────────────
// 에러 처리
// ─────────────────────────────────────────────
describe('에러 처리', () => {
  it('plane/linear 모두 없으면 에러', async () => {
    await expect(writeConfig()).rejects.toThrow('하나 이상을 제공');
  });

  it('mkdirSync 실패 시 에러 전파', async () => {
    mockExistsSync.mockReturnValue(false);
    mockMkdirSync.mockImplementationOnce(() => { throw new Error('permission denied'); });
    await expect(writeConfig(samplePlane)).rejects.toThrow('디렉터리 생성 실패');
  });

  it('writeFileSync 실패 시 에러 전파', async () => {
    mockExistsSync.mockReturnValue(false);
    mockWriteFileSync.mockImplementationOnce(() => { throw new Error('disk full'); });
    await expect(writeConfig(samplePlane)).rejects.toThrow('쓰기 실패');
  });
});
