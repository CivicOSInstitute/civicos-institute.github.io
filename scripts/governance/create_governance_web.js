#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const GOV_CFG = path.join(__dirname, 'governance_config.json');
const WEB_CFG = path.join(__dirname, 'governance_web_config.json');
const OUT = path.join(ROOT, 'generated', 'governance', 'web');
const DOCX_DIR = path.join(ROOT, 'generated', 'governance', 'docx');
const PDF_DIR = path.join(ROOT, 'generated', 'governance', 'pdf');
const SUITE_ZIP = path.join(ROOT, 'generated', 'governance', 'CivicOS_Governance_Suite.zip');
const LOG_PATH = path.join(ROOT, 'generated', 'governance', 'generation_log.jsonl');

const EXPECTED_FILES = [
  'index.html', 'articles.html', 'bylaws.html', 'conflict-of-interest.html',
  'delegation-authority.html', 'document-retention.html', 'ip-licensing.html', 'data-privacy.html',
  'board-member-agreement.html', 'whistleblower.html', 'compensation-review.html', 'downloads.html'
];

const PAGE_TO_FILE = {
  index: 'index.html', articles: 'articles.html', bylaws: 'bylaws.html',
  'conflict-of-interest': 'conflict-of-interest.html', 'delegation-authority': 'delegation-authority.html',
  'document-retention': 'document-retention.html', 'ip-licensing': 'ip-licensing.html',
  'data-privacy': 'data-privacy.html', 'board-member-agreement': 'board-member-agreement.html',
  whistleblower: 'whistleblower.html', 'compensation-review': 'compensation-review.html', downloads: 'downloads.html',
};

const SHORT_BY_ID = {
  AOI: 'Articles_of_Incorporation', '01': 'Bylaws', '02': 'Conflict_of_Interest_Policy', '03': 'Delegation_of_Authority_Matrix',
  '04': 'Document_Retention_Records_Policy', '05': 'Intellectual_Property_Licensing_Policy', '06': 'Data_Privacy_Security_Policy',
  '07': 'Board_Member_Agreement', '08': 'Whistleblower_Policy', '09': 'Compensation_Review_Policy',
};

function usage() {
  console.log('Usage:');
  console.log('  node scripts/governance/create_governance_web.js --all');
  console.log('  node scripts/governance/create_governance_web.js --page <slug>');
}

const esc = (s = '') => String(s).replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));

