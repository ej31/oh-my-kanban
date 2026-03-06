// Plane 입력값 검증 모듈

/**
 * Workspace slug 형식: 소문자·숫자·하이픈
 * 하이픈으로 시작하거나 끝나는 것은 허용하지 않는다.
 */
const SLUG_REGEX = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/;

/** Plane API 키 최소 길이 */
const MIN_API_KEY_LENGTH = 10;

const TIMEOUT_MS = 10_000;

export interface ConnectionResult {
  ok: boolean;
  error?: string;
}

/** Plane API 키 형식 검증 */
export function validatePlaneApiKeyFormat(value: string): string | undefined {
  if (!value.trim()) return 'API 키를 입력해주세요';
  if (value.trim().length < MIN_API_KEY_LENGTH) {
    return `API 키가 너무 짧습니다 (${MIN_API_KEY_LENGTH}자 이상이어야 합니다)`;
  }
}

/** Workspace slug 형식 검증 */
export function validateWorkspaceSlugFormat(value: string): string | undefined {
  if (!value.trim()) return 'Workspace slug를 입력해주세요';
  if (!SLUG_REGEX.test(value.trim())) {
    return 'Workspace slug는 소문자, 숫자, 하이픈(-)만 사용할 수 있으며 하이픈으로 시작하거나 끝날 수 없습니다';
  }
}

/**
 * Plane API 키와 workspace slug를 실제 API 호출로 검증한다.
 * GET {baseUrl}/api/v1/workspaces/{workspaceSlug}/ 로 접근 가능 여부 확인.
 */
export async function testPlaneConnection(
  baseUrl: string,
  apiKey: string,
  workspaceSlug: string
): Promise<ConnectionResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  const normalizedBase = baseUrl.replace(/\/$/, '');
  const url = `${normalizedBase}/api/v1/workspaces/${workspaceSlug}/`;

  try {
    const response = await fetch(url, {
      headers: { 'X-API-Key': apiKey },
      signal: controller.signal,
    });

    if (response.status === 401 || response.status === 403) {
      return { ok: false, error: 'API 키가 유효하지 않습니다' };
    }

    if (response.status === 404) {
      return {
        ok: false,
        error: `Workspace '${workspaceSlug}'를 찾을 수 없습니다. slug를 다시 확인하세요.`,
      };
    }

    if (!response.ok) {
      return { ok: false, error: `Plane 서버 응답 오류: ${response.status}` };
    }

    return { ok: true };
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      return {
        ok: false,
        error: `Plane API 연결 시간이 초과되었습니다 (${TIMEOUT_MS / 1000}초)`,
      };
    }
    return {
      ok: false,
      error: `연결 실패: ${err instanceof Error ? err.message : String(err)}`,
    };
  } finally {
    clearTimeout(timer);
  }
}
