// Python/pip 탐지, 버전 확인, 패키지 설치 모듈 (PEP 668 대응)
import { execSync, spawnSync } from 'node:child_process';
import * as clack from '@clack/prompts';
import pc from 'picocolors';

const EXEC_TIMEOUT_MS = 30_000;
const EXEC_OPTIONS = { encoding: 'utf8' as const, stdio: 'pipe' as const, timeout: EXEC_TIMEOUT_MS };

/** Python 실행 가능 경로 탐지. 없으면 null */
export function findPython(): string | null {
  const candidates = ['python3', 'python'];
  for (const cmd of candidates) {
    try {
      const result = execSync(`which ${cmd}`, EXEC_OPTIONS).trim();
      if (result) return cmd;
    } catch {
      // 해당 명령어 없음, 다음 후보 시도
    }
  }
  return null;
}

/** pip 실행 가능 경로 탐지 순서: pip3 → pip → python -m pip → uv pip */
export function findPip(python: string): string | null {
  // pip3, pip 직접 실행 시도
  for (const cmd of ['pip3', 'pip']) {
    try {
      const result = execSync(`which ${cmd}`, EXEC_OPTIONS).trim();
      if (result) return cmd;
    } catch {
      // 다음 후보 시도
    }
  }

  // python -m pip 시도
  try {
    const result = spawnSync(python, ['-m', 'pip', '--version'], EXEC_OPTIONS);
    if (result.status === 0) return `${python} -m pip`;
  } catch {
    // 다음 후보 시도
  }

  // uv pip 시도
  try {
    const result = execSync('which uv', EXEC_OPTIONS).trim();
    if (result) return 'uv pip';
  } catch {
    // uv 없음
  }

  return null;
}

/** Python 버전 확인. 3.10+ 아니면 에러 */
export function checkPythonVersion(python: string): void {
  let output: string;
  // spawnSync 사용: execSync 셸 인젝션 방지 (python 파라미터가 external input일 수 있음)
  const result = spawnSync(python, ['--version'], EXEC_OPTIONS);
  if (result.error) {
    throw new Error(`Python 버전 확인 실패: ${result.error.message}`);
  }
  if (result.status !== 0) {
    throw new Error(`Python 버전 확인 실패: ${result.stderr || '알 수 없는 오류'}`);
  }
  output = (result.stdout ?? '').trim();

  // "Python 3.x.y" 형식에서 버전 추출
  const match = output.match(/Python (\d+)\.(\d+)/);
  if (!match) {
    throw new Error(`Python 버전 파싱 실패: "${output}"`);
  }

  const major = parseInt(match[1], 10);
  const minor = parseInt(match[2], 10);

  if (major < 3 || (major === 3 && minor < 10)) {
    throw new Error(
      `Python 3.10 이상이 필요합니다. 현재 버전: ${output}\n` +
      `https://www.python.org/downloads/ 에서 최신 버전을 설치하세요.`
    );
  }
}

/** PEP 668 에러 여부 확인 */
function isPep668Error(stderr: string): boolean {
  return (
    stderr.includes('externally-managed-environment') ||
    stderr.includes('externally managed')
  );
}

/** pipx 존재 여부 확인 */
function hasPipx(): boolean {
  try {
    const result = execSync('which pipx', EXEC_OPTIONS).trim();
    return Boolean(result);
  } catch {
    return false;
  }
}

/** pip 명령어를 배열 형태로 분리 */
function splitPipCmd(pip: string): { cmd: string; args: string[] } {
  const parts = pip.split(' ');
  return { cmd: parts[0], args: parts.slice(1) };
}

/** pip install 실행. PEP 668 감지 시 pipx 폴백 */
export async function installPackage(pip: string, python: string): Promise<void> {
  // --skip-install 플래그 확인
  if (process.argv.includes('--skip-install')) {
    clack.log.warn(pc.yellow('--skip-install 플래그 감지: 패키지 설치를 건너뜁니다.'));
    return;
  }

  const packageName = 'oh-my-kanban';
  const spinner = clack.spinner();

  spinner.start(`${packageName} 설치 중...`);

  const { cmd, args } = splitPipCmd(pip);
  const installArgs = [...args, 'install', packageName];

  const result = spawnSync(cmd, installArgs, {
    encoding: 'utf8',
    stdio: 'pipe',
    timeout: EXEC_TIMEOUT_MS,
  });

  // 설치 성공
  if (result.status === 0) {
    spinner.stop(pc.green(`${packageName} 설치 완료`));
    return;
  }

  spinner.stop(pc.red('pip install 실패'));

  const stderr = result.stderr ?? '';

  // PEP 668 (externally-managed-environment) 감지
  if (isPep668Error(stderr)) {
    clack.log.warn(
      pc.yellow('시스템이 외부 관리 Python 환경(PEP 668)을 사용 중입니다.')
    );

    if (hasPipx()) {
      // pipx로 자동 재시도
      const pipxSpinner = clack.spinner();
      pipxSpinner.start('pipx로 설치 시도 중...');

      const pipxResult = spawnSync('pipx', ['install', packageName], {
        encoding: 'utf8',
        stdio: 'pipe',
        timeout: EXEC_TIMEOUT_MS,
      });

      if (pipxResult.status === 0) {
        pipxSpinner.stop(pc.green(`pipx로 ${packageName} 설치 완료`));
        return;
      }

      pipxSpinner.stop(pc.red('pipx 설치도 실패했습니다.'));
      throw new Error(
        `pipx 설치 실패:\n${pipxResult.stderr ?? pipxResult.stdout ?? '알 수 없는 오류'}`
      );
    } else {
      // pipx 없음: 설치 안내
      clack.note(
        [
          pc.bold('pipx가 설치되어 있지 않습니다. 아래 방법 중 하나를 선택하세요:'),
          '',
          pc.cyan('방법 1) pipx 설치 후 재실행 (권장)'),
          `  ${pc.dim('macOS:')}  brew install pipx`,
          `  ${pc.dim('기타:')}   pip install pipx`,
          `  이후:   pipx install ${packageName}`,
          '',
          pc.cyan('방법 2) 사용자 디렉터리에 설치 (대안)'),
          `  ${python} -m pip install --user ${packageName}`,
          '',
          pc.red('방법 3) 시스템 보호 무시 (최후 수단, 비권장)'),
          `  ${pc.dim('⚠ 시스템 패키지 충돌 위험이 있습니다.')}`,
          `  ${python} -m pip install --break-system-packages ${packageName}`,
        ].join('\n'),
        'PEP 668 해결 방법'
      );

      throw new Error(
        'PEP 668: 시스템 관리 환경에서 직접 설치할 수 없습니다. 위 안내를 참고하세요.'
      );
    }
  }

  // 일반 pip 오류
  throw new Error(
    `pip install 실패:\n${stderr || result.stdout || '알 수 없는 오류'}`
  );
}

/** findPython의 테스트 호환 별칭 */
export { findPython as detectPython };
