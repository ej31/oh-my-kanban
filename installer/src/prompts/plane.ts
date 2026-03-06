import { confirm, text, password, select, isCancel, spinner } from '@clack/prompts';
import pc from 'picocolors';
import { t } from '../i18n.js';

export interface PlaneConfig {
  baseUrl: string;
  apiKey: string;
  workspaceSlug: string;
}

const PLANE_API_TIMEOUT_MS = 8000;

/**
 * URL에서 workspace slug를 추출한다.
 * 예: https://app.plane.so/my-workspace/projects/... -> my-workspace
 * 일반 문자열이면 그대로 반환한다.
 */
export function extractWorkspaceSlug(input: string): string {
  try {
    const url = new URL(input);
    // pathname: /my-workspace/projects/... → segments[1]
    const segments = url.pathname.split('/').filter(Boolean);
    if (segments.length > 0) {
      return segments[0];
    }
  } catch {
    // URL 파싱 실패 → 입력값을 slug로 간주
  }
  return input.trim();
}

export async function promptPlaneConfig(): Promise<PlaneConfig> {
  const m = t();

  const isSelfHosted = await confirm({
    message: m.isSelfHosted,
  });

  if (isCancel(isSelfHosted)) {
    process.exit(0);
  }

  // self-hosted가 아니면 기본 URL 사용, 아니면 사용자 입력
  let baseUrl: string;
  if (!isSelfHosted) {
    baseUrl = 'https://api.plane.so';
  } else {
    const baseUrlRaw = await text({
      message: m.planeServerUrl,
      placeholder: 'https://your-plane-instance.example.com',
      validate(value) {
        if (!value.trim()) return m.planeUrlRequired;
        try {
          new URL(value);
        } catch {
          return m.planeUrlInvalid;
        }
      },
    });

    if (isCancel(baseUrlRaw)) {
      process.exit(0);
    }
    baseUrl = (baseUrlRaw as string).replace(/\/$/, '');
  }

  // API 키 입력 + 실제 API 검증 루프
  // 연결 실패(서버 URL 문제) 시 URL 재입력, 인증 실패(API Key 문제) 시 API Key 재입력
  let apiKey = '';
  while (true) {
    const apiKeyRaw = await password({
      message: m.planeApiKey,
      validate(value) {
        if (!value.trim()) return m.planeApiKeyRequired;
      },
    });

    if (isCancel(apiKeyRaw)) {
      process.exit(0);
    }

    const s = spinner();
    s.start(m.planeValidating);
    let validationResult: 'ok' | 'authFailed' | 'connectFailed' = 'connectFailed';

    try {
      // /api/v1/users/me/ — 모든 Plane 버전에서 API Key 검증에 사용 가능한 엔드포인트
      const res = await fetch(`${baseUrl}/api/v1/users/me/`, {
        headers: { 'X-Api-Key': apiKeyRaw as string },
        signal: AbortSignal.timeout(PLANE_API_TIMEOUT_MS),
      });

      if (res.status === 401 || res.status === 403) {
        validationResult = 'authFailed';
        s.stop(pc.red(`✗ ${m.planeAuthFailed}`));
      } else if (!res.ok) {
        validationResult = 'connectFailed';
        s.stop(pc.red(`✗ ${m.planeConnectFailed}`));
      } else {
        validationResult = 'ok';
        s.stop(pc.green('✓'));
        apiKey = apiKeyRaw as string;
      }
    } catch {
      validationResult = 'connectFailed';
      s.stop(pc.red(`✗ ${m.planeConnectFailed}`));
    }

    if (validationResult === 'ok') break;

    // 연결 실패 → 서버 URL을 다시 입력받는다
    if (validationResult === 'connectFailed') {
      const newBaseUrlRaw = await text({
        message: m.planeServerUrl,
        defaultValue: 'https://api.plane.so',
        placeholder: 'https://api.plane.so',
        validate(value) {
          if (!value.trim()) return m.planeUrlRequired;
          try {
            new URL(value);
          } catch {
            return m.planeUrlInvalid;
          }
        },
      });
      if (isCancel(newBaseUrlRaw)) {
        process.exit(0);
      }
      baseUrl = (newBaseUrlRaw as string).replace(/\/$/, '');
    }
    // authFailed → 루프 상단에서 API Key만 재입력
  }

  // API Key 검증 성공 후 워크스페이스 목록 자동 조회
  const sw = spinner();
  sw.start(m.planeFetchingWorkspaces);

  let workspaces: { slug: string; name: string }[] = [];
  try {
    const res = await fetch(`${baseUrl}/api/v1/workspaces/`, {
      headers: { 'X-Api-Key': apiKey },
      signal: AbortSignal.timeout(PLANE_API_TIMEOUT_MS),
    });
    if (res.ok) {
      const json = (await res.json()) as { slug: string; name: string }[];
      workspaces = Array.isArray(json) ? json.filter((w) => w.slug && w.name) : [];
    }
  } catch {
    // 조회 실패 시 수동 입력으로 폴백
  }
  sw.stop();

  // 워크스페이스 선택 또는 수동 입력
  let workspaceSlug = '';

  if (workspaces.length > 0) {
    // 워크스페이스 목록 조회 성공 → select 프롬프트
    while (true) {
      const selected = await select<string>({
        message: m.planeSelectWorkspace,
        options: workspaces.map((w) => ({ value: w.slug, label: w.name, hint: w.slug })),
      });

      if (isCancel(selected)) {
        process.exit(0);
      }

      workspaceSlug = selected as string;
      break;
    }
  } else {
    // 워크스페이스 목록 조회 실패 → 수동 입력 + 검증
    while (true) {
      const workspaceInput = await text({
        message: m.planeWorkspace,
        placeholder: m.planeWorkspacePlaceholder,
        validate(value) {
          if (!value.trim()) return m.planeWorkspaceRequired;
        },
      });

      if (isCancel(workspaceInput)) {
        process.exit(0);
      }

      const slug = extractWorkspaceSlug(workspaceInput as string);
      const s = spinner();
      s.start(m.planeValidating);
      let valid = false;

      try {
        // /api/v1/workspaces/{slug}/projects/ — slug 검증에 사용 가능한 엔드포인트
        // /api/v1/workspaces/{slug}/ 는 일부 self-hosted 버전에서 401을 반환하므로 projects/ 사용
        const res = await fetch(`${baseUrl}/api/v1/workspaces/${slug}/projects/`, {
          headers: { 'X-Api-Key': apiKey },
          signal: AbortSignal.timeout(PLANE_API_TIMEOUT_MS),
        });

        if (res.status === 404 || res.status === 403) {
          // 404: slug 없음 / 403: Plane이 존재하지 않는 workspace에 접근 시 403으로 응답
          s.stop(pc.red(`✗ ${m.planeWorkspaceNotFound}`));
        } else if (res.status === 401) {
          s.stop(pc.red(`✗ ${m.planeAuthFailed}`));
        } else if (!res.ok) {
          s.stop(pc.red(`✗ ${m.planeConnectFailed}`));
        } else {
          s.stop(pc.green('✓'));
          workspaceSlug = slug;
          valid = true;
        }
      } catch {
        s.stop(pc.red(`✗ ${m.planeConnectFailed}`));
      }

      if (valid) break;
    }
  }

  console.log(pc.cyan(`  workspace slug: ${pc.bold(workspaceSlug)}`));

  return {
    baseUrl,
    apiKey,
    workspaceSlug,
  };
}
