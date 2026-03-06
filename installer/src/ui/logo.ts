import { createRequire } from 'node:module';
import cfonts from 'cfonts';
import pc from 'picocolors';

const _require = createRequire(import.meta.url);
const { version: WIZARD_VERSION } = _require('../../package.json') as { version: string };

export function printLogo(): void {
  cfonts.say('OH MY|KANBAN', {
    font: 'block',
    align: 'left',
    colors: ['cyan', 'white'],
    background: 'transparent',
    letterSpacing: 1,
    lineHeight: 1,
    space: false,
    maxLength: 0,
  });
  console.log(pc.dim(`  Setup Wizard v${WIZARD_VERSION}`));
  console.log();
}
