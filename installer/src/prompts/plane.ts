import { confirm, text, password, isCancel, spinner, cancel } from '@clack/prompts';
import pc from 'picocolors';
import {
  validatePlaneApiKeyFormat,
  validateWorkspaceSlugFormat,
  testPlaneConnection,
} from '../validators/plane.js';

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
  // self-hosted 여부 확인
  const isSelfHosted = await confirm({
    message: 'Plane을 직접 호스팅(self-hosted)하고 있나요?',
  });

  if (isCancel(isSelfHosted)) {
    process.exit(0);
  }

  // self-hosted가 아니면 기본 URL 사용, 아니면 사용자 입력
  let baseUrl: string;
  if (!isSelfHosted) {
    baseUrl = 'https://api.plane.so';
  } else {
    const baseUrlInput = await text({
      message: 'Plane 서버 URL을 입력하세요',
      placeholder: 'https://your-plane-instance.example.com',
      validate(value) {
        if (!value.trim()) return 'URL을 입력해주세요';
        try {
          new URL(value);
        } catch {
          return '올바른 URL 형식이 아닙니다 (예: https://your-plane-instance.example.com)';
        }
      },
    });

    if (isCancel(baseUrlInput)) {
      process.exit(0);
    }
    baseUrl = baseUrlInput as string;
  }

  // API 키 (마스킹) — 형식 검증 포함
  const apiKey = await password({
    message: 'Plane API 키를 입력하세요',
    validate(value) {
      return validatePlaneApiKeyFormat(value);
    },
  });

  if (isCancel(apiKey)) {
    process.exit(0);
  }

  // workspace slug (URL 또는 slug 직접 입력) — 추출 후 형식 검증
  const workspaceInput = await text({
    message: 'Workspace URL 또는 slug를 입력하세요',
    placeholder: 'https://app.plane.so/my-workspace/projects/... 또는 my-workspace',
    validate(value) {
      if (!value.trim()) return 'Workspace 정보를 입력해주세요';
      const slug = extractWorkspaceSlug(value);
      return validateWorkspaceSlugFormat(slug);
    },
  });

  if (isCancel(workspaceInput)) {
    process.exit(0);
  }

  const normalizedApiKey = (apiKey as string).trim();
  const workspaceSlug = extractWorkspaceSlug(workspaceInput as string);
  console.log(pc.cyan(`  workspace slug: ${pc.bold(workspaceSlug)}`));

  // 실제 API 연결 테스트
  const s = spinner();
  s.start('Plane API 연결을 확인하는 중...');

  const result = await testPlaneConnection(
    baseUrl,
    normalizedApiKey,
    workspaceSlug
  );

  if (!result.ok) {
    s.stop(pc.red(`연결 실패: ${result.error}`));
    cancel('입력한 값을 확인한 후 다시 시도하세요.');
    process.exit(1);
  }

  s.stop(pc.green('Plane API 연결 성공'));

  return {
    baseUrl,
    apiKey: normalizedApiKey,
    workspaceSlug,
  };
}
