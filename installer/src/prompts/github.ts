import { note } from '@clack/prompts';

export async function promptGithubConfig(): Promise<void> {
  note(
    'GitHub 통합은 현재 준비 중입니다.\n향후 버전에서 지원될 예정입니다.',
    '준비 중'
  );
  process.exit(0);
}
