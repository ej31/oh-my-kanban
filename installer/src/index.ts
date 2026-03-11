#!/usr/bin/env node

import { cancel, intro, isCancel, outro, select, text } from '@clack/prompts';
import pc from 'picocolors';

import {
  writeConfig,
  type InstallerConfigInput,
  type LinearConfig,
  type PlaneConfig,
} from './config-writer.js';
import { findPip, findPython, checkPythonVersion, installPackage } from './python.js';
import { promptProviderSelection } from './prompts/provider-select.js';
import { promptLinearConfig } from './providers/linear.js';
import { promptPlaneConfig } from './providers/plane.js';


async function promptProfileName(): Promise<string> {
  const value = await text({
    message: 'Profile name',
    initialValue: 'default',
    validate(input) {
      if (!input.trim()) return 'Profile name is required.';
      if (!/^[a-zA-Z0-9_-]+$/.test(input.trim())) {
        return 'Use only letters, numbers, hyphens, and underscores.';
      }
    },
  });

  if (isCancel(value)) {
    cancel('Operation cancelled.');
    process.exit(0);
  }

  return String(value).trim();
}


async function promptOutputFormat(): Promise<'table' | 'json' | 'plain'> {
  const value = await select<'table' | 'json' | 'plain'>({
    message: 'Default output format',
    initialValue: 'table',
    options: [
      { value: 'table', label: 'table', hint: 'human-friendly default' },
      { value: 'json', label: 'json', hint: 'automation pipelines' },
      { value: 'plain', label: 'plain', hint: 'simple script parsing' },
    ],
  });

  if (isCancel(value)) {
    cancel('Operation cancelled.');
    process.exit(0);
  }

  return value;
}


async function main(): Promise<void> {
  intro(pc.bgCyan(pc.black(' oh-my-kanban setup ')));

  const profile = await promptProfileName();
  const output = await promptOutputFormat();
  const providers = await promptProviderSelection();

  let plane: PlaneConfig | undefined;
  let linear: LinearConfig | undefined;

  if (providers.includes('plane')) {
    plane = await promptPlaneConfig();
  }
  if (providers.includes('linear')) {
    linear = await promptLinearConfig();
  }

  const python = findPython();
  if (!python) {
    cancel('Python 3.10+ was not found in PATH.');
    process.exit(1);
  }

  try {
    checkPythonVersion(python);
  } catch (error) {
    cancel(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }

  const pip = findPip(python);
  if (!pip) {
    cancel('pip or uv pip was not found.');
    process.exit(1);
  }

  await installPackage(pip, python);

  const config: InstallerConfigInput = {
    profile,
    output,
    plane,
    linear,
  };
  await writeConfig(config);

  outro(pc.green(`Profile '${profile}' is ready. Run 'omk config show --profile ${profile}'.`));
}


main().catch((error: unknown) => {
  cancel(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
