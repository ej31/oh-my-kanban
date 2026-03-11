import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

import { note } from '@clack/prompts';
import pc from 'picocolors';

import type { LinearConfig } from './providers/linear.js';
import type { PlaneConfig } from './providers/plane.js';

export type InstallerConfigInput = {
  profile: string;
  output: 'table' | 'json' | 'plain';
  plane?: PlaneConfig;
  linear?: LinearConfig;
};


function getConfigPaths() {
  const configDir = join(homedir(), '.config', 'oh-my-kanban');
  return {
    configDir,
    configFile: join(configDir, 'config.toml'),
    backupFile: join(configDir, 'config.toml.bak'),
  };
}


export function escapeTomlValue(value: string): string {
  return value
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r');
}


function validateProfileName(name: string): boolean {
  return /^[a-zA-Z0-9_-]+$/.test(name);
}


function readExistingConfig(): string {
  const { configFile } = getConfigPaths();
  if (!existsSync(configFile)) return '';
  return readFileSync(configFile, 'utf8');
}


function removeProfileSections(content: string, profile: string): string {
  const sectionHeaderRe = /^\[([^\]]+)\]\s*$/;
  const lines = content.split('\n');
  const result: string[] = [];
  let inTargetSection = false;

  for (const line of lines) {
    const match = line.match(sectionHeaderRe);
    if (match) {
      const sectionName = match[1];
      inTargetSection = sectionName === profile || sectionName.startsWith(`${profile}.`);
      if (inTargetSection) {
        continue;
      }
    }
    if (!inTargetSection) {
      result.push(line);
    }
  }

  return result.join('\n');
}


function buildProfileSection(config: InstallerConfigInput): string {
  const lines: string[] = [`[${config.profile}]`, `output = "${escapeTomlValue(config.output)}"`, ''];

  if (config.plane) {
    lines.push(`[${config.profile}.plane]`);
    lines.push(`base_url = "${escapeTomlValue(config.plane.baseUrl)}"`);
    lines.push(`api_key = "${escapeTomlValue(config.plane.apiKey)}"`);
    lines.push(`workspace_slug = "${escapeTomlValue(config.plane.workspaceSlug)}"`);
    if (config.plane.projectId) {
      lines.push(`project_id = "${escapeTomlValue(config.plane.projectId)}"`);
    }
    lines.push('');
  }

  if (config.linear) {
    lines.push(`[${config.profile}.linear]`);
    lines.push(`api_key = "${escapeTomlValue(config.linear.apiKey)}"`);
    if (config.linear.teamId) {
      lines.push(`team_id = "${escapeTomlValue(config.linear.teamId)}"`);
    }
    lines.push('');
  }

  return lines.join('\n').trimEnd() + '\n';
}


export async function writeConfig(config: InstallerConfigInput): Promise<void> {
  if (!validateProfileName(config.profile)) {
    throw new Error('Profile names may only contain letters, numbers, hyphens, and underscores.');
  }
  if (!config.plane && !config.linear) {
    throw new Error('At least one provider must be configured.');
  }

  const { configDir, configFile, backupFile } = getConfigPaths();
  mkdirSync(configDir, { recursive: true });
  if (existsSync(configFile)) {
    copyFileSync(configFile, backupFile);
  }

  const existing = removeProfileSections(readExistingConfig(), config.profile);
  const content = `${existing.trimEnd()}${existing.trimEnd() ? '\n\n' : ''}${buildProfileSection(config)}`;
  writeFileSync(configFile, content, { encoding: 'utf8', mode: 0o600 });

  const lines = [
    `${pc.dim('path:')} ${configFile}`,
    `${pc.dim('profile:')} ${config.profile}`,
    `${pc.dim('providers:')} ${[config.plane && 'plane', config.linear && 'linear'].filter(Boolean).join(', ')}`,
  ];
  if (existsSync(backupFile)) {
    lines.push(`${pc.dim('backup:')} ${backupFile}`);
  }
  note(lines.join('\n'), pc.green('Config written'));
}
