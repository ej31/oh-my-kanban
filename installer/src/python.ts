import { execSync, spawnSync } from 'node:child_process';

import { log, note, spinner } from '@clack/prompts';

const EXEC_TIMEOUT_MS = 30_000;
const EXEC_OPTIONS = { encoding: 'utf8' as const, stdio: 'pipe' as const, timeout: EXEC_TIMEOUT_MS };


export function findPython(): string | null {
  for (const command of ['python3', 'python']) {
    try {
      if (execSync(`which ${command}`, EXEC_OPTIONS).trim()) {
        return command;
      }
    } catch {
      continue;
    }
  }
  return null;
}


export function findPip(python: string): string | null {
  for (const command of ['pip3', 'pip']) {
    try {
      if (execSync(`which ${command}`, EXEC_OPTIONS).trim()) {
        return command;
      }
    } catch {
      continue;
    }
  }

  try {
    const result = spawnSync(python, ['-m', 'pip', '--version'], EXEC_OPTIONS);
    if (result.status === 0) return `${python} -m pip`;
  } catch {
    // noop
  }

  try {
    if (execSync('which uv', EXEC_OPTIONS).trim()) {
      return 'uv pip';
    }
  } catch {
    // noop
  }

  return null;
}


export function checkPythonVersion(python: string): void {
  const result = spawnSync(python, ['--version'], EXEC_OPTIONS);
  if (result.error) {
    throw new Error(`Python version check failed: ${result.error.message}`);
  }
  if (result.status !== 0) {
    throw new Error(`Python version check failed: ${result.stderr || 'unknown error'}`);
  }

  const output = `${result.stdout || result.stderr || ''}`.trim();
  const match = output.match(/Python (\d+)\.(\d+)/);
  if (!match) {
    throw new Error(`Could not parse Python version from '${output}'.`);
  }

  const major = Number(match[1]);
  const minor = Number(match[2]);
  if (major < 3 || (major === 3 && minor < 10)) {
    throw new Error(`Python 3.10+ is required. Current version: ${output}`);
  }
}


function splitPipCommand(pip: string): { cmd: string; args: string[] } {
  const parts = pip.split(' ');
  return { cmd: parts[0], args: parts.slice(1) };
}


function isPep668Error(stderr: string): boolean {
  return stderr.includes('externally-managed-environment') || stderr.includes('externally managed');
}


function hasPipx(): boolean {
  try {
    return Boolean(execSync('which pipx', EXEC_OPTIONS).trim());
  } catch {
    return false;
  }
}


export async function installPackage(
  pip: string,
  python: string,
  packageName = process.env.OMK_INSTALL_PACKAGE || 'oh-my-kanban',
): Promise<void> {
  if (process.argv.includes('--skip-install')) {
    log.warn('--skip-install detected; skipping Python package installation.');
    return;
  }

  const s = spinner();
  s.start(`Installing ${packageName} ...`);

  const { cmd, args } = splitPipCommand(pip);
  const result = spawnSync(cmd, [...args, 'install', packageName], EXEC_OPTIONS);

  if (result.status === 0) {
    s.stop(`Installed ${packageName}`);
    return;
  }

  s.stop(`pip install failed for ${packageName}`);
  const stderr = result.stderr ?? '';

  if (isPep668Error(stderr)) {
    log.warn('Detected externally managed Python environment (PEP 668).');

    if (hasPipx()) {
      const pipxSpinner = spinner();
      pipxSpinner.start(`Retrying ${packageName} with pipx ...`);
      const pipxResult = spawnSync('pipx', ['install', packageName], EXEC_OPTIONS);
      if (pipxResult.status === 0) {
        pipxSpinner.stop(`Installed ${packageName} with pipx`);
        return;
      }
      pipxSpinner.stop(`pipx install failed for ${packageName}`);
      throw new Error(pipxResult.stderr || pipxResult.stdout || 'pipx install failed');
    }

    note(
      [
        'This system uses an externally managed Python environment.',
        '',
        'Recommended:',
        '  brew install pipx',
        `  pipx install ${packageName}`,
        '',
        'Alternative:',
        `  ${python} -m pip install --user ${packageName}`,
      ].join('\n'),
      'PEP 668 guidance',
    );
    throw new Error('PEP 668 blocked direct installation.');
  }

  throw new Error(stderr || result.stdout || 'pip install failed');
}
