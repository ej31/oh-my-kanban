import { note } from '@clack/prompts';
import { spawnSync } from 'child_process';
import { t } from '../i18n.js';
import { padForNote, padTitle } from '../ui/pad-for-note.js';

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
  if (platform === 'linux') return m.ghInstallLinux;
  return m.ghInstallUnsupported;
}


export async function promptGithubConfig(): Promise<void> {
  const m = t();
  const { installed, authenticated, scopes } = checkGhAuth();

  // 1. gh 미설치
  if (!installed) {
    const installGuide = getInstallInstructions(m);
    note(
      padForNote(`${installGuide}\n\n${m.ghAuthInstruction}\n\n${m.ghRerun}`),
      padTitle(m.ghNotInstalled),
    );
    process.exit(1);
  }

  // 2. gh 설치됨 but 미인증
  if (!authenticated) {
    note(
      padForNote(`${m.ghAuthInstruction}\n\n${m.ghRerun}`),
      padTitle(m.ghNotAuthenticated),
    );
    process.exit(1);
  }

  // 3. 필수 권한(scope) 부족 — 없으면 GitHub 기능을 사용할 수 없음
  const missingScopes = REQUIRED_SCOPES.filter((s) => !scopes.includes(s));
  if (missingScopes.length > 0) {
    const scopeArg = REQUIRED_SCOPES.join(',');
    note(
      padForNote(
        `${m.ghScopeMissing}: ${missingScopes.join(', ')}\n\n${m.ghAddScopes}\n  gh auth refresh --scopes ${scopeArg}\n\n${m.ghRerun}`,
      ),
      padTitle(m.ghScopesRequired),
    );
    process.exit(1);
  }

  // 4. 실제 API 호출로 최종 검증 — 토큰이 만료/폐기됐을 경우를 잡아낸다
  const apiTestResult = spawnSync('gh', ['api', '/user'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  if (apiTestResult.status !== 0 || apiTestResult.error) {
    note(padForNote(m.ghApiTestFailed), padTitle(m.ghReadyTitle));
    process.exit(1);
  }

  // 5. 설치 + 인증 + 권한 + API 호출 모두 확인 완료
  note(padForNote(m.ghReadyNote), padTitle(m.ghReadyTitle));
}
