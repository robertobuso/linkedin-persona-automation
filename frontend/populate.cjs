#!/usr/bin/env node
/**
 * Parse implementation.md and write each fenced code block
 * to the file path shown in its preceding heading.
 *
 * Example heading in the markdown:
 * ### `src/stores/authStore.ts` - Authentication Store
 */
const fs   = require('fs');
const path = require('path');

const md = fs.readFileSync('ui-components.md', 'utf8');

// ── match:  ### `path/to/file` … ```ts\n(code)…```
const re = /###\s+`([^`]+)`[^]*?```[\w-]*\n([\s\S]*?)```/g;

let m, created = 0;
while ((m = re.exec(md)) !== null) {
  const filePath = m[1];
  const code     = m[2].replace(/\s*$/, '') + '\n';

  const abs = path.resolve(filePath);
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, code);

  console.log('✅  wrote', filePath);
  created++;
}

console.log(`\nFinished. ${created} files populated.`);
