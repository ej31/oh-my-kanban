import { confirm, text, password, isCancel, spinner } from '@clack/prompts';
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

  const baseUrlRaw = await text({
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

  if (isCancel(baseUrlRaw)) {
    process.exit(0);
  }

  let baseUrl = (baseUrlRaw as string).replace(/\/$/, '');

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
      const res = await fetch(`${baseUrl}/api/v1/workspaces/`, {
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

  // Workspace slug 입력 + 실제 API 검증 루프
  let workspaceSlug = '';
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
      const res = await fetch(`${baseUrl}/api/v1/workspaces/${slug}/`, {
        headers: { 'X-Api-Key': apiKey },
        signal: AbortSignal.timeout(PLANE_API_TIMEOUT_MS),
      });

      if (res.status === 404) {
        s.stop(pc.red(`✗ ${m.planeWorkspaceNotFound}`));
      } else if (res.status === 401 || res.status === 403) {
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

  console.log(pc.cyan(`  workspace slug: ${pc.bold(workspaceSlug)}`));

  return {
    baseUrl,
    apiKey,
    workspaceSlug,
  };
}
