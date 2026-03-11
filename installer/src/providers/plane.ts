import { cancel, confirm, isCancel, password, text } from '@clack/prompts';

export type PlaneConfig = {
  baseUrl: string;
  apiKey: string;
  workspaceSlug: string;
  projectId?: string;
};


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

  const apiKey = await password({
    message: 'Plane API key',
    validate(input) {
      if (!input.trim()) return 'Plane API key is required.';
    },
  });
  if (isCancel(apiKey)) {
    cancel('Operation cancelled.');
    process.exit(0);
  }

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
    apiKey: String(apiKey),
    workspaceSlug: extractWorkspaceSlug(String(workspaceInput)),
    projectId: String(projectId).trim() || undefined,
  };
}
