#!/usr/bin/env node
const { execFileSync } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');

const ROOT = '/Users/AI-OPS/.openclaw/workspace';
const outDir = path.join(ROOT, 'generated', 'board');
const dateArg = process.argv[2];
const date = dateArg || new Date().toISOString().slice(0, 10);

const mdPath = path.join(outDir, `board_brief_${date}.md`);
const docxPath = path.join(outDir, `board_brief_${date}.docx`);

if (!fs.existsSync(mdPath)) {
  console.error(`Missing markdown source: ${mdPath}`);
  process.exit(1);
}

execFileSync('pandoc', [mdPath, '-o', docxPath, '--from', 'markdown', '--to', 'docx'], { stdio: 'inherit' });
console.log(docxPath);
