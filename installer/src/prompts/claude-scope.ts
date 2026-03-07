import { select, note, spinner, isCancel } from '@clack/prompts';
import { spawnSync } from 'node:child_process';
import { homedir } from 'node:os';
import { join } from 'node:path';
import pc from 'picocolors';
import { t } from '../i18n.js';
import { RestartWizard, RESTART_SENTINEL } from '../restart.js';
import { padForNote, padTitle } from '../ui/pad-for-note.js';

export async function promptClaudeScope(python: string): Promise<void> {
  const m = t();

  // 범위 선택 전 추천 이유 안내
  note(padForNote(m.claudeScopeNote), padTitle(m.claudeScopeTitle));

  const projectScopePath = join(process.cwd(), '.claude', 'settings.json');
  const localScopePath = join(process.cwd(), '.claude', 'settings.local.json');
  const userScopePath = join(homedir(), '.claude', 'settings.json');

  const scope = await select<string>({
    message: m.claudeScopeSelect,
    options: [
      { value: 'user', label: m.claudeScopeUser, hint: userScopePath },
      { value: 'project', label: m.claudeScopeProject, hint: projectScopePath },
      { value: 'local', label: m.claudeScopeLocal, hint: localScopePath },
      { value: RESTART_SENTINEL, label: m.returnToFirstStep },
    ],
  });

  if (isCancel(scope)) {
    process.exit(0);
  }

  if (scope === RESTART_SENTINEL) {
    throw new RestartWizard();
  }

  // omk hooks install [--local] [--local-only] 실행
  const s = spinner();
  s.start(m.claudeHooksInstalling);

  const args = ['-m', 'oh_my_kanban', 'hooks', 'install'];
  if (scope === 'project') args.push('--local');
  if (scope === 'local') args.push('--local-only');

  const result = spawnSync(python, args, {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  if (result.status !== 0 || result.error) {
    s.stop(pc.red(`✗ ${m.claudeHooksFailed}`));
    if (result.stderr?.trim()) {
      console.log(pc.dim(result.stderr.trim()));
    }
  } else {
    s.stop(pc.green(`✓ ${m.claudeHooksInstalled}`));
  }

  // MCP 서버 자동 등록
  const s2 = spinner();
  s2.start(m.claudeMcpInstalling);

  const mcpArgs = ['-m', 'oh_my_kanban', 'mcp', 'install'];
  if (scope === 'project') mcpArgs.push('--local');
  if (scope === 'local') mcpArgs.push('--local-only');

  const mcpResult = spawnSync(python, mcpArgs, {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  if (mcpResult.status !== 0 || mcpResult.error) {
    s2.stop(pc.red(`✗ ${m.claudeMcpFailed}`));
    if (mcpResult.stderr?.trim()) {
      console.log(pc.dim(mcpResult.stderr.trim()));
    }
  } else {
    s2.stop(pc.green(`✓ ${m.claudeMcpInstalled}`));
  }
}
