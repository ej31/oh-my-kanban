import { password, text, isCancel } from '@clack/prompts';
import { t } from '../i18n.js';

export interface LinearConfig {
  apiKey: string;
  teamId: string;
}

export async function promptLinearConfig(): Promise<LinearConfig> {
  const m = t();

  const apiKey = await password({
    message: m.linearApiKey,
    validate(value) {
      if (!value.trim()) return m.linearApiKeyRequired;
    },
  });

  if (isCancel(apiKey)) {
    process.exit(0);
  }

  const teamId = await text({
    message: m.linearTeamId,
    placeholder: m.linearTeamIdPlaceholder,
    validate(value) {
      if (!value.trim()) return m.linearTeamIdRequired;
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
