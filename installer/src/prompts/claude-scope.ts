import { select, note, spinner, isCancel } from '@clack/prompts';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import pc from 'picocolors';
import { t } from '../i18n.js';
import { RestartWizard, RESTART_SENTINEL } from '../restart.js';

// @clack/prompts의 note()는 문자 수로 박스 너비를 계산하여 한글(2열) 포함 시 박스가 깨짐.
// 각 줄의 와이드 문자 수만큼 공백을 추가해 표시 너비를 보정한다.
function padForNote(text: string): string {
  return text
    .split('\n')
    .map((line) => {
      let wideCount = 0;
      for (const char of line) {
        const code = char.codePointAt(0) ?? 0;
        if (
          (code >= 0xac00 && code <= 0xd7af) || // 한글 음절
          (code >= 0x1100 && code <= 0x11ff) || // 한글 자모
          (code >= 0x3130 && code <= 0x318f) || // 한글 호환 자모
          (code >= 0x4e00 && code <= 0x9fff) || // CJK 통합 한자
          (code >= 0xff01 && code <= 0xff60)    // 전각 ASCII
        ) {
          wideCount++;
        }
      }
      return wideCount > 0 ? line + ' '.repeat(wideCount) : line;
    })
    .join('\n');
}

export async function promptClaudeScope(python: string): Promise<void> {
  const m = t();

  // 범위 선택 전 추천 이유 안내
  note(padForNote(m.claudeScopeNote), m.claudeScopeTitle);

  const projectScopePath = join(process.cwd(), '.claude', 'settings.json');
  const userScopePath = join(process.env['HOME'] ?? '~', '.claude', 'settings.json');

  const scope = await select<string>({
    message: m.claudeScopeSelect,
    options: [
      { value: 'project', label: m.claudeScopeProject, hint: projectScopePath },
      { value: 'user', label: m.claudeScopeUser, hint: userScopePath },
      { value: RESTART_SENTINEL, label: m.returnToFirstStep },
    ],
  });

  if (isCancel(scope)) {
    process.exit(0);
  }

  if (scope === RESTART_SENTINEL) {
    throw new RestartWizard();
  }

  const isLocal = scope === 'project';
  const settingsPath = isLocal ? projectScopePath : userScopePath;

  // omk hooks install [--local] 실행
  const s = spinner();
  s.start(m.claudeHooksInstalling);

  const args = ['-m', 'oh_my_kanban', 'hooks', 'install'];
  if (isLocal) args.push('--local');

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
    m.claudeMcpTitle,
  );
}
