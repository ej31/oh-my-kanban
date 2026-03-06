import { note } from '@clack/prompts';
import { execSync } from 'child_process';
import { t } from '../i18n.js';

// gh CLI 설치 여부 확인
function isGhInstalled(): boolean {
  try {
    execSync('gh --version', { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

// gh CLI 인증 여부 확인
function isGhAuthenticated(): boolean {
  try {
    execSync('gh auth status', { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
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

  if (!isGhInstalled()) {
    // gh 미설치: OS별 설치 안내 + 인증 안내 + 재실행 안내
    const installGuide = getInstallInstructions(m);
    note(
      `${installGuide}\n\n${m.ghAuthInstruction}\n\n${m.ghRerun}`,
      m.ghNotInstalled,
    );
    process.exit(0);
  }

  if (!isGhAuthenticated()) {
    // gh 설치됨 but 미인증: 인증 안내 + 재실행 안내
    note(`${m.ghAuthInstruction}\n\n${m.ghRerun}`, m.ghNotAuthenticated);
    process.exit(0);
  }

  // gh 설치 + 인증 완료
  note(m.ghReadyNote, m.ghReadyTitle);
  process.exit(0);
}
