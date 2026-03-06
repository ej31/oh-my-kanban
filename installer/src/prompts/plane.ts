import { confirm, text, password, isCancel } from '@clack/prompts';
import pc from 'picocolors';
import { t } from '../i18n.js';

export interface PlaneConfig {
  baseUrl: string;
  apiKey: string;
  workspaceSlug: string;
}

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

  const baseUrl = await text({
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

  if (isCancel(baseUrl)) {
    process.exit(0);
  }

  const apiKey = await password({
    message: m.planeApiKey,
    validate(value) {
      if (!value.trim()) return m.planeApiKeyRequired;
    },
  });

  if (isCancel(apiKey)) {
    process.exit(0);
  }

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

  const workspaceSlug = extractWorkspaceSlug(workspaceInput as string);

  console.log(pc.cyan(`  workspace slug: ${pc.bold(workspaceSlug)}`));

  return {
    baseUrl: baseUrl as string,
    apiKey: apiKey as string,
    workspaceSlug,
  };
}
