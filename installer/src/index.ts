#!/usr/bin/env node
// oh-my-kanban 설치 위저드 진입점

import { intro, outro, cancel } from '@clack/prompts';
import pc from 'picocolors';
import { printLogo } from './ui/logo.js';
import { promptServiceSelect, type ServiceType } from './prompts/service-select.js';
import { promptPlaneConfig } from './prompts/plane.js';
import { promptLinearConfig } from './prompts/linear.js';
import { promptGithubConfig } from './prompts/github.js';
import { findPython, findPip, checkPythonVersion, installPackage } from './python.js';
import { writeConfig, type PlaneConfig, type LinearConfig } from './config-writer.js';

async function main(): Promise<void> {
  printLogo();
  intro(pc.bgCyan(pc.black(' oh-my-kanban 설정 위저드 ')));

  // 1. 서비스 선택
  const service: ServiceType = await promptServiceSelect();

  // 2. 서비스별 설정 수집 후 config-writer 타입으로 변환
  let planeConfig: PlaneConfig | undefined;
  let linearConfig: LinearConfig | undefined;

  if (service === 'plane') {
    const result = await promptPlaneConfig();
    planeConfig = {
      base_url: result.baseUrl,
      api_key: result.apiKey,
      workspace_slug: result.workspaceSlug,
    };
  } else if (service === 'linear') {
    const result = await promptLinearConfig();
    linearConfig = {
      linear_api_key: result.apiKey,
      linear_team_id: result.teamId,
    };
  } else {
    await promptGithubConfig();
    return;
  }

  // 3. Python 환경 확인
  const python = findPython();
  if (!python) {
    cancel(
      pc.red('Python을 찾을 수 없습니다. https://www.python.org/downloads/ 에서 Python 3.10 이상을 설치하세요.')
    );
    process.exit(1);
  }

  try {
    checkPythonVersion(python);
  } catch (err) {
    cancel(pc.red(err instanceof Error ? err.message : String(err)));
    process.exit(1);
  }

  const pip = findPip(python);
  if (!pip) {
    cancel(pc.red('pip을 찾을 수 없습니다. Python과 pip이 올바르게 설치되어 있는지 확인하세요.'));
    process.exit(1);
  }

  // 4. oh-my-kanban 패키지 설치
  try {
    await installPackage(pip, python);
  } catch (err) {
    cancel(pc.red(err instanceof Error ? err.message : String(err)));
    process.exit(1);
  }

  // 5. 설정 파일 저장
  try {
    await writeConfig(planeConfig, linearConfig);
  } catch (err) {
    cancel(pc.red(`설정 파일 저장 실패: ${err instanceof Error ? err.message : String(err)}`));
    process.exit(1);
  }

  outro(pc.green('설정이 완료되었습니다! `omk` 명령어로 시작하세요.'));
}

main().catch((err: unknown) => {
  console.error(pc.red('예상치 못한 오류가 발생했습니다:'), err);
  process.exit(1);
});
