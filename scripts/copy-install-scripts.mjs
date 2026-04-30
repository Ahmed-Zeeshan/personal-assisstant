import { copyFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, '..');
const dest = join(repoRoot, 'website', 'public', 'install');

mkdirSync(dest, { recursive: true });
copyFileSync(join(here, 'install.sh'),  join(dest, 'install.sh'));
copyFileSync(join(here, 'install.ps1'), join(dest, 'install.ps1'));
console.log(`copied install scripts → ${dest}`);
