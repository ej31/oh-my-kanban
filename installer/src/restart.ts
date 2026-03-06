// 위저드 재시작 시그널 — 언어 선택부터 다시 시작한다.
export class RestartWizard extends Error {
  constructor() {
    super('restart');
  }
}

export const RESTART_SENTINEL = '__restart__';
