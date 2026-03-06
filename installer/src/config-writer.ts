// TOML 설정 파일 생성 모듈
// Python save_config()와 동일한 이스케이프 로직 사용
import { homedir } from 'node:os';
import { join } from 'node:path';
import { existsSync, mkdirSync, readFileSync, writeFileSync, copyFileSync } from 'node:fs';
import * as clack from '@clack/prompts';
import pc from 'picocolors';

const CONFIG_DIR = join(homedir(), '.config', 'oh-my-kanban');
const CONFIG_FILE = join(CONFIG_DIR, 'config.toml');
const CONFIG_BAK_FILE = join(CONFIG_DIR, 'config.toml.bak');

export interface PlaneConfig {
  base_url: string;
  api_key: string;
  workspace_slug: string;
}

export interface LinearConfig {
  linear_api_key: string;
  linear_team_id: string;
}

/** Python _escape_toml_string()와 동일 로직 (테스트용 공개 export) */
export function escapeTomlValue(value: string): string {
  return escapeTomlString(value);
}

/** Python _escape_toml_string()와 동일 로직 */
function escapeTomlString(value: string): string {
  return value
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r');
}

/** 프로필 이름 검증: 영문/숫자/언더스코어/하이픈만 허용 */
function validateProfileName(name: string): boolean {
  return /^[a-zA-Z0-9_-]+$/.test(name);
}

/** API 키 마스킹 (앞 4자 + **** + 뒤 4자) */
function maskApiKey(key: string): string {
  if (key.length <= 8) return '****';
  return `${key.slice(0, 4)}****${key.slice(-4)}`;
}

/**
 * 기존 TOML 파일에서 특정 프로필 섹션을 제거하거나 전체 내용을 읽어 반환.
 * 프로필이 이미 존재하면 해당 섹션을 교체한다.
 */
function readExistingConfig(): string {
  if (!existsSync(CONFIG_FILE)) return '';
  try {
    return readFileSync(CONFIG_FILE, 'utf8');
  } catch (err) {
    throw new Error(
      `기존 config.toml 읽기 실패: ${err instanceof Error ? err.message : String(err)}`
    );
  }
}

/**
 * TOML 텍스트에서 특정 프로필 섹션([profile_name] ~ 다음 섹션 직전)을 제거.
 * 줄 단위로 파싱하여 TOML 값 내부의 [section] 패턴과 혼동하지 않음.
 * 없으면 원본 그대로 반환.
 */
function removeProfileSection(content: string, profile: string): string {
  const lines = content.split('\n');
  const sectionHeaderRe = /^\[([^\]]+)\]$/;
  let inTargetSection = false;
  const result: string[] = [];

  for (const line of lines) {
    const match = line.match(sectionHeaderRe);
    if (match) {
      inTargetSection = match[1] === profile;
      if (inTargetSection) continue;
    }
    if (!inTargetSection) {
      result.push(line);
    }
  }
  return result.join('\n');
}

/** 프로필 TOML 섹션 문자열 생성 */
function buildProfileSection(
  profile: string,
  plane?: PlaneConfig,
  linear?: LinearConfig
): string {
  const lines: string[] = [`[${profile}]`];

  if (plane) {
    lines.push(`base_url = "${escapeTomlString(plane.base_url)}"`);
    lines.push(`api_key = "${escapeTomlString(plane.api_key)}"`);
    lines.push(`workspace_slug = "${escapeTomlString(plane.workspace_slug)}"`);
  }

  if (linear) {
    lines.push(`linear_api_key = "${escapeTomlString(linear.linear_api_key)}"`);
    lines.push(`linear_team_id = "${escapeTomlString(linear.linear_team_id)}"`);
  }

  return lines.join('\n') + '\n';
}

/** 통합 테스트용: 임의 경로에 TOML 파일을 동기 방식으로 쓴다 */
export interface TomlConfigRecord {
  base_url: string;
  api_key: string;
  workspace_slug: string;
  linear_api_key: string;
  linear_team_id: string;
}