function mdToHtml(md = '') {
  const lines = md.split(/\r?\n/); const out = []; let inList = false;
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) { if (inList) { out.push('</ul>'); inList = false; } continue; }
    if (/^###\s+/.test(line)) { if (inList) { out.push('</ul>'); inList = false; } out.push(`<h3>${esc(line.replace(/^###\s+/, ''))}</h3>`); continue; }
    if (/^##\s+/.test(line)) { if (inList) { out.push('</ul>'); inList = false; } out.push(`<h2>${esc(line.replace(/^##\s+/, ''))}</h2>`); continue; }
    if (/^#\s+/.test(line)) { if (inList) { out.push('</ul>'); inList = false; } out.push(`<h1>${esc(line.replace(/^#\s+/, ''))}</h1>`); continue; }
    if (/^[-*]\s+/.test(line)) { if (!inList) { out.push('<ul>'); inList = true; } out.push(`<li>${esc(line.replace(/^[-*]\s+/, ''))}</li>`); continue; }
    out.push(`<p>${esc(line)}</p>`);
  }
  if (inList) out.push('</ul>');
  return out.join('\n');
}

function readJsonStrict(p) {
  if (!fs.existsSync(p)) throw new Error(`Missing config: ${p}`);
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { throw new Error(`Malformed JSON in ${p}: ${e.message}`); }
}

function ensure() {
  fs.mkdirSync(OUT, { recursive: true });
  if (!fs.existsSync(LOG_PATH)) fs.writeFileSync(LOG_PATH, '');
}

function statusClass(status = 'DRAFT') {
  const s = String(status).toUpperCase();
  if (s === 'ADOPTED') return 'adopted';
  if (s.includes('REVIEW')) return 'review';
  return 'draft';
}

function styleBlock() {
  return `<style>
:root{--navy:#1B2B4B;--gold:#B8963E;--lg:#F2F4F7;--border:#D0D5DD;--white:#FFFFFF;--td:#111111;--tb:#333333;--muted:#777777}
*{box-sizing:border-box} body{margin:0;font-family:Georgia,serif;color:var(--tb);background:var(--lg)}
a{color:var(--navy)}
.top{background:var(--navy);color:#fff;padding:14px 18px;position:sticky;top:0;z-index:10}
.brand{font-family:Arial,sans-serif;font-weight:700}
.nav-wrap{display:flex;align-items:center;justify-content:space-between}
.nav-links{display:flex;gap:14px}.nav-links a{font-family:Arial,sans-serif;color:#fff;text-decoration:none;font-size:14px}
.hamb{display:none;background:none;border:1px solid rgba(255,255,255,.4);color:#fff;padding:6px 10px;border-radius:6px}
main{max-width:1120px;margin:22px auto;padding:0 16px}
.card{background:#fff;border:1px solid var(--border);border-radius:8px;padding:16px;border-left:4px solid var(--gold);transition:box-shadow .2s ease}
.card:hover{box-shadow:0 4px 12px rgba(0,0,0,.1)}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.badge{display:inline-block;padding:4px 8px;border-radius:20px;font-family:Arial,sans-serif;font-size:12px;border:1px solid}
.badge.draft{background:#FFF3CD;color:#856404;border-color:#FFEAA7}
.badge.adopted{background:#D1E7DD;color:#0A3622;border-color:#A3CFBB}
.badge.review{background:#CFF4FC;color:#055160;border-color:#9EEAF9}
.kf{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.kf span{font-family:Arial,sans-serif;font-size:12px;background:var(--lg);border:1px solid var(--border);padding:4px 8px;border-radius:16px}
.layer{margin-top:14px}
.fulltext{background:var(--lg);border-left:3px solid var(--border);padding:24px;overflow:hidden;max-height:0;transition:max-height .35s ease}
.fulltext.open{max-height:2200px}
.tog{font-family:Arial,sans-serif;background:#fff;border:1px solid var(--border);padding:8px 12px;border-radius:6px;cursor:pointer}
.dl{display:inline-block;background:var(--navy);color:#fff !important;text-decoration:none;padding:10px 14px;border-radius:6px;font-family:Arial,sans-serif}
.dl:hover{background:var(--gold);color:#fff !important}
.small{font-size:12px;color:var(--muted);font-family:Arial,sans-serif}
footer{margin:30px 0;color:var(--muted);font-family:Arial,sans-serif;font-size:12px}
@media (max-width:768px){.grid{grid-template-columns:1fr}.hamb{display:inline-block}.nav-links{display:none;flex-direction:column;background:var(--navy);position:absolute;left:0;right:0;top:54px;padding:10px 18px}.nav-links.open{display:flex}.dl{display:block;width:100%;text-align:center}}
</style>`;
}

const scriptBlock = () => `<script>function toggleMenu(){document.getElementById('navLinks').classList.toggle('open')} function toggleFull(id,btn){const e=document.getElementById(id);const open=e.classList.toggle('open');btn.setAttribute('aria-expanded',open?'true':'false');btn.textContent=open?'Hide full text':'Show full text';}</script>`;
const nav = () => `<header class="top"><div class="nav-wrap"><div class="brand">CivicOS Governance</div><button class="hamb" aria-label="Toggle navigation" onclick="toggleMenu()">☰</button><nav id="navLinks" class="nav-links" aria-label="Governance navigation"><a href="index.html">Index</a><a href="downloads.html">Downloads</a></nav></div></header>`;
const wrap = (title, body) => `<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>${esc(title)}</title>${styleBlock()}</head><body>${nav()}<main>${body}</main>${scriptBlock()}<footer><main>Generated by create_governance_web.js</main></footer></body></html>`;

function fileInfo(docId, version) {
  const short = SHORT_BY_ID[docId];
  const docxName = `${docId}_${short}_CivicOS_Institute_v${version}.docx`;
  const pdfName = `${docId}_${short}_CivicOS_Institute_v${version}.pdf`;
  const docx = path.join(DOCX_DIR, docxName);
  const pdf = path.join(PDF_DIR, pdfName);
  return {
    docxName, docxExists: fs.existsSync(docx), docxSize: fs.existsSync(docx) ? fs.statSync(docx).size : 0,
    pdfName, pdfExists: fs.existsSync(pdf), pdfSize: fs.existsSync(pdf) ? fs.statSync(pdf).size : 0,
  };
}

function layer3Downloads(info) {
  const primary = info.pdfExists
    ? `<a class="dl" href="downloads/pdf/${esc(info.pdfName)}" download>Download PDF</a>`
    : '';
  const secondary = `<a class="dl" href="downloads/docx/${esc(info.docxName)}" download>${info.pdfExists ? 'Download DOCX' : 'Download DOCX'}</a>`;
  if (info.pdfExists) return `${primary} <span class="small">&nbsp;</span> ${secondary}`;
  return secondary;
}

function buildDocPage(d, govCfg) {
  const dc = govCfg.documents[d.id] || { version: '1.0', status: 'DRAFT', adopted: null, last_reviewed: null };
  const mdPath = path.join(ROOT, d.source_markdown);
  const fullHtml = mdToHtml(fs.existsSync(mdPath) ? fs.readFileSync(mdPath, 'utf8') : 'Full text source not found.');
  const info = fileInfo(d.id, dc.version || '1.0');

  const body = `<article>
  <h1>${esc(d.title)}</h1>
  <section class="layer card" aria-label="At a glance"><h2>Layer 1 — At a glance</h2><span class="badge ${statusClass(dc.status)}">${esc(dc.status || 'DRAFT')}</span><p>${esc(d.summary)}</p><div class="kf">${d.key_facts.map(k=>`<span>${esc(k)}</span>`).join('')}</div><div class="small">Last reviewed: ${esc(dc.last_reviewed || 'Not yet reviewed')}</div></section>
  <section class="layer card" aria-label="Full text"><h2>Layer 2 — Full text</h2><button class="tog" aria-label="Toggle full text" aria-expanded="true" aria-controls="full-${d.id}" onclick="toggleFull('full-${d.id}',this)">Hide full text</button><div id="full-${d.id}" class="fulltext open">${fullHtml}</div></section>
  <section class="layer card" aria-label="Download"><h2>Layer 3 — Download</h2>${layer3Downloads(info)}<div class="small">Version ${esc(dc.version || '1.0')} · Status: ${esc(dc.status || 'DRAFT')} · ${esc(dc.adopted || 'Pending adoption')}</div></section>
</article>`;
  return wrap(`${d.title} | CivicOS Governance`, body);
}

function buildIndex(webCfg, govCfg) {
  const cards = webCfg.documents.map(d => {
    const dc = govCfg.documents[d.id] || { status: 'DRAFT', last_reviewed: null, version: '1.0', adopted: null };
    const mdPath = path.join(ROOT, d.source_markdown);
    const fullHtml = mdToHtml(fs.existsSync(mdPath) ? fs.readFileSync(mdPath, 'utf8') : 'Full text source not found.');
    const info = fileInfo(d.id, dc.version || '1.0');
    return `<article class="card"><h2 style="margin-top:0"><a href="${esc(d.page)}">${esc(d.title)}</a></h2><span class="badge ${statusClass(dc.status)}">${esc(dc.status || 'DRAFT')}</span><div class="small" style="margin-top:6px">Layer 1 — At a glance</div><p>${esc(d.summary)}</p><div class="kf">${d.key_facts.map(k => `<span>${esc(k)}</span>`).join('')}</div><div class="small">Last reviewed: ${esc(dc.last_reviewed || 'Not yet reviewed')}</div><div class="layer"><div class="small">Layer 2 — Full text</div><button class="tog" aria-label="Toggle full text" aria-expanded="false" aria-controls="full-${d.id}" onclick="toggleFull('full-${d.id}',this)">Show full text</button><div id="full-${d.id}" class="fulltext">${fullHtml}</div></div><div class="layer"><div class="small">Layer 3 — Download</div>${layer3Downloads(info)}</div></article>`;
  }).join('');

  const body = `<section class="card" style="margin-bottom:14px"><h1>Governance</h1></section><section role="note" aria-label="Governance documents provisional status notice" style="background:#FFF3CD;border-left:4px solid #B8963E;border-radius:6px;padding:20px 24px;color:#856404;font-family:Arial,sans-serif;font-size:15px;line-height:1.6;margin-bottom:32px;">⚖ These governance documents are published in draft form as part of our founding transparency commitment. They reflect our current operating standards and are pending formal adoption at our first board meeting. We believe you should be able to see how we govern ourselves before, during, and after that process — not just after.</section><section class="grid">${cards}</section><section class="card" style="margin-top:14px"><h2>Transparency Statement</h2><p>${esc(webCfg.transparency_statement)}</p></section><aside class="card" style="margin-top:14px" aria-label="Board composition summary"><h2>Board Composition Summary</h2><p><strong>${govCfg.board.min_directors}–${govCfg.board.max_directors}</strong> directors · ${govCfg.board.term_years}-year terms · minimum ${govCfg.board.meetings_per_year_minimum} meetings/year · quorum: ${esc(govCfg.board.quorum)}</p></aside><section class="card" style="margin-top:14px"><h2>Downloads</h2><a class="dl" href="downloads.html">Open downloads center</a></section>`;
  return wrap('Governance | CivicOS Institute', body);
}

function buildDownloads(webCfg, govCfg) {
  const rows = webCfg.documents.map(d => {
    const dc = govCfg.documents[d.id] || { version: '1.0', status: 'DRAFT', adopted: null, last_reviewed: null };
    const info = fileInfo(d.id, dc.version || '1.0');
    const size = info.pdfExists ? info.pdfSize : info.docxSize;
    const pdfBtn = info.pdfExists ? `<a class="dl" href="downloads/pdf/${esc(info.pdfName)}" download>PDF ⬇</a>` : '';
    const docxBtn = `<a class="dl" href="downloads/docx/${esc(info.docxName)}" download>DOCX ⬇</a>`;
    return `<tr><td>${esc(d.title)}</td><td>${esc(dc.version || '1.0')}</td><td><span class="badge ${statusClass(dc.status)}">${esc(dc.status || 'DRAFT')}</span></td><td>${pdfBtn} ${docxBtn}</td><td>${size}</td></tr>`;
  }).join('');

  const changelog = webCfg.documents.map(d => {
    const dc = govCfg.documents[d.id] || { version: '1.0', status: 'DRAFT', last_reviewed: null };
    return `<tr><td>${esc(d.id)}</td><td>${esc(dc.version || '1.0')}</td><td>${esc(dc.status || 'DRAFT')}</td><td>${esc(dc.last_reviewed || 'N/A')}</td></tr>`;
  }).join('');

  const body = `<article>
    <h1>Governance Downloads</h1>
    <section class="card"><h2>Layer 1 — At a glance</h2><p>Download every governance document with status, version, and file metadata.</p></section>
    <section class="card layer"><h2>Layer 2 — Full text</h2><button class="tog" aria-label="Toggle full text" aria-expanded="false" aria-controls="full-downloads" onclick="toggleFull('full-downloads',this)">Show full text</button><div id="full-downloads" class="fulltext"><p>This page includes complete download metadata and a changelog table for review and audit traceability.</p></div></section>
    <section class="card layer"><h2>Layer 3 — Download</h2><a class="dl" href="downloads/CivicOS_Governance_Suite.zip" download>Download Full Suite ZIP</a></section>
    <section class="card layer"><h2>Documents</h2><div style="overflow:auto"><table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif"><thead><tr><th align="left">Document</th><th align="left">Version</th><th align="left">Status</th><th align="left">Downloads</th><th align="left">Size</th></tr></thead><tbody>${rows}</tbody></table></div></section>
    <section class="card layer"><h2>Changelog: Version History</h2><div style="overflow:auto"><table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif"><thead><tr><th align="left">ID</th><th align="left">Version</th><th align="left">Status</th><th align="left">Last Reviewed</th></tr></thead><tbody>${changelog}</tbody></table></div></section>
  </article>`;
  return wrap('Governance Downloads | CivicOS Institute', body);
}

function writePage(file, html) { fs.writeFileSync(path.join(OUT, file), html); }

function checkWellFormed(html, file) {
  const voidTags = new Set(['meta', 'link', 'br', 'hr', 'img', 'input']);
  const re = /<\/?([a-zA-Z0-9]+)(\s[^>]*)?>/g;
  const stack = [];
  let m;
  while ((m = re.exec(html)) !== null) {
    const raw = m[0], tag = m[1].toLowerCase(), closing = raw.startsWith('</'), selfClose = raw.endsWith('/>') || voidTags.has(tag);
    if (closing) { const top = stack.pop(); if (top !== tag) throw new Error(`${file}: unclosed/mismatched tag near </${tag}>`); }
    else if (!selfClose) stack.push(tag);
  }
  if (stack.length) throw new Error(`${file}: unclosed tags remain (${stack.join(',')})`);
}

function runValidation(webCfg, govCfg, pagesGenerated) {
  const missing = EXPECTED_FILES.filter(f => !fs.existsSync(path.join(OUT, f)));
  if (missing.length) throw new Error(`Missing expected pages: ${missing.join(', ')}`);

  for (const f of EXPECTED_FILES) checkWellFormed(fs.readFileSync(path.join(OUT, f), 'utf8'), f);

  const broken_pdf_links = [];
  const broken_docx_links = [];
  for (const d of webCfg.documents) {
    const dc = govCfg.documents[d.id] || { version: '1.0', status: 'DRAFT' };
    const html = fs.readFileSync(path.join(OUT, d.page), 'utf8');

    if (!html.includes(`>${dc.status || 'DRAFT'}<`)) throw new Error(`${d.page}: status badge mismatch with governance_config.json`);
    for (const fact of d.key_facts) if (!html.includes(fact)) throw new Error(`${d.page}: key_facts mismatch for '${fact}'`);
    for (const l of ['Layer 1 — At a glance', 'Layer 2 — Full text', 'Layer 3 — Download']) if (!html.includes(l)) throw new Error(`${d.page}: missing ${l}`);

    const info = fileInfo(d.id, dc.version || '1.0');
    if (!info.docxExists) broken_docx_links.push(`downloads/docx/${info.docxName}`);
    if (!info.pdfExists) broken_pdf_links.push(`downloads/pdf/${info.pdfName}`);
  }

  if (!fs.existsSync(SUITE_ZIP)) broken_docx_links.push('downloads/CivicOS_Governance_Suite.zip');
  return { pages_generated: pagesGenerated.slice(), broken_pdf_links, broken_docx_links };
}

function appendLog(entry) { fs.appendFileSync(LOG_PATH, JSON.stringify(entry) + '\n'); }

function main() {
  const args = process.argv.slice(2);
  const modeAll = args.length === 1 && args[0] === '--all';
  const modePage = args.length === 2 && args[0] === '--page';
  if (!modeAll && !modePage) { usage(); process.exit(0); }

  ensure();
  let govCfg, webCfg;
  try { govCfg = readJsonStrict(GOV_CFG); webCfg = readJsonStrict(WEB_CFG); }
  catch (e) { console.error(`ESCALATION REQUIRED: ${e.message}. Notify NCerbone@civicos-institute.org`); process.exit(1); }

  const pagesGenerated = [];
  if (modeAll) {
    writePage('index.html', buildIndex(webCfg, govCfg)); pagesGenerated.push('index.html');
    for (const d of webCfg.documents) { writePage(d.page, buildDocPage(d, govCfg)); pagesGenerated.push(d.page); }
    writePage('downloads.html', buildDownloads(webCfg, govCfg)); pagesGenerated.push('downloads.html');
  } else {
    const target = PAGE_TO_FILE[args[1]];
    if (!target) { usage(); process.exit(0); }
    if (target === 'index.html') writePage(target, buildIndex(webCfg, govCfg));
    else if (target === 'downloads.html') writePage(target, buildDownloads(webCfg, govCfg));
    else {
      const d = webCfg.documents.find(x => x.page === target);
      if (!d) { usage(); process.exit(0); }
      writePage(target, buildDocPage(d, govCfg));
    }
    pagesGenerated.push(target);
  }

  let status = 'ok';
  let broken_pdf_links = [];
  let broken_docx_links = [];
  try {
    const v = runValidation(webCfg, govCfg, pagesGenerated);
    broken_pdf_links = v.broken_pdf_links;
    broken_docx_links = v.broken_docx_links;
    if (broken_pdf_links.length || broken_docx_links.length) status = 'warning';
  } catch (e) {
    status = 'error';
    appendLog({ timestamp: new Date().toISOString(), trigger: modeAll ? '--all' : `--page ${args[1]}`, pages_generated: pagesGenerated, broken_pdf_links, broken_docx_links, operator: 'Burt', status, error: e.message });
    console.error(`ESCALATION REQUIRED: ${e.message}. Notify NCerbone@civicos-institute.org`);
    process.exit(1);
  }

  appendLog({ timestamp: new Date().toISOString(), trigger: modeAll ? '--all' : `--page ${args[1]}`, pages_generated: pagesGenerated, broken_pdf_links, broken_docx_links, operator: 'Burt', status });

  console.log(`Generated ${pagesGenerated.length} page(s) to ${OUT}`);
  pagesGenerated.forEach(p => console.log(`- ${p}`));
  if (broken_pdf_links.length) {
    console.log('Broken PDF links (warnings):');
    broken_pdf_links.forEach(l => console.log(`- ${l}`));
  }
  if (broken_docx_links.length) {
    console.log('Broken DOCX/ZIP links (warnings):');
    broken_docx_links.forEach(l => console.log(`- ${l}`));
  }
  console.log(`Status: ${status}`);
}

main();
