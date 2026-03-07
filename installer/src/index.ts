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
import { promptClaudeScope } from './prompts/claude-scope.js';
import { findPython, findPip, checkPythonVersion, installPackage } from './python.js';
import { writeConfig, type PlaneConfig, type LinearConfig } from './config-writer.js';
import { t } from './i18n.js';
import { RestartWizard } from './restart.js';

async function runSetup(): Promise<void> {
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
      project_id: result.projectId || undefined,
    };
  } else if (service === 'linear') {
    const result = await promptLinearConfig();
    linearConfig = {
      linear_api_key: result.apiKey,
      linear_team_id: result.teamId,
    };
  } else {
    // GitHub는 config 파일이 없지만 Python 환경 + Claude Code 연동은 동일하게 설정
    await promptGithubConfig();
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

  // 5. 설정 파일 저장 (Plane/Linear만 해당, GitHub는 config 없음)
  if (planeConfig || linearConfig) {
    try {
      await writeConfig(planeConfig, linearConfig);
    } catch (err) {
      cancel(pc.red(`${m.configSaveFailed}${err instanceof Error ? err.message : String(err)}`));
      process.exit(1);
    }
  }

  // 6. Claude Code 연동 설정 (scope 선택 + hooks 설치 + MCP 안내)
  await promptClaudeScope(python);

  const outroMsg =
    service === 'plane' ? m.outroPlane
    : service === 'linear' ? m.outroLinear
    : m.outro;
  outro(pc.green(outroMsg));
}

async function main(): Promise<void> {
  printLogo();

  // 처음으로 돌아가기 선택 시 언어 선택부터 재시작하는 루프
  while (true) {
    try {
      await runSetup();
      break;
    } catch (err) {
      if (err instanceof RestartWizard) {
        // 언어 선택 화면부터 다시 시작
        continue;
      }
      throw err;
    }
  }
}

main().catch((err: unknown) => {
  console.error(pc.red(t().unexpectedError), err);
  process.exit(1);
});
