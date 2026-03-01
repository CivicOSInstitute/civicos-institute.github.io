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

function applyConfigTokens(md = '', govCfg = {}) {
  const orgName = govCfg?.org?.name || 'CivicOS Institute';
  const state = govCfg?.org?.state || 'Florida';
  const tokenMap = {
    '[CIVICOS INSTITUTE]': orgName,
    '[STATE OF INCORPORATION]': state,
    '[THREE (3)]': '3',
    '[TWO (2)]': '2',
    '[ONE (1)]': '1',
    '[FOUR (4)]': '4',
    '[FIFTEEN (15)]': '15',
    '[SEVEN (7)]': '7',
    '[NINE (9)]': '9'
  };
  let out = String(md);
  for (const [k, v] of Object.entries(tokenMap)) out = out.split(k).join(String(v));
  out = out.replace(/\[([A-Z\s]+)\s*\((\d+)\)\]/g, '$2');
  out = out.replace(/\[([^\]]+)\]/g, '$1');
  return out;
}

function formatInline(text = '') {
  let t = esc(text);
  t = t.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  t = t.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  return t;
}

function mdToHtml(md = '') {
  const lines = md.split(/\r?\n/); const out = []; let inList = false;
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) { if (inList) { out.push('</ul>'); inList = false; } continue; }
    if (/^###\s+/.test(line)) { if (inList) { out.push('</ul>'); inList = false; } out.push(`<h3>${formatInline(line.replace(/^###\s+/, ''))}</h3>`); continue; }
    if (/^##\s+/.test(line)) { if (inList) { out.push('</ul>'); inList = false; } out.push(`<h2>${formatInline(line.replace(/^##\s+/, ''))}</h2>`); continue; }
    if (/^#\s+/.test(line)) { if (inList) { out.push('</ul>'); inList = false; } out.push(`<h1>${formatInline(line.replace(/^#\s+/, ''))}</h1>`); continue; }
    if (/^[-*]\s+/.test(line)) { if (!inList) { out.push('<ul>'); inList = true; } out.push(`<li>${formatInline(line.replace(/^[-*]\s+/, ''))}</li>`); continue; }
    out.push(`<p>${formatInline(line)}</p>`);
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
:root{--bg:#0A0F1E;--navbg:rgba(10,15,30,.95);--text:#F4F1EB;--gold:#D4A843;--muted:#8B95A5;--divider:rgba(244,241,235,.12)}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font-family:"IBM Plex Sans",sans-serif;max-width:100%;overflow-x:hidden}
a{color:var(--gold);text-decoration:none}
a:hover{text-decoration:underline}
.site-nav{position:sticky;top:0;z-index:50;height:56px;background:var(--navbg);backdrop-filter:blur(8px);border-bottom:1px solid rgba(244,241,235,.12)}
.nav-wrap{max-width:1200px;height:100%;margin:0 auto;padding:0 16px;display:flex;align-items:center;gap:14px}
.wordmark{font-family:"IBM Plex Mono",monospace;font-size:13px;letter-spacing:1.82px;text-transform:uppercase;color:var(--text);white-space:nowrap}
.nav-links{display:flex;align-items:center;gap:14px;flex:1;justify-content:center}
.nav-links a{font-family:"IBM Plex Mono",monospace;font-size:13px;letter-spacing:1.82px;text-transform:uppercase;color:var(--gold);padding-bottom:3px;border-bottom:1px solid transparent}
.nav-links a.active{border-bottom-color:var(--gold)}
.nav-cta{display:flex;align-items:center;gap:8px}
.btn-cta{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:1.2px;text-transform:uppercase;padding:8px 10px;border:1px solid var(--gold);color:var(--gold);border-radius:2px}
.btn-cta.fill{background:var(--gold);color:var(--bg)}
.hamb{display:none;background:none;border:1px solid rgba(244,241,235,.45);color:var(--text);padding:6px 10px;border-radius:2px}
.hero{max-width:1200px;margin:0 auto;padding:80px 16px 60px;border-bottom:1px solid rgba(212,168,67,.3)}
.eyebrow,.small,.layer-label{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:var(--muted)}
.hero h1{margin:12px 0 14px;font-family:"Playfair Display",Georgia,serif;font-size:clamp(44px,8vw,80px);line-height:1.06;color:var(--text)}
.hero h1 em{color:var(--gold);font-style:italic}
.hero p{max-width:640px;color:var(--muted);font-size:18px;line-height:1.6;margin:0}
.hero .status-badge{margin-top:12px}
main{max-width:1200px;margin:0 auto;padding:28px 16px 40px}
.card{background:transparent;border:1px solid rgba(244,241,235,.2);border-left:3px solid var(--gold);border-radius:2px;padding:28px 28px 24px;transition:all .2s ease}
.card:hover{border-left-color:#f0c86b;background:rgba(212,168,67,.04)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr));gap:14px}
.card h2,.card h3{font-family:"Playfair Display",Georgia,serif;color:var(--text);font-size:22px}
.card h2 a:hover{color:var(--gold);text-decoration:none}
.card p,.card li{font-family:"IBM Plex Sans",sans-serif;color:var(--muted);line-height:1.65;font-size:15px}
.badge{display:inline-block;padding:4px 10px;border-radius:2px;font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:1.2px;text-transform:uppercase}
.badge.draft{background:rgba(212,168,67,.12);color:var(--gold);border:1px solid rgba(212,168,67,.3)}
.badge.adopted{background:rgba(34,197,94,.12);color:#86EFAC;border:1px solid rgba(34,197,94,.3)}
.badge.review{background:rgba(59,130,246,.12);color:#93C5FD;border:1px solid rgba(59,130,246,.3)}
.kf{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.kf span{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted);background:rgba(244,241,235,.06);border:1px solid rgba(244,241,235,.15);padding:4px 10px;border-radius:3px}
.layer{margin-top:14px}
.fulltext{margin-top:10px;background:rgba(244,241,235,.03);border-left:2px solid rgba(212,168,67,.3);padding:20px;overflow:hidden;max-height:0;transition:max-height .35s ease}
.fulltext.open{max-height:3200px}
.tog{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:1.2px;text-transform:uppercase;background:transparent;border:1px solid rgba(212,168,67,.4);color:var(--gold);padding:8px 12px;border-radius:2px;cursor:pointer}
.dl{display:inline-block;padding:10px 14px;border-radius:2px;font-family:"IBM Plex Sans",sans-serif;font-size:13px;font-weight:700}
.dl.pdf{background:var(--gold);color:var(--bg);border:1px solid var(--gold)}
.dl.pdf:hover{background:var(--text);text-decoration:none}
.dl.docx{background:transparent;color:var(--text);border:1px solid rgba(244,241,235,.3)}
.dl.docx:hover{border-color:var(--gold);color:var(--gold);text-decoration:none}
.dl.zip{display:block;width:100%;text-align:center;padding:16px;background:var(--gold);color:var(--bg);border:1px solid var(--gold)}
.dl.zip:hover{background:var(--text);text-decoration:none}
.rule{height:1px;background:var(--divider);margin:16px 0}
.table-wrap{overflow:auto;border:1px solid rgba(244,241,235,.1)}
table{width:100%;border-collapse:collapse}
table thead tr{background:rgba(212,168,67,.1)}
table th{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:var(--gold)}
table th,table td{border-bottom:1px solid var(--divider);padding:10px}
table td{color:var(--text);font-family:"IBM Plex Sans",sans-serif}
table tbody tr:nth-child(odd){background:rgba(244,241,235,.02)}
.provisional{display:block;width:100%;max-width:100%;background:rgba(212,168,67,.08);border-left:4px solid var(--gold);border:1px solid rgba(212,168,67,.2);border-radius:2px;padding:20px 24px;color:var(--gold);font-size:14px}
.board-panel{background:rgba(244,241,235,.04);border:1px solid rgba(244,241,235,.1);border-top:2px solid var(--gold)}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:12px}
.stat .value{font-family:"Playfair Display",Georgia,serif;font-size:36px;font-weight:700;color:var(--text)}
.stat .label{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:var(--muted)}
footer{border-top:1px solid var(--divider);padding:18px 16px;color:var(--muted);font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:1px;text-transform:uppercase}
@media (max-width:980px){.nav-links{gap:10px}.nav-links a{font-size:12px;letter-spacing:1.2px}.btn-cta{font-size:11px;padding:7px 8px}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:600px){.grid{grid-template-columns:1fr !important}}
@media (max-width:768px){
  .documents-grid,.cards-grid,[class*="grid"]{grid-template-columns:1fr !important}
  .board-stats,.stats-grid,.stat-row,.stats{grid-template-columns:1fr 1fr;gap:16px}
  .pills,.facts,[class*="pill"],[class*="tag"],.kf{flex-wrap:wrap}
  .card,[class*="card"]{padding:20px 16px}
  .provisional,.provisional-banner,.transparency-notice,[class*="banner"],[class*="notice"]{width:100%;box-sizing:border-box;margin-left:0;margin-right:0}
  .hamb{display:inline-block}
  .nav-links{display:none;position:absolute;left:0;right:0;top:56px;background:var(--navbg);padding:12px 16px;flex-direction:column;align-items:flex-start}
  .nav-links.open{display:flex}
  .nav-cta{display:none}
}
</style>`;
}

const scriptBlock = () => `<script>function toggleMenu(){document.getElementById('navLinks').classList.toggle('open')} function closeMenu(){const n=document.getElementById('navLinks');if(n)n.classList.remove('open')} function toggleFull(id,btn){const e=document.getElementById(id);const open=e.classList.toggle('open');btn.setAttribute('aria-expanded',open?'true':'false');btn.textContent=open?'Hide full text':'Show full text';} function enforceMobileGrid(){const vw=Math.min(window.innerWidth||9999,document.documentElement.clientWidth||9999,document.body.clientWidth||9999);document.querySelectorAll('.grid').forEach(g=>{if(vw<=768){g.style.gridTemplateColumns='1fr';g.style.width='100%';g.style.maxWidth='100%';}else{g.style.gridTemplateColumns='';g.style.width='';g.style.maxWidth='';}});} document.addEventListener('click',function(ev){const nav=document.querySelector('.site-nav');const links=document.getElementById('navLinks');if(!nav||!links) return; if(window.innerWidth<=768 && links.classList.contains('open') && !nav.contains(ev.target)){closeMenu();}}); document.addEventListener('DOMContentLoaded',function(){const links=document.querySelectorAll('#navLinks a');links.forEach(a=>a.addEventListener('click',()=>{if(window.innerWidth<=768) closeMenu();}));enforceMobileGrid();}); window.addEventListener('resize',enforceMobileGrid);</script>`;
const nav = () => `<header class="site-nav"><div class="nav-wrap"><a class="wordmark" href="/">CIVICOS INSTITUTE</a><button class="hamb" aria-label="Toggle navigation" onclick="toggleMenu()">☰</button><nav id="navLinks" class="nav-links" aria-label="Site navigation"><a href="/">Home</a><a href="/about/">About</a><a href="/publications/">Publications</a><a href="/letters/">Letters</a><a href="/ebook/">Ebook</a><a href="/open-source/">Open Source</a><a href="/governance/" class="active">Governance</a><a href="/contact/">Contact</a></nav><div class="nav-cta"><a class="btn-cta" href="/donate/">Donate ♥</a><a class="btn-cta" href="/open-source/">Free AI Kit ↓</a><a class="btn-cta fill" href="/ebook/">Get the Ebook →</a></div></div></header>`;
const wrap = (title, body) => `<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>${esc(title)}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,800;1,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">${styleBlock()}</head><body>${nav()}${body}${scriptBlock()}<footer><div style="max-width:1200px;margin:0 auto">CivicOS Institute · Governance</div></footer></body></html>`;

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
    ? `<a class="dl pdf" href="downloads/pdf/${esc(info.pdfName)}" download>Download PDF</a>`
    : '';
  const secondary = `<a class="dl docx" href="downloads/docx/${esc(info.docxName)}" download>Download DOCX</a>`;
  if (info.pdfExists) return `${primary} <span class="small">&nbsp;</span> ${secondary}`;
  return secondary;
}

function buildDocPage(d, govCfg) {
  const dc = govCfg.documents[d.id] || { version: '1.0', status: 'DRAFT', adopted: null, last_reviewed: null };
  const mdPath = path.join(ROOT, d.source_markdown);
  const sourceMd = fs.existsSync(mdPath) ? fs.readFileSync(mdPath, 'utf8') : 'Full text source not found.';
  const fullHtml = mdToHtml(applyConfigTokens(sourceMd, govCfg));
  const info = fileInfo(d.id, dc.version || '1.0');

  const body = `<section class="hero"><div class="eyebrow">— GOVERNANCE DOCUMENT · ${esc(d.id)}</div><h1>${esc(d.title)}</h1><p>${esc(d.summary)}</p><div class="status-badge"><span class="badge ${statusClass(dc.status)}">${esc(dc.status || 'DRAFT')}</span></div></section><main><article>
  <section class="layer card" aria-label="At a glance"><h2>Layer 1 — At a glance</h2><span class="badge ${statusClass(dc.status)}">${esc(dc.status || 'DRAFT')}</span><p>${esc(d.summary)}</p><div class="kf">${d.key_facts.map(k=>`<span>${esc(k)}</span>`).join('')}</div><div class="small">Last reviewed: ${esc(dc.last_reviewed || 'Not yet reviewed')}</div></section>
  <section class="layer card" aria-label="Full text"><h2>Layer 2 — Full text</h2><button class="tog" aria-label="Toggle full text" aria-expanded="true" aria-controls="full-${d.id}" onclick="toggleFull('full-${d.id}',this)">Hide full text</button><div id="full-${d.id}" class="fulltext open">${fullHtml}</div></section>
  <section class="layer card" aria-label="Download"><h2>Layer 3 — Download</h2>${layer3Downloads(info)}<div class="small">Version ${esc(dc.version || '1.0')} · Status: ${esc(dc.status || 'DRAFT')} · ${esc(dc.adopted || 'Pending adoption')}</div></section>
</article></main>`;
  return wrap(`${d.title} | CivicOS Governance`, body);
}

function buildIndex(webCfg, govCfg) {
  const cards = webCfg.documents.map(d => {
    const dc = govCfg.documents[d.id] || { status: 'DRAFT', last_reviewed: null, version: '1.0', adopted: null };
    const mdPath = path.join(ROOT, d.source_markdown);
    const sourceMd = fs.existsSync(mdPath) ? fs.readFileSync(mdPath, 'utf8') : 'Full text source not found.';
    const fullHtml = mdToHtml(applyConfigTokens(sourceMd, govCfg));
    const info = fileInfo(d.id, dc.version || '1.0');
    return `<article class="card"><h2 style="margin-top:0"><a href="${esc(d.page)}">${esc(d.title)}</a></h2><span class="badge ${statusClass(dc.status)}">${esc(dc.status || 'DRAFT')}</span><div class="small" style="margin-top:6px">Layer 1 — At a glance</div><p>${esc(d.summary)}</p><div class="kf">${d.key_facts.map(k => `<span>${esc(k)}</span>`).join('')}</div><div class="small">Last reviewed: ${esc(dc.last_reviewed || 'Not yet reviewed')}</div><div class="layer"><div class="small">Layer 2 — Full text</div><button class="tog" aria-label="Toggle full text" aria-expanded="false" aria-controls="full-${d.id}" onclick="toggleFull('full-${d.id}',this)">Show full text</button><div id="full-${d.id}" class="fulltext">${fullHtml}</div></div><div class="layer"><div class="small">Layer 3 — Download</div>${layer3Downloads(info)}</div></article>`;
  }).join('');

  const body = `<section class="hero"><div class="eyebrow">— GOVERNANCE & TRANSPARENCY</div><h1>How we <em>govern</em></h1><p>${esc(webCfg.transparency_statement)}</p></section><main><section class="provisional" role="note" aria-label="Governance documents provisional status notice" style="margin-bottom:18px">⚖ These governance documents are published in draft form as part of our founding transparency commitment. They reflect our current operating standards and are pending formal adoption at our first board meeting. We believe you should be able to see how we govern ourselves before, during, and after that process — not just after.</section><section class="grid">${cards}</section><section class="card board-panel" style="margin-top:14px"><h2>Board Composition Summary</h2><div class="stats"><div class="stat"><div class="value">${govCfg.board.min_directors}</div><div class="label">Min directors</div></div><div class="stat"><div class="value">${govCfg.board.max_directors}</div><div class="label">Max directors</div></div><div class="stat"><div class="value">${govCfg.board.term_years}</div><div class="label">Term years</div></div><div class="stat"><div class="value">${govCfg.board.meetings_per_year_minimum}</div><div class="label">Min meetings/year</div></div></div><p class="small" style="margin-top:10px">Quorum: ${esc(govCfg.board.quorum)}</p><div class="rule"></div><a class="dl docx" href="downloads.html">Open downloads center</a></section></main>`;
  return wrap('Governance | CivicOS Institute', body);
}

function buildDownloads(webCfg, govCfg) {
  const rows = webCfg.documents.map(d => {
    const dc = govCfg.documents[d.id] || { version: '1.0', status: 'DRAFT', adopted: null, last_reviewed: null };
    const info = fileInfo(d.id, dc.version || '1.0');
    const sizeBytes = info.pdfExists ? info.pdfSize : info.docxSize;
    const size = `${Math.round((sizeBytes || 0) / 1024)} KB`;
    const pdfBtn = info.pdfExists ? `<a class="dl pdf" href="downloads/pdf/${esc(info.pdfName)}" download>PDF ⬇</a>` : '';
    const docxBtn = `<a class="dl docx" href="downloads/docx/${esc(info.docxName)}" download>DOCX ⬇</a>`;
    return `<tr><td>${esc(d.title)}</td><td>${esc(dc.version || '1.0')}</td><td><span class="badge ${statusClass(dc.status)}">${esc(dc.status || 'DRAFT')}</span></td><td>${pdfBtn} ${docxBtn}</td><td>${size}</td></tr>`;
  }).join('');

  const changelog = webCfg.documents.map(d => {
    const dc = govCfg.documents[d.id] || { version: '1.0', status: 'DRAFT', last_reviewed: null };
    return `<tr><td>${esc(d.id)}</td><td>${esc(dc.version || '1.0')}</td><td>${esc(dc.status || 'DRAFT')}</td><td>${esc(dc.last_reviewed || 'N/A')}</td></tr>`;
  }).join('');

  const body = `<section class="hero"><div class="eyebrow">— GOVERNANCE DOWNLOADS</div><h1>Document Suite</h1><p>Download every governance document with current status, version, and audit metadata.</p></section><main><article>
    <section class="card"><h2>Layer 1 — At a glance</h2><p>Access each policy in PDF and DOCX, plus a full suite archive.</p></section>
    <section class="card layer"><h2>Layer 2 — Full text</h2><button class="tog" aria-label="Toggle full text" aria-expanded="false" aria-controls="full-downloads" onclick="toggleFull('full-downloads',this)">Show full text</button><div id="full-downloads" class="fulltext"><p>This page includes complete download metadata and a changelog table for review and audit traceability.</p></div></section>
    <section class="card layer"><h2>Layer 3 — Download</h2><a class="dl zip" href="downloads/CivicOS_Governance_Suite.zip" download>Download Full Suite ZIP</a></section>
    <section class="card layer"><h2>Documents</h2><div class="table-wrap"><table><thead><tr><th align="left">Document</th><th align="left">Version</th><th align="left">Status</th><th align="left">Downloads</th><th align="left">Size</th></tr></thead><tbody>${rows}</tbody></table></div></section>
    <section class="card layer"><h2>Changelog: Version History</h2><div class="table-wrap"><table><thead><tr><th align="left">ID</th><th align="left">Version</th><th align="left">Status</th><th align="left">Last Reviewed</th></tr></thead><tbody>${changelog}</tbody></table></div></section>
  </article></main>`;
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
