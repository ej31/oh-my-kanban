import { confirm, text, password, select, isCancel, spinner } from '@clack/prompts';
import pc from 'picocolors';
import { t, type Messages } from '../i18n.js';
import { RestartWizard, RESTART_SENTINEL } from '../restart.js';
import { validateWorkspaceSlugFormat } from '../validators/plane.js';

export interface PlaneConfig {
  baseUrl: string;
  apiKey: string;
  workspaceSlug: string;
  projectId: string;
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
          const slug = extractWorkspaceSlug(value);
          return validateWorkspaceSlugFormat(slug);
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

  // 프로젝트 목록 자동 조회
  const sp = spinner();
  sp.start(m.planeFetchingProjects);

  let projects: { id: string; name: string }[] = [];
  try {
    const res = await fetch(`${baseUrl}/api/v1/workspaces/${workspaceSlug}/projects/`, {
      headers: { 'X-Api-Key': apiKey },
      signal: AbortSignal.timeout(PLANE_API_TIMEOUT_MS),
    });
    if (res.ok) {
      const json = await res.json() as { results?: { id: string; name: string }[] } | { id: string; name: string }[];
      const arr = Array.isArray(json) ? json : ((json as { results?: { id: string; name: string }[] }).results ?? []);
      projects = arr.filter((p) => p.id && p.name);
    }
  } catch {
    // 조회 실패 → 선택 없이 건너뛰기
  }
  sp.stop();

  // 프로젝트 선택 또는 생성
  const CREATE_SENTINEL = '__create__';
  let projectId = '';

  if (projects.length > 0) {
    // 기존 프로젝트 선택 메뉴
    while (true) {
      const selected = await select<string>({
        message: m.planeSelectProject,
        options: [
          ...projects.map((p) => ({ value: p.id, label: p.name })),
          { value: CREATE_SENTINEL, label: m.planeCreateProject },
          { value: RESTART_SENTINEL, label: m.returnToFirstStep },
        ],
      });

      if (isCancel(selected)) process.exit(0);
      if (selected === RESTART_SENTINEL) throw new RestartWizard();

      if (selected === CREATE_SENTINEL) {
        const created = await createProject(baseUrl, apiKey, workspaceSlug, m);
        if (created) {
          projectId = created;
          break;
        }
        // 생성 실패 → 선택 메뉴 재표시
        continue;
      }

      projectId = selected;
      break;
    }
  } else {
    // 프로젝트 없음 → 생성 필수
    while (true) {
      const action = await select<string>({
        message: m.planeNoProjectsFound,
        options: [
          { value: CREATE_SENTINEL, label: m.planeCreateProject },
          { value: RESTART_SENTINEL, label: m.returnToFirstStep },
        ],
      });

      if (isCancel(action)) process.exit(0);
      if (action === RESTART_SENTINEL) throw new RestartWizard();

      if (action === CREATE_SENTINEL) {
        const created = await createProject(baseUrl, apiKey, workspaceSlug, m);
        if (created) {
          projectId = created;
          break;
        }
        // 생성 실패 → 선택 메뉴 재표시
        continue;
      }
    }
  }

  return {
    baseUrl,
    apiKey,
    workspaceSlug,
    projectId,
  };
}

/** 프로젝트 이름에서 식별자를 자동 생성한다. 유니코드 글자/숫자를 모두 지원한다.
 *  예: "My Project" → "MP", "한글 프로젝트" → "한프", "テスト" → "テス"
 */
function generateIdentifier(name: string): string {
  const UNICODE_CHAR = /\p{L}|\p{N}/u;

  // 각 단어의 첫 번째 유니코드 글자/숫자를 이니셜로 추출
  const words = name.trim().split(/\s+/);
  const initials = words
    .map((w) => Array.from(w).find((ch) => UNICODE_CHAR.test(ch)) ?? '')
    .filter(Boolean)
    .join('')
    .toUpperCase();

  if (initials.length >= 2) return initials.slice(0, 6);

  // 단어가 하나뿐이면 유니코드 글자/숫자 앞 6자
  const chars = Array.from(name)
    .filter((ch) => UNICODE_CHAR.test(ch))
    .join('')
    .toUpperCase();
  if (chars.length > 0) return chars.slice(0, 6);

  // 모든 문자가 필터링된 경우 → 이름 기반 해시로 고유 식별자 생성
  const hash = Array.from(name).reduce(
    (acc, ch) => ((acc * 31 + ch.charCodeAt(0)) & 0xffff),
    0,
  );
  return `P${hash.toString(16).toUpperCase().slice(0, 5)}`;
}

/** 새 프로젝트를 생성하고 project id를 반환한다. 실패 시 null 반환 */
async function createProject(
  baseUrl: string,
  apiKey: string,
  workspaceSlug: string,
  m: Messages,
): Promise<string | null> {
  while (true) {
    const nameRaw = await text({
      message: m.planeProjectName,
      validate(value) {
        if (!value.trim()) return m.planeProjectNameRequired;
        if (value.trim().length > 255) return m.planeProjectNameTooLong;
      },
    });

    if (isCancel(nameRaw)) process.exit(0);

    const name = (nameRaw as string).trim();
    const identifier = generateIdentifier(name);

    const s = spinner();
    s.start(m.planeProjectCreating);

    try {
      const res = await fetch(`${baseUrl}/api/v1/workspaces/${workspaceSlug}/projects/`, {
        method: 'POST',
        headers: {
          'X-Api-Key': apiKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, identifier, network: 2 }),
        signal: AbortSignal.timeout(PLANE_API_TIMEOUT_MS),
      });

      if (res.ok) {
        const json = await res.json() as { id: string };
        s.stop(pc.green(`✓ ${m.planeProjectCreated}: ${name}`));
        // 생성된 프로젝트 URL 표시 (cloud는 app.plane.so, self-hosted는 baseUrl 그대로)
        const webBase = baseUrl === 'https://api.plane.so'
          ? 'https://app.plane.so'
          : baseUrl;
        console.log(pc.cyan(`  ${webBase}/${workspaceSlug}/projects/${json.id}/issues/`));
        return json.id;
      } else {
        const body = await res.text().catch(() => '');
        s.stop(pc.red(`✗ ${m.planeProjectCreateFailed}`));
        if (body) console.log(pc.dim(body.slice(0, 200)));
        // 실패 시 루프 탈출 (null 반환)
        return null;
      }
    } catch {
      s.stop(pc.red(`✗ ${m.planeProjectCreateFailed}`));
      return null;
    }
  }
}
