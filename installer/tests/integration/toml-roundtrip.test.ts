/**
 * TOML 라운드트립 통합 테스트
 *
 * TypeScript가 생성한 config.toml을 Python의 load_config()로 파싱했을 때
 * 값이 일치하는지 검증한다 (크로스런타임 호환성 테스트).
 *
 * 전제 조건: oh_my_kanban 패키지가 Python 환경에 설치되어 있어야 한다.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { execSync } from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { writeConfigToml } from '../../src/config-writer.js';
import { detectPython } from '../../src/python.js';

// Python 실행 파일 경로 (테스트 스위트 전체에서 공유)
let pythonBin: string | null = null;
// 임시 디렉토리 경로
let tmpDir: string;

const VERIFY_SCRIPT = path.resolve(
  __dirname,
  'verify_toml.py',
);

beforeAll(() => {
  pythonBin = detectPython();
  tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'omc-toml-test-'));
});

afterAll(() => {
  // 임시 디렉토리 정리
  try {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  } catch {
    // 정리 실패는 무시
  }
});

/**
 * Python 환경에 oh_my_kanban이 설치되어 있는지 확인한다.
 */
function isPythonPackageAvailable(): boolean {
  if (!pythonBin) return false;
  try {
    execSync(`${pythonBin} -c "import oh_my_kanban"`, { stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

/**
 * verify_toml.py를 실행해 config.toml을 파싱한 결과를 반환한다.
 */
function verifyToml(configPath: string): Record<string, string> {
  if (!pythonBin) {
    throw new Error('Python 실행 파일을 찾을 수 없다');
  }
  const output = execSync(
    `${pythonBin} "${VERIFY_SCRIPT}" "${configPath}"`,
    { stdio: 'pipe' },
  ).toString();
  return JSON.parse(output) as Record<string, string>;
}

describe('TOML 라운드트립: TypeScript 생성 → Python 파싱', () => {
  it('Plane 설정을 생성 후 verify_toml.py로 파싱하면 값이 일치한다', () => {
    if (!isPythonPackageAvailable()) {
      // oh_my_kanban 미설치 환경에서는 스킵
      console.warn('oh_my_kanban 패키지가 설치되어 있지 않아 통합 테스트를 건너뜁니다.');
      return;
    }

    const configPath = path.join(tmpDir, 'config-plane.toml');
    const planeConfig = {
      base_url: 'https://api.plane.so',
      api_key: 'plane-test-key-123',
      workspace_slug: 'my-workspace',
      linear_api_key: '',
      linear_team_id: '',
    };

    writeConfigToml(configPath, planeConfig);

    const parsed = verifyToml(configPath);

    expect(parsed.base_url).toBe(planeConfig.base_url);
    expect(parsed.api_key).toBe(planeConfig.api_key);
    expect(parsed.workspace_slug).toBe(planeConfig.workspace_slug);
  });

  it('Linear 설정을 생성 후 verify_toml.py로 파싱하면 값이 일치한다', () => {
    if (!isPythonPackageAvailable()) {
      console.warn('oh_my_kanban 패키지가 설치되어 있지 않아 통합 테스트를 건너뜁니다.');
      return;
    }

    const configPath = path.join(tmpDir, 'config-linear.toml');
    const linearConfig = {
      base_url: 'https://api.plane.so',
      api_key: '',
      workspace_slug: '',
      linear_api_key: 'lin_api_test_key_abc',
      linear_team_id: 'team-uuid-xyz',
    };

    writeConfigToml(configPath, linearConfig);

    const parsed = verifyToml(configPath);

    expect(parsed.linear_api_key).toBe(linearConfig.linear_api_key);
    expect(parsed.linear_team_id).toBe(linearConfig.linear_team_id);
  });
});
