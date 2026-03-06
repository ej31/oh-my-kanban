// Plane validator 단위 테스트
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  validatePlaneApiKeyFormat,
  validateWorkspaceSlugFormat,
  testPlaneConnection,
} from '../../validators/plane.js';

// ─────────────────────────────────────────────
// API 키 형식 검증
// ─────────────────────────────────────────────
describe('validatePlaneApiKeyFormat', () => {
  it('빈 값은 에러', () => {
    expect(validatePlaneApiKeyFormat('')).toBe('API 키를 입력해주세요');
    expect(validatePlaneApiKeyFormat('   ')).toBe('API 키를 입력해주세요');
  });

  it('10자 미만은 에러', () => {
    expect(validatePlaneApiKeyFormat('short')).toBeDefined();
    expect(validatePlaneApiKeyFormat('123456789')).toBeDefined();
  });

  it('10자 이상이면 통과', () => {
    expect(validatePlaneApiKeyFormat('1234567890')).toBeUndefined();
    expect(validatePlaneApiKeyFormat('plane-api-key-valid-long-enough')).toBeUndefined();
  });
});

// ─────────────────────────────────────────────
// Workspace slug 형식 검증
// ─────────────────────────────────────────────
describe('validateWorkspaceSlugFormat', () => {
  it('빈 값은 에러', () => {
    expect(validateWorkspaceSlugFormat('')).toBe('Workspace slug를 입력해주세요');
    expect(validateWorkspaceSlugFormat('   ')).toBe('Workspace slug를 입력해주세요');
  });

  it('대문자 포함은 에러', () => {
    expect(validateWorkspaceSlugFormat('MyWorkspace')).toBeDefined();
  });

  it('하이픈으로 시작/끝나면 에러', () => {
    expect(validateWorkspaceSlugFormat('-workspace')).toBeDefined();
    expect(validateWorkspaceSlugFormat('workspace-')).toBeDefined();
  });

  it('특수문자 포함은 에러', () => {
    expect(validateWorkspaceSlugFormat('my_workspace')).toBeDefined();
    expect(validateWorkspaceSlugFormat('my workspace')).toBeDefined();
    expect(validateWorkspaceSlugFormat('my.workspace')).toBeDefined();
  });

  it('1자 단독도 통과 (소문자/숫자)', () => {
    // 정규식: ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ → 1자도 허용
    expect(validateWorkspaceSlugFormat('a')).toBeUndefined();
  });

  it('올바른 slug는 통과', () => {
    expect(validateWorkspaceSlugFormat('my-workspace')).toBeUndefined();
    expect(validateWorkspaceSlugFormat('workspace123')).toBeUndefined();
    expect(validateWorkspaceSlugFormat('my-great-workspace')).toBeUndefined();
  });
});

// ─────────────────────────────────────────────
// API 연결 테스트 (fetch 모킹)
// ─────────────────────────────────────────────
describe('testPlaneConnection', () => {
  const BASE_URL = 'https://api.plane.so';
  const API_KEY = 'plane-api-key-valid';
  const SLUG = 'my-workspace';

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('정상 응답 시 ok: true 반환', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
    }));

    const result = await testPlaneConnection(BASE_URL, API_KEY, SLUG);
    expect(result.ok).toBe(true);
    expect(result.error).toBeUndefined();
  });

  it('올바른 URL을 호출한다', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200 });
    vi.stubGlobal('fetch', mockFetch);

    await testPlaneConnection('https://api.plane.so/', API_KEY, SLUG);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    // 트레일링 슬래시가 중복되지 않아야 한다
    expect(calledUrl).toBe(`https://api.plane.so/api/v1/workspaces/${SLUG}/`);
  });

  it('401 응답 시 API 키 오류 메시지', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }));

    const result = await testPlaneConnection(BASE_URL, API_KEY, SLUG);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/API 키/);
  });

  it('403 응답 시 API 키 오류 메시지', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 403 }));

    const result = await testPlaneConnection(BASE_URL, API_KEY, SLUG);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/API 키/);
  });

  it('404 응답 시 workspace 오류 메시지', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }));

    const result = await testPlaneConnection(BASE_URL, API_KEY, SLUG);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/Workspace/);
    expect(result.error).toContain(SLUG);
  });

  it('500 응답 시 서버 오류 메시지', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }));

    const result = await testPlaneConnection(BASE_URL, API_KEY, SLUG);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/500/);
  });

  it('네트워크 오류 시 연결 실패 메시지', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('ECONNREFUSED')));

    const result = await testPlaneConnection(BASE_URL, API_KEY, SLUG);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/연결 실패/);
  });

  it('AbortError 시 타임아웃 메시지', async () => {
    const abortError = new Error('aborted');
    abortError.name = 'AbortError';
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(abortError));

    const result = await testPlaneConnection(BASE_URL, API_KEY, SLUG);
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/초과/);
  });
});
