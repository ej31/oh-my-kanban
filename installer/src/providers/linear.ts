import { cancel, isCancel, password, text } from '@clack/prompts';

export type LinearConfig = {
  apiKey: string;
  teamId?: string;
};


export async function promptLinearConfig(): Promise<LinearConfig> {
  const apiKey = await password({
    message: 'Linear API key',
    validate(input) {
      if (!input.trim()) return 'Linear API key is required.';
    },
  });
  if (isCancel(apiKey)) {
    cancel('Operation cancelled.');
    process.exit(0);
  }

  const teamId = await text({
    message: 'Default Linear team ID (optional)',
    placeholder: 'team ID',
  });
  if (isCancel(teamId)) {
    cancel('Operation cancelled.');
    process.exit(0);
  }

  return {
    apiKey: String(apiKey),
    teamId: String(teamId).trim() || undefined,
  };
}
