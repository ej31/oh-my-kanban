import { createRequire } from 'node:module';
import pc from 'picocolors';

const _require = createRequire(import.meta.url);
const { version: WIZARD_VERSION } = _require('../../package.json') as { version: string };

// figlet으로 생성한 "oh-my-kanban" ASCII art
const ASCII_LOGO = `
  ___  _   _       __  __  _  _     _  __              _
 / _ \\| |_| |_    |  \\/  || || |   | |/ /__ _ _ _  __| |__  __ _ _ _
| (_) | ' \\  _|   | |\\/| || \\/ |   | ' </ _\` | ' \\| _  / _\` | ' \\
 \\___/|_||_\\__|   |_|  |_| \\__/ _ |_|\\_\\__,_|_||_|___|\\__,_|_||_|
                         |___|
`;

export function printLogo(): void {
  console.log(pc.cyan(ASCII_LOGO));
  console.log(pc.bold(pc.white(`  Setup Wizard v${WIZARD_VERSION}`)));
  console.log();
}
