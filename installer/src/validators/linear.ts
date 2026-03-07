// Linear 입력값 검증 모듈

/** Linear Personal API 키 형식: lin_api_ + 최소 32자 */
const LINEAR_API_KEY_REGEX = /^lin_api_[A-Za-z0-9]{32,}$/;

/** UUID v4 형식 */
const UUID_REGEX =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const TIMEOUT_MS = 10_000;

export interface ConnectionResult {
  ok: boolean;
  error?: string;
}

/** API 키 형식 검증 */
export function validateLinearApiKeyFormat(value: string): string | undefined {
  if (!value.trim()) return 'API 키를 입력해주세요';
  if (!LINEAR_API_KEY_REGEX.test(value.trim())) {
    return 'Linear API 키 형식이 올바르지 않습니다 (lin_api_로 시작하는 40자 이상이어야 합니다)';
  }
}

/** Team ID 형식 검증 (UUID) */
export function validateLinearTeamIdFormat(value: string): string | undefined {
  if (!value.trim()) return 'Team ID를 입력해주세요';
  if (!UUID_REGEX.test(value.trim())) {
    return 'Team ID는 UUID 형식이어야 합니다 (예: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)';
  }
}

/**
 * Linear API 키와 Team ID를 실제 API 호출로 검증한다.
 * - viewer 쿼리로 API 키 유효성 확인
 * - team 쿼리로 Team ID 존재 여부 확인
 */
export async function testLinearConnection(
  apiKey: string,
  teamId: string,
): Promise<ConnectionResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch('https://api.linear.app/graphql', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: apiKey,
      },
      body: JSON.stringify({
        query: 'query CheckTeam($id: String!) { viewer { id } team(id: $id) { id name } }',
        variables: { id: teamId },
      }),
      signal: controller.signal,
    });

    if (response.status === 401 || response.status === 403) {
      return { ok: false, error: 'API 키가 유효하지 않습니다' };
    }

    if (!response.ok) {
      return { ok: false, error: `Linear 서버 응답 오류: ${response.status}` };
    }

    const data = (await response.json()) as {
      data?: { viewer?: { id: string }; team?: { id: string; name: string } };
      errors?: Array<{ message: string }>;
    };

    if (!data.data?.viewer) {
      return { ok: false, error: 'API 키가 유효하지 않습니다' };
    }

    if (!data.data.team) {
      return {
        ok: false,
        error: `Team ID '${teamId}'를 찾을 수 없습니다. Linear 설정에서 Team ID를 확인하세요.`,
      };
    }

    return { ok: true };
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      return {
        ok: false,
        error: `Linear API 연결 시간이 초과되었습니다 (${TIMEOUT_MS / 1000}초)`,
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
