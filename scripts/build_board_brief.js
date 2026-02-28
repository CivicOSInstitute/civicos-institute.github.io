#!/usr/bin/env node
const { execFileSync } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');

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

function fmtDate(isoDate) {
  const d = new Date(`${isoDate}T00:00:00`);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
}

function escXml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

function injectHeader(docxFile, dateLabel) {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'board-docx-'));
  execFileSync('unzip', ['-q', '-o', docxFile, '-d', tmpDir], { stdio: 'inherit' });

  const xmlPath = path.join(tmpDir, 'word', 'document.xml');
  let xml = fs.readFileSync(xmlPath, 'utf8');

  const CENTER_TAB_DXA = 4680; // exactly half of content width for Letter with 1-inch margins
  const RIGHT_TAB_DXA = 9360;  // right edge of content width (TabStopPosition.MAX equivalent)
  const org = 'CIVICOS INSTITUTE';
  const title = 'Board Intelligence Brief';

  const headerPara =
    `<w:p>` +
      `<w:pPr>` +
        `<w:spacing w:before="80" w:after="80"/>` +
        `<w:tabs>` +
          `<w:tab w:val="center" w:pos="${CENTER_TAB_DXA}"/>` +
          `<w:tab w:val="right" w:pos="${RIGHT_TAB_DXA}"/>` +
        `</w:tabs>` +
        `<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="4" w:color="auto"/></w:pBdr>` +
      `</w:pPr>` +
      `<w:r><w:rPr><w:b/></w:rPr><w:t>${escXml(org)}</w:t></w:r>` +
      `<w:r><w:tab/></w:r>` +
      `<w:r><w:rPr><w:b/></w:rPr><w:t>${escXml(title)}</w:t></w:r>` +
      `<w:r><w:tab/></w:r>` +
      `<w:r><w:rPr><w:b/></w:rPr><w:t>${escXml(dateLabel)}</w:t></w:r>` +
    `</w:p>` +
    `<w:p><w:pPr><w:spacing w:before="0" w:after="40"/></w:pPr></w:p>`;

  xml = xml.replace('<w:body>', `<w:body>${headerPara}`);
  fs.writeFileSync(xmlPath, xml, 'utf8');

  const cwd = process.cwd();
  process.chdir(tmpDir);
  execFileSync('zip', ['-qr', docxFile, '.'], { stdio: 'inherit' });
  process.chdir(cwd);

  fs.rmSync(tmpDir, { recursive: true, force: true });
}

execFileSync('pandoc', [mdPath, '-o', docxPath, '--from', 'markdown', '--to', 'docx'], { stdio: 'inherit' });
injectHeader(docxPath, fmtDate(date));
console.log(docxPath);
