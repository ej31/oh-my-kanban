import { password, text, isCancel } from '@clack/prompts';

export interface LinearConfig {
  apiKey: string;
  teamId: string;
}

export async function promptLinearConfig(): Promise<LinearConfig> {
  // API 키 (마스킹)
  const apiKey = await password({
    message: 'Linear API 키를 입력하세요',
    validate(value) {
      if (!value.trim()) return 'API 키를 입력해주세요';
    },
  });

  if (isCancel(apiKey)) {
    process.exit(0);
  }

  // Team ID
  const teamId = await text({
    message: 'Linear Team ID를 입력하세요',
    placeholder: 'team_xxxxxxxx',
    validate(value) {
      if (!value.trim()) return 'Team ID를 입력해주세요';
    },
  });

  if (isCancel(teamId)) {
    process.exit(0);
  }

  return {
    apiKey: apiKey as string,
    teamId: teamId as string,
  };
}