export function writeConfigToml(filePath: string, config: TomlConfigRecord): void {
  const lines: string[] = ['[default]'];
  lines.push(`base_url = "${escapeTomlString(config.base_url)}"`);
  lines.push(`api_key = "${escapeTomlString(config.api_key)}"`);
  lines.push(`workspace_slug = "${escapeTomlString(config.workspace_slug)}"`);
  lines.push(`linear_api_key = "${escapeTomlString(config.linear_api_key)}"`);
  lines.push(`linear_team_id = "${escapeTomlString(config.linear_team_id)}"`);
  writeFileSync(filePath, lines.join('\n') + '\n', { encoding: 'utf8' });
}

/** config.toml 생성/업데이트. */
export async function writeConfig(
  plane?: PlaneConfig,
  linear?: LinearConfig,
  profile = 'default'
): Promise<void> {

  // 프로필 이름 검증
  if (!validateProfileName(profile)) {
    throw new Error(
      `유효하지 않은 프로필 이름: "${profile}"\n` +
      '프로필 이름은 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용할 수 있습니다.'
    );
  }

  // 설정할 내용이 없으면 에러
  if (!plane && !linear) {
    throw new Error('Plane 또는 Linear 설정 중 하나 이상을 제공해야 합니다.');
  }

  // 디렉터리 생성 (없으면)
  if (!existsSync(CONFIG_DIR)) {
    try {
      mkdirSync(CONFIG_DIR, { recursive: true });
    } catch (err) {
      throw new Error(
        `설정 디렉터리 생성 실패: ${CONFIG_DIR}\n` +
        `${err instanceof Error ? err.message : String(err)}`
      );
    }
  }

  // 기존 파일 백업
  if (existsSync(CONFIG_FILE)) {
    try {
      copyFileSync(CONFIG_FILE, CONFIG_BAK_FILE);
    } catch (err) {
      throw new Error(
        `기존 config.toml 백업 실패: ${err instanceof Error ? err.message : String(err)}`
      );
    }
  }

  // 기존 내용 읽기 + 해당 프로필 섹션 제거
  let existing = readExistingConfig();
  existing = removeProfileSection(existing, profile);

  // 새 프로필 섹션 추가
  const newSection = buildProfileSection(profile, plane, linear);
  const finalContent = (existing.trimEnd() ? existing.trimEnd() + '\n\n' : '') + newSection;

  // 파일 쓰기
  try {
    writeFileSync(CONFIG_FILE, finalContent, { encoding: 'utf8', mode: 0o600 });
  } catch (err) {
    throw new Error(
      `config.toml 쓰기 실패: ${err instanceof Error ? err.message : String(err)}`
    );
  }

  // 완료 요약 출력
  const summaryLines: string[] = [
    `${pc.dim('경로:')} ${CONFIG_FILE}`,
    `${pc.dim('프로필:')} ${profile}`,
  ];

  if (plane) {
    summaryLines.push('');
    summaryLines.push(pc.bold('[Plane]'));
    summaryLines.push(`  base_url:        ${plane.base_url}`);
    summaryLines.push(`  api_key:         ${maskApiKey(plane.api_key)}`);
    summaryLines.push(`  workspace_slug:  ${plane.workspace_slug}`);
  }

  if (linear) {
    summaryLines.push('');
    summaryLines.push(pc.bold('[Linear]'));
    summaryLines.push(`  linear_api_key:  ${maskApiKey(linear.linear_api_key)}`);
    summaryLines.push(`  linear_team_id:  ${linear.linear_team_id}`);
  }

  if (existsSync(CONFIG_BAK_FILE)) {
    summaryLines.push('');
    summaryLines.push(pc.dim(`백업: ${CONFIG_BAK_FILE}`));
  }

  clack.note(summaryLines.join('\n'), pc.green('설정 파일 저장 완료'));
}
