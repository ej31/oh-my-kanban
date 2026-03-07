import { select, note, spinner, isCancel } from '@clack/prompts';
import { spawnSync } from 'node:child_process';
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
  const userScopePath = join(process.env['HOME'] ?? '~', '.claude', 'settings.json');

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

  const settingsPath =
    scope === 'project' ? projectScopePath
    : scope === 'local' ? localScopePath
    : userScopePath;

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

  // MCP 서버 등록 안내
  note(
    padForNote(m.claudeMcpNote.replace('{path}', settingsPath)),
    padTitle(m.claudeMcpTitle),
  );
}
