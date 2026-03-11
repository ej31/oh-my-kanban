import { cancel, confirm, isCancel, password, spinner, text } from '@clack/prompts';

export type PlaneConfig = {
  baseUrl: string;
  apiKey: string;
  workspaceSlug: string;
  projectId?: string;
};
const PLANE_API_TIMEOUT_MS = 8_000;


function extractWorkspaceSlug(input: string): string {
  try {
    const url = new URL(input);
    const segments = url.pathname.split('/').filter(Boolean);
    if (segments.length > 0) {
      return segments[0];
    }
  } catch {
    return input.trim();
  }
  return input.trim();
}


async function fetchWithTimeout(url: string, apiKey: string): Promise<Response> {
  return fetch(url, {
    headers: { 'X-Api-Key': apiKey },
    signal: AbortSignal.timeout(PLANE_API_TIMEOUT_MS),
  });
}


export async function validatePlaneApiKey(baseUrl: string, apiKey: string): Promise<boolean> {
  try {
    const response = await fetchWithTimeout(`${baseUrl}/api/v1/users/me/`, apiKey);
    return response.ok;
  } catch {
    return false;
  }
}


export async function validatePlaneWorkspace(
  baseUrl: string,
  apiKey: string,
  workspaceSlug: string,
): Promise<boolean> {
  try {
    const response = await fetchWithTimeout(
      `${baseUrl}/api/v1/workspaces/${workspaceSlug}/projects/`,
      apiKey,
    );
    return response.ok;
  } catch {
    return false;
  }
}


export async function promptPlaneConfig(): Promise<PlaneConfig> {
  const selfHosted = await confirm({
    message: 'Are you using self-hosted Plane?',
    initialValue: false,
  });

  if (isCancel(selfHosted)) {
    cancel('Operation cancelled.');
    process.exit(0);
  }

  let baseUrl = 'https://api.plane.so';
  if (selfHosted) {
    const value = await text({
      message: 'Plane base URL',
      placeholder: 'https://plane.example.com',
      validate(input) {
        if (!input.trim()) return 'Base URL is required.';
        try {
          new URL(input);
          return;
        } catch {
          return 'Enter a valid URL.';
        }
      },
    });

    if (isCancel(value)) {
      cancel('Operation cancelled.');
      process.exit(0);
    }

    baseUrl = String(value).replace(/\/$/, '');
  }

  let apiKey = '';
  while (!apiKey) {
    const value = await password({
      message: 'Plane API key',
      validate(input) {
        if (!input.trim()) return 'Plane API key is required.';
      },
    });
    if (isCancel(value)) {
      cancel('Operation cancelled.');
      process.exit(0);
    }

    const s = spinner();
    s.start('Validating Plane API key ...');
    const valid = await validatePlaneApiKey(baseUrl, String(value));
    s.stop(valid ? 'Plane API key validated' : 'Plane API key validation failed');
    if (valid) {
      apiKey = String(value);
    }
  }

  let workspaceSlug = '';
  while (!workspaceSlug) {
    const workspaceInput = await text({
      message: 'Plane workspace slug or URL',
      placeholder: 'my-workspace or https://app.plane.so/my-workspace/',
      validate(input) {
        if (!input.trim()) return 'Workspace slug or URL is required.';
      },
    });
    if (isCancel(workspaceInput)) {
      cancel('Operation cancelled.');
      process.exit(0);
    }

    const candidate = extractWorkspaceSlug(String(workspaceInput));
    const s = spinner();
    s.start('Validating Plane workspace ...');
    const valid = await validatePlaneWorkspace(baseUrl, apiKey, candidate);
    s.stop(valid ? 'Plane workspace validated' : 'Plane workspace validation failed');
    if (valid) {
      workspaceSlug = candidate;
    }
  }

  const projectId = await text({
    message: 'Default Plane project UUID (optional)',
    placeholder: 'project UUID',
  });
  if (isCancel(projectId)) {
    cancel('Operation cancelled.');
    process.exit(0);
  }

  return {
    baseUrl,
    apiKey,
    workspaceSlug,
    projectId: String(projectId).trim() || undefined,
  };
}
