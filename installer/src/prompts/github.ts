import { note } from '@clack/prompts';
import { spawnSync } from 'child_process';
import { t } from '../i18n.js';

// GitHub 태스크 관리에 필요한 필수 권한(scope)
// - repo: 이슈, PR 읽기/쓰기
// - project: GitHub Projects v2 관리
// - read:org: 조직 프로젝트 접근
const REQUIRED_SCOPES = ['repo', 'project', 'read:org'];

interface GhAuthResult {
  installed: boolean;
  authenticated: boolean;
  scopes: string[];
}

// gh 설치 여부 + 인증 상태 + 권한(scope) 한 번에 확인
function checkGhAuth(): GhAuthResult {
  const versionResult = spawnSync('gh', ['--version'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  if (versionResult.status !== 0 || versionResult.error) {
    return { installed: false, authenticated: false, scopes: [] };
  }

  // 미인증 시 exit code 1
  const authResult = spawnSync('gh', ['auth', 'status'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  if (authResult.status !== 0) {
    return { installed: true, authenticated: false, scopes: [] };
  }

  // stderr에서 Token scopes 파싱
  // 예시: Token scopes: 'gist', 'read:org', 'repo', 'workflow'
  const output = authResult.stderr || authResult.stdout || '';
  const scopeMatch = output.match(/Token scopes:\s*(.+)/);
  const scopes: string[] = scopeMatch
    ? scopeMatch[1].split(',').map((s) => s.trim().replace(/['"]/g, ''))
    : [];

  return { installed: true, authenticated: true, scopes };
}

// OS별 설치 안내 메시지 반환
function getInstallInstructions(m: ReturnType<typeof t>): string {
  const platform = process.platform;
  if (platform === 'darwin') return m.ghInstallMacOS;
  if (platform === 'win32') return m.ghInstallWindows;
  return m.ghInstallLinux;
}

// @clack/prompts의 note()는 문자 수로 박스 너비를 계산하여 한글(2열) 포함 시 박스가 깨짐.
// 각 줄의 와이드 문자 수만큼 공백을 추가해 표시 너비를 보정한다.
function padForNote(text: string): string {
  return text
    .split('\n')
    .map((line) => {
      let wideCount = 0;
      for (const char of line) {
        const code = char.codePointAt(0) ?? 0;
        if (
          (code >= 0xac00 && code <= 0xd7af) || // 한글 음절
          (code >= 0x1100 && code <= 0x11ff) || // 한글 자모
          (code >= 0x3130 && code <= 0x318f) || // 한글 호환 자모
          (code >= 0x4e00 && code <= 0x9fff) || // CJK 통합 한자
          (code >= 0xff01 && code <= 0xff60) // 전각 ASCII
        ) {
          wideCount++;
        }
      }
      return wideCount > 0 ? line + ' '.repeat(wideCount) : line;
    })
    .join('\n');
}

export async function promptGithubConfig(): Promise<void> {
  const m = t();
  const { installed, authenticated, scopes } = checkGhAuth();

  // 1. gh 미설치
  if (!installed) {
    const installGuide = getInstallInstructions(m);
    note(
      padForNote(`${installGuide}\n\n${m.ghAuthInstruction}\n\n${m.ghRerun}`),
      m.ghNotInstalled,
    );
    process.exit(0);
  }

  // 2. gh 설치됨 but 미인증
  if (!authenticated) {
    note(
      padForNote(`${m.ghAuthInstruction}\n\n${m.ghRerun}`),
      m.ghNotAuthenticated,
    );
    process.exit(0);
  }

  // 3. 필수 권한(scope) 부족 — 없으면 GitHub 기능을 사용할 수 없음
  const missingScopes = REQUIRED_SCOPES.filter((s) => !scopes.includes(s));
  if (missingScopes.length > 0) {
    const scopeArg = REQUIRED_SCOPES.join(',');
    note(
      padForNote(
        `${m.ghScopeMissing}: ${missingScopes.join(', ')}\n\n${m.ghAddScopes}\n  gh auth refresh --scopes ${scopeArg}\n\n${m.ghRerun}`,
      ),
      m.ghScopesRequired,
    );
    process.exit(0);
  }

  // 4. 설치 + 인증 + 권한 모두 확인 완료
  note(padForNote(m.ghReadyNote), m.ghReadyTitle);
  process.exit(0);
}
