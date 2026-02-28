#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const GOV_CFG = path.join(__dirname, 'governance_config.json');
const WEB_CFG = path.join(__dirname, 'governance_web_config.json');
const OUT = path.join(ROOT, 'generated', 'governance', 'web');
const DOCX_DIR = path.join(ROOT, 'generated', 'governance', 'docx');
const LOG = path.join(ROOT, 'generated', 'governance', 'generation_log.jsonl');

function usage() {
  console.log('Usage: node scripts/governance/create_governance_web.js --all');
}

function esc(s='') { return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }

function mdToHtml(md='') {
  const lines = md.split(/\r?\n/);
  const out = [];
  let inList = false;
  for (const lineRaw of lines) {
    const line = lineRaw.trimEnd();
    if (!line.trim()) { if (inList) { out.push('</ul>'); inList=false; } continue; }
    if (/^###\s+/.test(line)) { if (inList){out.push('</ul>');inList=false;} out.push(`<h3>${esc(line.replace(/^###\s+/,''))}</h3>`); continue; }
    if (/^##\s+/.test(line)) { if (inList){out.push('</ul>');inList=false;} out.push(`<h2>${esc(line.replace(/^##\s+/,''))}</h2>`); continue; }
    if (/^#\s+/.test(line)) { if (inList){out.push('</ul>');inList=false;} out.push(`<h1>${esc(line.replace(/^#\s+/,''))}</h1>`); continue; }
    if (/^[-*]\s+/.test(line)) { if (!inList){out.push('<ul>'); inList=true;} out.push(`<li>${esc(line.replace(/^[-*]\s+/,''))}</li>`); continue; }
    if (/^\d+\)\s+/.test(line)) { if (!inList){out.push('<ul>'); inList=true;} out.push(`<li>${esc(line.replace(/^\d+\)\s+/,''))}</li>`); continue; }
    if (inList) { out.push('</ul>'); inList=false; }
    out.push(`<p>${esc(line)}</p>`);
  }
  if (inList) out.push('</ul>');
  return out.join('\n');
}

function readJson(p) { return JSON.parse(fs.readFileSync(p,'utf8')); }
function readTextMaybe(p) { return fs.existsSync(p) ? fs.readFileSync(p,'utf8') : 'Full text source not found.'; }
function ensure() { fs.mkdirSync(OUT, {recursive:true}); }

function statusClass(status='DRAFT') {
  const s = String(status).toUpperCase();
  if (s === 'ADOPTED') return 'adopted';
  if (s.includes('REVIEW')) return 'review';
  return 'draft';
}

function styles() {
  return `
<style>
:root{--navy:#1B2B4B;--gold:#B8963E;--lg:#F2F4F7;--border:#D0D5DD;--white:#fff;--text:#111;--body:#333;--muted:#777}
*{box-sizing:border-box} body{margin:0;font-family:Georgia,serif;color:var(--body);background:var(--lg)}
a{color:var(--navy)}
.top{background:var(--navy);color:#fff;padding:14px 18px;position:sticky;top:0;z-index:10}
.brand{font-family:Arial,sans-serif;font-weight:700}
.nav-wrap{display:flex;align-items:center;justify-content:space-between}
.nav-links{display:flex;gap:14px}
.nav-links a{color:#fff;text-decoration:none;font-family:Arial,sans-serif;font-size:14px}
.hamb{display:none;background:none;border:1px solid rgba(255,255,255,.4);color:#fff;padding:6px 10px;border-radius:6px}
main{max-width:1100px;margin:22px auto;padding:0 16px}
.card{background:#fff;border:1px solid var(--border);border-radius:8px;padding:16px;border-left:4px solid var(--gold);transition:box-shadow .2s ease}
.card:hover{box-shadow:0 4px 12px rgba(0,0,0,.1)}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.badge{display:inline-block;padding:4px 8px;border-radius:20px;font-family:Arial,sans-serif;font-size:12px;border:1px solid}
.badge.draft{background:#FFF3CD;color:#856404;border-color:#FFEAA7}
.badge.adopted{background:#D1E7DD;color:#0A3622;border-color:#A3CFBB}
.badge.review{background:#CFF4FC;color:#055160;border-color:#9EEAF9}
.kf{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.kf span{font-family:Arial,sans-serif;font-size:12px;background:var(--lg);border:1px solid var(--border);padding:4px 8px;border-radius:16px}
.layer{margin-top:14px}
.fulltext{background:var(--lg);border-left:3px solid var(--border);padding:24px;overflow:hidden;max-height:0;transition:max-height .35s ease}
.fulltext.open{max-height:2000px}
.tog{font-family:Arial,sans-serif;background:#fff;border:1px solid var(--border);padding:8px 12px;border-radius:6px;cursor:pointer}
.dl{display:inline-block;background:var(--navy);color:#fff !important;text-decoration:none;padding:10px 14px;border-radius:6px;font-family:Arial,sans-serif}
.dl:hover{background:var(--gold)}
.small{font-size:12px;color:var(--muted);font-family:Arial,sans-serif}
footer{margin:30px 0;color:var(--muted);font-family:Arial,sans-serif;font-size:12px}
code{font-family:monospace}
@media (max-width:768px){.grid{grid-template-columns:1fr}.hamb{display:inline-block}.nav-links{display:none;flex-direction:column;background:var(--navy);position:absolute;left:0;right:0;top:54px;padding:10px 18px}.nav-links.open{display:flex}.dl{display:block;width:100%;text-align:center}}
</style>`;
}

function script() { return `<script>
function toggleMenu(){document.getElementById('navLinks').classList.toggle('open')}
function toggleFull(id,btn){const e=document.getElementById(id);const open=e.classList.toggle('open');btn.setAttribute('aria-expanded',open?'true':'false');btn.textContent=open?'Hide full text':'Show full text';}
</script>`; }

function nav() {
  return `<header class="top"><div class="nav-wrap"><div class="brand">CivicOS Governance</div><button class="hamb" aria-label="Toggle navigation" onclick="toggleMenu()">☰</button><nav id="navLinks" class="nav-links" aria-label="Governance navigation"><a href="index.html">Index</a><a href="downloads.html">Downloads</a></nav></div></header>`;
}

function pageWrap(title, body) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>${esc(title)}</title>${styles()}</head><body>${nav()}<main>${body}</main>${script()}<footer><main>Generated by create_governance_web.js</main></footer></body></html>`;
}

function findDocx(docId, short, version) {
  const f = `${docId}_${short}_CivicOS_Institute_v${version}.docx`;
  const p = path.join(DOCX_DIR, f);
  return { name: f, path: p, exists: fs.existsSync(p), size: fs.existsSync(p) ? fs.statSync(p).size : 0 };
}

function buildDocPage(d, cfg, web) {
  const dc = cfg.documents[d.id] || {version:'1.0',status:'DRAFT',adopted:null,last_reviewed:null};
  const docx = findDocx(d.id, d.id==='AOI'?'Articles_of_Incorporation':{
    '01':'Bylaws','02':'Conflict_of_Interest_Policy','03':'Delegation_of_Authority_Matrix','04':'Document_Retention_Records_Policy','05':'Intellectual_Property_Licensing_Policy','06':'Data_Privacy_Security_Policy','07':'Board_Member_Agreement','08':'Whistleblower_Policy','09':'Compensation_Review_Policy'}[d.id], dc.version||'1.0');
  const mdPath = path.join(ROOT, d.source_markdown);
  const html = mdToHtml(readTextMaybe(mdPath));
  const body = `
  <article>
    <h1>${esc(d.title)}</h1>
    <section class="layer card" aria-label="At a glance">
      <div><span class="badge ${statusClass(dc.status)}">${esc(dc.status||'DRAFT')}</span></div>
      <p>${esc(d.summary)}</p>
      <div class="kf">${d.key_facts.map(x=>`<span>${esc(x)}</span>`).join('')}</div>
      <div class="small">Last reviewed: ${esc(dc.last_reviewed || 'Not yet reviewed')}</div>
    </section>

    <section class="layer card" aria-label="Full text">
      <button class="tog" aria-expanded="true" aria-controls="full-${d.id}" onclick="toggleFull('full-${d.id}',this)">Hide full text</button>
      <div id="full-${d.id}" class="fulltext open">${html}</div>
    </section>

    <section class="layer card" aria-label="Downloads">
      <a class="dl" href="../docx/${esc(docx.name)}" download>Download document</a>
      <div class="small">Version ${esc(dc.version||'1.0')} · Adoption: ${esc(dc.adopted || 'Pending')} · File size: ${docx.size||'N/A'} bytes</div>
    </section>
  </article>`;
  return pageWrap(`${d.title} | CivicOS Governance`, body);
}

function buildIndex(cfg, web) {
  const cards = web.documents.map((d) => {
    const dc = cfg.documents[d.id] || {version:'1.0',status:'DRAFT',adopted:null,last_reviewed:null};
    const mdPath = path.join(ROOT, d.source_markdown);
    const full = mdToHtml(readTextMaybe(mdPath));
    const docx = findDocx(d.id, d.id==='AOI'?'Articles_of_Incorporation':{
      '01':'Bylaws','02':'Conflict_of_Interest_Policy','03':'Delegation_of_Authority_Matrix','04':'Document_Retention_Records_Policy','05':'Intellectual_Property_Licensing_Policy','06':'Data_Privacy_Security_Policy','07':'Board_Member_Agreement','08':'Whistleblower_Policy','09':'Compensation_Review_Policy'}[d.id], dc.version||'1.0');
    return `<article class="card">
      <h2 style="margin-top:0"><a href="${esc(d.page)}">${esc(d.title)}</a></h2>
      <div><span class="badge ${statusClass(dc.status)}">${esc(dc.status||'DRAFT')}</span></div>
      <p>${esc(d.summary)}</p>
      <div class="kf">${d.key_facts.map(x=>`<span>${esc(x)}</span>`).join('')}</div>
      <div class="small">Last reviewed: ${esc(dc.last_reviewed || 'Not yet reviewed')}</div>
      <div class="layer"><div class="small">Layer 2 — Full text</div><button class="tog" aria-expanded="false" aria-controls="full-${d.id}" onclick="toggleFull('full-${d.id}',this)">Show full text</button>
      <div id="full-${d.id}" class="fulltext">${full}</div></div>
      <div class="layer"><div class="small">Layer 3 — Download</div><a class="dl" href="../docx/${esc(docx.name)}" download>Download</a> <span class="small">v${esc(dc.version||'1.0')} · ${esc(dc.adopted||'Pending')}</span></div>
    </article>`;
  }).join('');

  const body = `
  <section class="card" style="margin-bottom:14px"><h1>Governance</h1><h2>Layer 1 — At a glance</h2><p>${esc(web.transparency_statement)}</p></section>
  <aside class="card" style="margin-bottom:14px" aria-label="Board composition summary"><h2>Board Composition Summary</h2>
  <p><strong>${cfg.board.min_directors}–${cfg.board.max_directors}</strong> directors · ${cfg.board.term_years}-year terms · minimum ${cfg.board.meetings_per_year_minimum} meetings/year · quorum: ${esc(cfg.board.quorum)}</p></aside>
  <section class="grid">${cards}</section>
  <section class="card" style="margin-top:14px" aria-label="Site-wide downloads"><h2>Downloads</h2>
  <a class="dl" href="downloads.html">Open downloads center</a>
  <div class="small" style="margin-top:8px">Includes full suite ZIP and individual document downloads.</div>
  </section>`;
  return pageWrap('Governance | CivicOS Institute', body);
}

function buildDownloads(cfg, web) {
  const rows = web.documents.map((d) => {
    const dc = cfg.documents[d.id] || {version:'1.0',status:'DRAFT',adopted:null};
    const short = d.id==='AOI'?'Articles_of_Incorporation':{
      '01':'Bylaws','02':'Conflict_of_Interest_Policy','03':'Delegation_of_Authority_Matrix','04':'Document_Retention_Records_Policy','05':'Intellectual_Property_Licensing_Policy','06':'Data_Privacy_Security_Policy','07':'Board_Member_Agreement','08':'Whistleblower_Policy','09':'Compensation_Review_Policy'}[d.id];
    const docx = findDocx(d.id, short, dc.version||'1.0');
    return `<tr><td>${esc(d.id)}</td><td>${esc(d.title)}</td><td>${esc(dc.version||'1.0')}</td><td><span class="badge ${statusClass(dc.status)}">${esc(dc.status||'DRAFT')}</span></td><td>${esc(dc.adopted||'Pending')}</td><td>${docx.size||0}</td><td><a class="dl" href="../docx/${esc(docx.name)}" download>Download</a></td></tr>`;
  }).join('');

  const changelog = web.documents.map(d => {
    const dc = cfg.documents[d.id] || {};
    return `<tr><td>${esc(d.id)}</td><td>${esc(dc.version||'1.0')}</td><td>${esc(dc.status||'DRAFT')}</td><td>${esc(dc.last_reviewed||'N/A')}</td></tr>`;
  }).join('');

  const body = `<article>
    <h1>Governance Downloads</h1>
    <section class="card"><h2>Layer 1 — At a glance</h2><p>Download governance documents and review current status/version metadata.</p></section>
    <section class="card layer"><h2>Layer 3 — Download</h2><a class="dl" href="../docx/CivicOS_Governance_Suite.zip" download>Download Full Suite ZIP</a></section>
    <section class="card layer"><h2>Layer 2 — Full text</h2><button class="tog" aria-expanded="false" aria-controls="full-downloads" onclick="toggleFull('full-downloads',this)">Show full text</button><div id="full-downloads" class="fulltext"><p>This page provides complete downloadable governance artifacts and version history for transparency and auditability.</p></div></section>
    <section class="card layer"><h2>Documents</h2><div style="overflow:auto"><table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif">
    <thead><tr><th align="left">ID</th><th align="left">Document</th><th align="left">Version</th><th align="left">Status</th><th align="left">Adoption</th><th align="left">Size (bytes)</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table></div></section>
    <section class="card layer"><h2>Changelog (Version History)</h2><div style="overflow:auto"><table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif"><thead><tr><th align="left">ID</th><th align="left">Version</th><th align="left">Status</th><th align="left">Last Reviewed</th></tr></thead><tbody>${changelog}</tbody></table></div></section>
  </article>`;
  return pageWrap('Governance Downloads | CivicOS Institute', body);
}

function writeOut(name, html) { fs.writeFileSync(path.join(OUT, name), html); }

function validateGenerated(expected) {
  const missing = expected.filter(f => !fs.existsSync(path.join(OUT, f)));
  if (missing.length) throw new Error(`Missing pages: ${missing.join(', ')}`);
  for (const f of expected) {
    const txt = fs.readFileSync(path.join(OUT, f),'utf8');
    for (const needle of ['At a glance', 'Full text', 'Download']) {
      if (!txt.toLowerCase().includes(needle.toLowerCase())) throw new Error(`${f} missing layer marker: ${needle}`);
    }
  }
}

function main() {
  const args = process.argv.slice(2);
  if (!(args.length===1 && args[0]==='--all')) { usage(); process.exit(0); }
  ensure();
  const cfg = readJson(GOV_CFG);
  const web = readJson(WEB_CFG);

  const pages = [];
  writeOut('index.html', buildIndex(cfg, web)); pages.push('index.html');
  web.documents.forEach(d => { writeOut(d.page, buildDocPage(d,cfg,web)); pages.push(d.page); });
  writeOut('downloads.html', buildDownloads(cfg, web)); pages.push('downloads.html');

  validateGenerated(pages);
  console.log(`Generated ${pages.length} governance web pages in ${OUT}`);
  pages.forEach(p => console.log(`- ${p}`));
}

main();
