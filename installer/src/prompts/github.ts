import { note } from '@clack/prompts';
import { spawnSync } from 'child_process';
import { t } from '../i18n.js';

// GitHub 태스크 관리에 필요한 권한(scope)
const REQUIRED_SCOPES = ['repo'];
const RECOMMENDED_SCOPES = ['project', 'read:org'];

interface GhAuthResult {
  installed: boolean;
  authenticated: boolean;
  scopes: string[];
}

// gh 설치 여부 + 인증 상태 + 권한(scope) 한 번에 확인
function checkGhAuth(): GhAuthResult {
  // 설치 여부 확인
  const versionResult = spawnSync('gh', ['--version'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  if (versionResult.status !== 0 || versionResult.error) {
    return { installed: false, authenticated: false, scopes: [] };
  }

  // 인증 상태 확인 (미인증 시 exit code 1)
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

export async function promptGithubConfig(): Promise<void> {
  const m = t();
  const { installed, authenticated, scopes } = checkGhAuth();

  // 1. gh 미설치
  if (!installed) {
    const installGuide = getInstallInstructions(m);
    note(
      `${installGuide}\n\n${m.ghAuthInstruction}\n\n${m.ghRerun}`,
      m.ghNotInstalled,
    );
    process.exit(0);
  }

  // 2. gh 설치됨 but 미인증
  if (!authenticated) {
    note(`${m.ghAuthInstruction}\n\n${m.ghRerun}`, m.ghNotAuthenticated);
    process.exit(0);
  }

  // 3. 필수 권한(scope) 부족
  const missingRequired = REQUIRED_SCOPES.filter((s) => !scopes.includes(s));
  if (missingRequired.length > 0) {
    const allNeeded = [
      ...missingRequired,
      ...RECOMMENDED_SCOPES.filter((s) => !scopes.includes(s)),
    ];
    const scopeArg = allNeeded.join(',');
    note(
      `${m.ghScopeMissing}: ${missingRequired.join(', ')}\n\n${m.ghAddScopes}\n  gh auth refresh --scopes ${scopeArg}\n\n${m.ghRerun}`,
      m.ghScopesRequired,
    );
    process.exit(0);
  }

  // 4. 설치 + 인증 + 권한 모두 확인 완료
  const missingRec = RECOMMENDED_SCOPES.filter((s) => !scopes.includes(s));
  const readyNote =
    missingRec.length > 0
      ? `${m.ghReadyNote}\n\n${m.ghRecommendedScopes}: ${missingRec.join(', ')}\n  gh auth refresh --scopes ${missingRec.join(',')}`
      : m.ghReadyNote;

  note(readyNote, m.ghReadyTitle);
  process.exit(0);
}
