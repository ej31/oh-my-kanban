import { cancel, isCancel, password, spinner, text } from '@clack/prompts';

export type LinearConfig = {
  apiKey: string;
  teamId?: string;
};
const LINEAR_API_URL = 'https://api.linear.app/graphql';
const LINEAR_API_TIMEOUT_MS = 8_000;


async function executeLinearQuery(apiKey: string, query: string, variables?: Record<string, string>) {
  return fetch(LINEAR_API_URL, {
    method: 'POST',
    headers: {
      Authorization: apiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, variables: variables ?? {} }),
    signal: AbortSignal.timeout(LINEAR_API_TIMEOUT_MS),
  });
}


export async function validateLinearApiKey(apiKey: string): Promise<boolean> {
  try {
    const response = await executeLinearQuery(apiKey, '{ viewer { id } }');
    if (!response.ok) return false;
    const payload = (await response.json()) as { errors?: { message: string }[] };
    return !payload.errors?.length;
  } catch {
    return false;
  }
}


export async function validateLinearTeamId(apiKey: string, teamId: string): Promise<boolean> {
  if (!teamId.trim()) return true;
  try {
    const response = await executeLinearQuery(
      apiKey,
      'query Team($id: String!) { team(id: $id) { id } }',
      { id: teamId },
    );
    if (!response.ok) return false;
    const payload = (await response.json()) as {
      data?: { team?: { id: string } | null };
      errors?: { message: string }[];
    };
    return Boolean(payload.data?.team?.id) && !payload.errors?.length;
  } catch {
    return false;
  }
}


export async function promptLinearConfig(): Promise<LinearConfig> {
  let apiKey = '';
  while (!apiKey) {
    const value = await password({
      message: 'Linear API key',
      validate(input) {
        if (!input.trim()) return 'Linear API key is required.';
      },
    });
    if (isCancel(value)) {
      cancel('Operation cancelled.');
      process.exit(0);
    }

    const s = spinner();
    s.start('Validating Linear API key ...');
    const valid = await validateLinearApiKey(String(value));
    s.stop(valid ? 'Linear API key validated' : 'Linear API key validation failed');
    if (valid) {
      apiKey = String(value);
    }
  }

  let teamId: string | undefined;
  while (teamId === undefined) {
    const value = await text({
      message: 'Default Linear team ID (optional)',
      placeholder: 'team ID',
    });
    if (isCancel(value)) {
      cancel('Operation cancelled.');
      process.exit(0);
    }

    const candidate = String(value).trim();
    if (!candidate) {
      teamId = undefined;
      break;
    }

    const s = spinner();
    s.start('Validating Linear team ID ...');
    const valid = await validateLinearTeamId(apiKey, candidate);
    s.stop(valid ? 'Linear team ID validated' : 'Linear team ID validation failed');
    if (valid) {
      teamId = candidate;
    }
  }

  return {
    apiKey,
    teamId,
  };
}
