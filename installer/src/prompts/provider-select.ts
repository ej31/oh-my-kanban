import { cancel, isCancel, multiselect } from '@clack/prompts';

import { getInstallerProviders } from '../provider-metadata.js';


export async function promptProviderSelection(): Promise<string[]> {
  const providers = getInstallerProviders();
  const selected = await multiselect<string>({
    message: 'Select providers to configure',
    options: providers.map((provider) => ({
      value: provider.name,
      label: provider.installer.label,
      hint: provider.installer.hint,
    })),
    required: true,
  });

  if (isCancel(selected)) {
    cancel('Operation cancelled.');
    process.exit(0);
  }

  return selected;
}
