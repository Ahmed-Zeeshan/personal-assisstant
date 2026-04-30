import { cpSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, '..');
const src = join(repoRoot, 'web', 'dist');
const dst = join(repoRoot, 'src', 'voice_assistant', 'desktop', 'web_dist');

if (!existsSync(src)) {
  console.error(`copy-web-dist: source ${src} does not exist; run 'cd web && npm run build' first.`);
  process.exit(1);
}

if (existsSync(dst)) rmSync(dst, { recursive: true, force: true });
mkdirSync(dst, { recursive: true });
cpSync(src, dst, { recursive: true });
console.log(`copied ${src} → ${dst}`);
