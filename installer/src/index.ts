#!/usr/bin/env node
// oh-my-kanban 설치 위저드 진입점

import { intro, outro, cancel } from '@clack/prompts';
import pc from 'picocolors';
import { printLogo } from './ui/logo.js';
import { promptLangSelect } from './prompts/lang-select.js';
import { promptServiceSelect, type ServiceType } from './prompts/service-select.js';
import { promptPlaneConfig } from './prompts/plane.js';
import { promptLinearConfig } from './prompts/linear.js';
import { promptGithubConfig } from './prompts/github.js';
import { findPython, findPip, checkPythonVersion, installPackage } from './python.js';
import { writeConfig, type PlaneConfig, type LinearConfig } from './config-writer.js';
import { t } from './i18n.js';

async function main(): Promise<void> {
  printLogo();

  // 0. 언어 선택
  await promptLangSelect();

  const m = t();
  intro(pc.bgCyan(pc.black(` ${m.intro} `)));

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
    cancel(pc.red(m.pythonNotFound));
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
    cancel(pc.red(m.pipNotFound));
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
    cancel(pc.red(`${m.configSaveFailed}${err instanceof Error ? err.message : String(err)}`));
    process.exit(1);
  }

  outro(pc.green(m.outro));
}

main().catch((err: unknown) => {
  console.error(pc.red(t().unexpectedError), err);
  process.exit(1);
});
