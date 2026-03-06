// Linear validator 단위 테스트
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  validateLinearApiKeyFormat,
  validateLinearTeamIdFormat,
  testLinearConnection,
} from '../../validators/linear.js';

// ─────────────────────────────────────────────
// API 키 형식 검증
// ─────────────────────────────────────────────
describe('validateLinearApiKeyFormat', () => {
  it('빈 값은 에러', () => {
    expect(validateLinearApiKeyFormat('')).toBe('API 키를 입력해주세요');
    expect(validateLinearApiKeyFormat('   ')).toBe('API 키를 입력해주세요');
  });

  it('lin_api_ 접두사가 없으면 에러', () => {
    expect(validateLinearApiKeyFormat('some_random_key_that_is_long_enough_to_pass')).toMatch(
      /lin_api_/
    );
  });

  it('너무 짧은 키는 에러', () => {
    expect(validateLinearApiKeyFormat('lin_api_short')).toBeDefined();
  });

  it('올바른 형식은 통과', () => {
    expect(
      validateLinearApiKeyFormat('lin_api_' + 'a'.repeat(32))
    ).toBeUndefined();
  });

  it('앞뒤 공백은 trim 후 검증', () => {
    expect(
      validateLinearApiKeyFormat('  lin_api_' + 'a'.repeat(32) + '  ')
    ).toBeUndefined();
  });
});

// ─────────────────────────────────────────────
// Team ID 형식 검증
// ─────────────────────────────────────────────
describe('validateLinearTeamIdFormat', () => {
  it('빈 값은 에러', () => {
    expect(validateLinearTeamIdFormat('')).toBe('Team ID를 입력해주세요');
    expect(validateLinearTeamIdFormat('   ')).toBe('Team ID를 입력해주세요');
  });

  it('UUID가 아닌 형식은 에러', () => {
    expect(validateLinearTeamIdFormat('123123')).toBeDefined();
    expect(validateLinearTeamIdFormat('team_abc')).toBeDefined();
    expect(validateLinearTeamIdFormat('not-a-uuid')).toBeDefined();
  });

  it('올바른 UUID 형식은 통과', () => {
    expect(
      validateLinearTeamIdFormat('550e8400-e29b-41d4-a716-446655440000')
    ).toBeUndefined();
  });

  it('대소문자 구분 없이 UUID 허용', () => {
    expect(
      validateLinearTeamIdFormat('550E8400-E29B-41D4-A716-446655440000')
    ).toBeUndefined();
  });
});

// ─────────────────────────────────────────────
// API 연결 테스트 (fetch 모킹)
// ─────────────────────────────────────────────
describe('testLinearConnection', () => {
  const VALID_API_KEY = 'lin_api_' + 'a'.repeat(32);
  const VALID_TEAM_ID = '550e8400-e29b-41d4-a716-446655440000';

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('정상 응답 시 ok: true 반환', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        data: {
          viewer: { id: 'user-1' },
          team: { id: VALID_TEAM_ID, name: '테스트팀' },
        },
      }),
    }));

    const result = await testLinearConnection(VALID_API_KEY, VALID_TEAM_ID);
    expect(result.ok).toBe(true);
    expect(result.error).toBeUndefined();
  });

  it('401 응답 시 API 키 오류 메시지', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({}),
    }));

    const result = await testLinearConnection(VALID_API_KEY, VALID_TEAM_ID);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/API 키/);
  });

  it('403 응답 시 API 키 오류 메시지', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({}),
    }));

    const result = await testLinearConnection(VALID_API_KEY, VALID_TEAM_ID);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/API 키/);
  });

  it('viewer 없으면 API 키 오류', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: { viewer: null, team: null } }),
    }));

    const result = await testLinearConnection(VALID_API_KEY, VALID_TEAM_ID);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/API 키/);
  });

  it('team 없으면 Team ID 오류', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: { viewer: { id: 'user-1' }, team: null } }),
    }));

    const result = await testLinearConnection(VALID_API_KEY, VALID_TEAM_ID);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/Team ID/);
  });

  it('네트워크 오류 시 연결 실패 메시지', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('ECONNREFUSED')));

    const result = await testLinearConnection(VALID_API_KEY, VALID_TEAM_ID);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/연결 실패/);
  });

  it('AbortError 시 타임아웃 메시지', async () => {
    const abortError = new Error('aborted');
    abortError.name = 'AbortError';
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(abortError));

    const result = await testLinearConnection(VALID_API_KEY, VALID_TEAM_ID);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/초과/);
  });
});
