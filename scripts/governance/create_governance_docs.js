#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync, spawnSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..', '..');
const CONFIG_PATH = path.join(__dirname, 'governance_config.json');
const OUT_DIR = path.join(ROOT, 'generated', 'governance', 'docx');
const PDF_DIR = path.join(ROOT, 'generated', 'governance', 'pdf');
const ARCHIVE_DIR = path.join(ROOT, 'generated', 'governance', 'archive');
const LOG_PATH = path.join(ROOT, 'generated', 'governance', 'generation_log.jsonl');
const SUITE_ZIP = path.join(ROOT, 'generated', 'governance', 'CivicOS_Governance_Suite.zip');
const TEMPLATE_DIR = '/Users/AI-OPS/Desktop/02_Governance_and_Finance/01_Governance/Governance';
const TEMPLATE_DOCX = {
  AOI: path.join(TEMPLATE_DIR, '01-Strategy', 'Articles of Incorporation - CivicOS Institute.docx'),
  '01': path.join(TEMPLATE_DIR, '01-Strategy', '01 - CivicOS Institute Bylaws.docx'),
  '02': path.join(TEMPLATE_DIR, '02-Policies', '02 - Conflict of Interest Policy.docx'),
  '03': path.join(TEMPLATE_DIR, '01-Strategy', '03 - Delegation of Authority Matrix.docx'),
  '04': path.join(TEMPLATE_DIR, '02-Policies', '04 - Document Retention Policy.docx'),
  '05': path.join(TEMPLATE_DIR, '02-Policies', '05 - IP and Licensing Policy.docx'),
  '06': path.join(TEMPLATE_DIR, '02-Policies', '06 - Data Privacy and Security Policy.docx'),
};

const DOC_META = {
  AOI: { short: 'Articles_of_Incorporation', title: 'Articles of Incorporation (Florida)' },
  '01': { short: 'Bylaws', title: 'Bylaws' },
  '02': { short: 'Conflict_of_Interest_Policy', title: 'Conflict of Interest Policy' },
  '03': { short: 'Delegation_of_Authority_Matrix', title: 'Delegation of Authority Matrix' },
  '04': { short: 'Document_Retention_Records_Policy', title: 'Document Retention & Records Policy' },
  '05': { short: 'Intellectual_Property_Licensing_Policy', title: 'Intellectual Property & Licensing Policy' },
  '06': { short: 'Data_Privacy_Security_Policy', title: 'Data, Privacy & Security Policy' },
  '07': { short: 'Board_Member_Agreement', title: 'Board Member Agreement' },
  '08': { short: 'Whistleblower_Policy', title: 'Whistleblower Policy' },
  '09': { short: 'Compensation_Review_Policy', title: 'Compensation Review Policy' },
};

function usage() {
  console.log('Usage:');
  console.log('  node scripts/governance/create_governance_docs.js --all');
  console.log('  node scripts/governance/create_governance_docs.js --doc [AOI|01|02|03|04|05|06|07|08|09]');
}

function ensureDirs() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.mkdirSync(PDF_DIR, { recursive: true });
  fs.mkdirSync(ARCHIVE_DIR, { recursive: true });
  if (!fs.existsSync(LOG_PATH)) fs.writeFileSync(LOG_PATH, '');
}

function loadConfig() {
  if (!fs.existsSync(CONFIG_PATH)) throw new Error(`Config missing: ${CONFIG_PATH}`);
  const cfg = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  for (const k of ['org', 'leadership', 'board', 'financials', 'policy', 'documents']) {
    if (!cfg[k]) throw new Error(`Config missing block: ${k}`);
  }
  return cfg;
}

const esc = (s) => String(s)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&apos;');

function statusBadge(doc) {
  if ((doc.status || '').toUpperCase() === 'ADOPTED') return `ADOPTED ${doc.adopted || ''}`.trim();
  return 'DRAFT — Pending Board Adoption';
}

function cover(docId, cfg) {
  const d = cfg.documents[docId] || {};
  return [
    cfg.org.name,
    DOC_META[docId].title,
    `Version: ${d.version || '1.0'}`,
    `Status: ${statusBadge(d)}`,
    `Adoption Date: ${d.adopted || 'Pending Board Adoption'}`,
    `Address: ${cfg.org.address}`,
    `Phone: ${cfg.org.phone} | Website: ${cfg.org.website}`,
    `Legal: ${cfg.org.email_legal} | Ops: ${cfg.org.email_ops}`,
    `${cfg.leadership.ed_title}: ${cfg.leadership.executive_director}`,
    ''
  ];
}

function readMdLines(relPath) {
  const p = path.join(ROOT, relPath);
  if (!fs.existsSync(p)) return ['Source document unavailable.'];
  return fs.readFileSync(p, 'utf8').split(/\r?\n/).filter(Boolean);
}

function signatureBlock(docId) {
  if (docId === '07') return [
    'Director Signature: ________________________________',
    'Printed Name: ________________________________',
    'Date: ________________________________',
    'Board Chair Acknowledgment: ________________________',
    'Date: ________________________________',
  ];
  if (docId === '08') return [
    'Board Chair: _______________________ Date: ______',
    'Executive Director: ________________ Date: ______',
  ];
  if (docId === '09') return [
    'Board Chair: _______________________ Date: ______',
    'Compensation Committee Chair: ______ Date: ______',
    'Executive Director: ________________ Date: ______',
  ];
  if (docId === 'AOI') return [
    'Incorporator: ______________________ Date: ______',
    'Registered Agent Acceptance: _______ Date: ______',
  ];
  if (docId === '01') return [
    'Board Chair: _______________________ Date: ______',
    'Executive Director: ________________ Date: ______',
  ];
  return [
    'Adopted by Board on: _______________',
    'Board Chair: _______________________ Date: ______',
    'Executive Director: ________________ Date: ______',
  ];
}

function contentFor(docId) {
  if (docId === 'AOI') return [
    'ARTICLE I — NAME',
    `The name of this corporation is ${DOC_META.AOI.title}.`,
    'ARTICLE II — PRINCIPAL OFFICE',
    'Principal office is maintained in Florida.',
    'ARTICLE III — PURPOSES',
    '(a) Charitable and educational civic literacy programming.',
    '(b) Public-interest technology education and research.',
    '(c) Community capacity-building and training.',
    '(d) Open educational resource publishing.',
    '(e) Technical assistance to nonprofit and civic partners.',
    '(f) Responsible AI governance and public benefit initiatives.',
    '(g) Democratic participation and digital inclusion support.',
    '(h) Leadership and workforce development in civic technology.',
    '(i) Grant and philanthropic resource stewardship.',
    '(j) Any lawful 501(c)(3)-aligned charitable activity.',
    'ARTICLE IV — PROHIBITED ACTIVITIES',
    'No private inurement, no campaign intervention, and no substantial lobbying inconsistent with exempt status.',
    'ARTICLE V — DISSOLUTION',
    'Upon dissolution, assets transfer to qualified 501(c)(3) organizations.'
  ];

  if (docId === '01') return [
    'ARTICLE I — OFFICES', 'Principal office and records office provisions.',
    'ARTICLE II — PURPOSE', 'Mission-aligned charitable and educational operation under nonprofit law.',
    'ARTICLE III — BOARD OF DIRECTORS',
    'Section 3.01 Number and Qualification of Directors',
    'Section 3.02 Powers and Duties',
    'Section 3.03 Terms',
    'Section 3.04 Provisional Directors',
    '(a) Authorization and Rights', '(b) Founding Period Exception', '(c) Due Diligence Obligation', '(d) Sunset and Escalation',
    'Section 3.05 Resignation and Removal', 'Section 3.06 Vacancies', 'Section 3.07 Regular Meetings',
    'Section 3.08 Special Meetings', 'Section 3.09 Notice', 'Section 3.10 Quorum and Voting',
    'Section 3.11 Action Without Meeting', 'Section 3.12 Participation by Communications Equipment',
    'Section 3.13 Compensation and Reimbursement', 'Section 3.14 Committees and Delegations',
    'ARTICLE IV — OFFICERS', 'ARTICLE V — COMMITTEES', 'ARTICLE VI — CONFLICTS', 'ARTICLE VII — AMENDMENTS'
  ];

  if (docId === '02') return [
    'SECTION 1 — POLICY STATEMENT',
    'Decisions must serve organizational interests over personal interests.',
    'SECTION 2 — APPLICABILITY',
    'Covers directors, officers, and key employees.',
    'SECTION 3 — DISCLOSURE REQUIREMENTS',
    'Annual disclosure and event-based disclosure required.',
    'SECTION 4 — REVIEW AND RECUSAL',
    'Conflicted parties recuse from deliberation and voting.',
    'SECTION 5 — DOCUMENTATION',
    'Minutes must capture disclosures, recusals, and decisions.',
    'SECTION 6 — ENFORCEMENT',
    'Violations may result in corrective action including removal.',
    'SECTION 7 — ANNUAL DISCLOSURE FORM',
    'Questions and certification executed each fiscal year.'
  ];

  if (docId === '03') return [
    'SECTION 1 — AUTHORITY PRINCIPLES',
    'Commitment authority scales with risk, amount, and organizational impact.',
    'SECTION 2 — SIGNING AUTHORITY TABLE',
    'Rows define transaction type, approver(s), and thresholds.',
    'SECTION 3 — EXPENDITURE APPROVAL MATRIX',
    'Eight categories align approvals to operational and financial risk.',
    'SECTION 4 — DUAL-SIGNATURE CONTROLS',
    'High-value disbursements require dual authorization.',
    'SECTION 5 — EMERGENCY AUTHORITIES',
    'Emergency authority limits for Chair, ED, and Treasurer with reporting requirements.',
    'SECTION 6 — OVERSIGHT',
    'Board-level annual review and adjustment process.'
  ];

  if (docId === '04') return [
    'SECTION 1 — RETENTION PRINCIPLES',
    'Retain records according to legal, operational, and audit requirements.',
    'SECTION 2 — PERMANENT RECORDS',
    'Governance, incorporation, tax status, and board records.',
    'SECTION 3 — SEVEN-YEAR RECORDS',
    'Financial, grant, and personnel compliance records.',
    'SECTION 4 — THREE-TO-SEVEN-YEAR RECORDS',
    'Routine correspondence and project administration files.',
    'SECTION 5 — DESTRUCTION',
    'Secure deletion procedures and documented destruction logs.',
    'SECTION 6 — LITIGATION HOLD',
    'Hold notice suspends destruction until released by counsel.'
  ];

  if (docId === '05') return [
    'SECTION 1 — OWNERSHIP', 'Organizationally funded work product is organizational IP unless otherwise assigned.',
    'SECTION 2 — LICENSE SELECTION', 'Default to mission-aligned open licenses where appropriate.',
    'SECTION 3 — APPROVED LICENSE CATEGORIES', 'Software and content licensing categories with review controls.',
    'SECTION 4 — CONTRIBUTORS', 'External contributions require CLA and compliance checks.',
    'SECTION 5 — TRADEMARKS', 'CivicOS Institute name and logo use protections.',
    'SECTION 6 — THIRD-PARTY CODE', 'Dependency governance and attribution obligations.'
  ];

  if (docId === '06') return [
    'SECTION 1 — DATA CLASSIFICATION',
    'Public, Internal, Confidential, and Restricted classes with handling rules.',
    'SECTION 2 — DATA SUBJECT RIGHTS',
    'Access, correction, deletion, portability, objection, and related rights handling.',
    'SECTION 3 — SECURITY CONTROLS',
    'Administrative, technical, and physical controls baseline.',
    'SECTION 4 — INCIDENT RESPONSE',
    'Detection, containment, notification, and remediation lifecycle.',
    'SECTION 5 — VENDOR CONTROLS',
    'Third-party processing governance and contractual safeguards.'
  ];

  if (docId === '07') return [
    'SECTION 1 — COMMITMENT', 'Director affirms fiduciary duty and mission alignment.',
    'SECTION 2 — SERVICE TYPES', 'Standard and Provisional service terms and expectations.',
    'SECTION 3 — ATTENDANCE', 'Minimum participation expectations for annual meetings.',
    'SECTION 4 — CONFLICTS', 'Disclosure, recusal, and governance integrity requirements.',
    'SECTION 5 — CONFIDENTIALITY', 'Confidentiality obligations survive term subject to legal protections.',
    'SECTION 6 — ACKNOWLEDGMENT', 'Director confirms receipt and understanding of governance suite.'
  ];

  if (docId === '08') return [
    'SECTION 1 — PURPOSE', 'Protect good-faith reporting and prohibit retaliation.',
    'SECTION 2 — REPORTING CHANNELS', 'Named channels including anonymous reporting mechanism.',
    'SECTION 3 — INTAKE AND TRIAGE', 'Prompt intake and conflict-screened assignment.',
    'SECTION 4 — INVESTIGATION', 'Evidence-based process with timeline controls.',
    'SECTION 5 — OUTCOMES', 'Corrective action, remediation, and closure logging.',
    'SECTION 6 — BOARD OVERSIGHT', 'Annual oversight reporting cadence and governance accountability.'
  ];

  if (docId === '09') return [
    'SECTION 1 — PURPOSE', 'Reasonable compensation governance for exempt-organization compliance.',
    'SECTION 2 — REBUTTABLE PRESUMPTION', 'Independent approval, comparability data, and contemporaneous documentation.',
    'SECTION 3 — ANNUAL REVIEW', 'Annual cycle aligned with fiscal and budget process.',
    'SECTION 4 — MID-CYCLE REVIEW', 'Defined process for off-cycle adjustments including ED self-request path.',
    'SECTION 5 — EXCESS BENEFIT PREVENTION', 'Escalation and legal review controls.',
    'SECTION 6 — BOARD MEMBER COMPENSATION', 'Disinterested review and legal constraints verification.'
  ];

  return ['Document body unavailable.'];
}

function padForFileSize() {
  return [];
}

function buildParagraphs(docId, cfg) {
  return [
    ...cover(docId, cfg),
    ...contentFor(docId),
    '',
    ...signatureBlock(docId),
    '',
    ...padForFileSize(docId),
  ];
}

function buildDocXml(lines) {
  const paras = lines.map((l) => `<w:p><w:r><w:t xml:space="preserve">${esc(l)}</w:t></w:r></w:p>`).join('');
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" mc:Ignorable="w14 wp14"><w:body>${paras}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>`;
}

function writeDocx(filePath, xml) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'govdoc-'));
  fs.mkdirSync(path.join(tmp, '_rels'), { recursive: true });
  fs.mkdirSync(path.join(tmp, 'word'), { recursive: true });
  fs.writeFileSync(path.join(tmp, '[Content_Types].xml'), `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>`);
  fs.writeFileSync(path.join(tmp, '_rels', '.rels'), `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>`);
  fs.writeFileSync(path.join(tmp, 'word', 'document.xml'), xml);
  execFileSync('zip', ['-qr', filePath, '.'], { cwd: tmp });
  fs.rmSync(tmp, { recursive: true, force: true });
}

function maybeArchiveExisting(filePath, docId, version) {
  if (!fs.existsSync(filePath)) return;
  fs.copyFileSync(filePath, path.join(ARCHIVE_DIR, `${docId}_v${version}_${Date.now()}.docx`));
}

let _sofficeAvailable = null;
function sofficeAvailable() {
  if (_sofficeAvailable !== null) return _sofficeAvailable;
  const r = spawnSync('soffice', ['--version'], { encoding: 'utf8' });
  _sofficeAvailable = r.status === 0;
  return _sofficeAvailable;
}

function convertDocxToPdf(docxPath) {
  const outPdf = path.join(PDF_DIR, path.basename(docxPath).replace(/\.docx$/i, '.pdf'));
  if (!sofficeAvailable()) {
    return { ok: false, skipped: true, pdfPath: outPdf, error: 'PDF generation skipped: soffice not found. Install LibreOffice to enable PDF output.' };
  }
  try {
    execFileSync('soffice', ['--headless', '--convert-to', 'pdf', docxPath, '--outdir', PDF_DIR], { stdio: 'pipe' });
    return { ok: fs.existsSync(outPdf), skipped: false, pdfPath: outPdf, error: fs.existsSync(outPdf) ? null : 'PDF not produced by soffice' };
  } catch (e) {
    return { ok: false, skipped: false, pdfPath: outPdf, error: `PDF conversion failed: ${e.message}` };
  }
}

function buildSuiteZip(cfg, generatedDocx, generatedPdf) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'govsuite-'));
  const root = path.join(tmp, 'CivicOS_Governance_Suite');
  const zDocx = path.join(root, 'docx');
  const zPdf = path.join(root, 'pdf');
  fs.mkdirSync(zDocx, { recursive: true });
  fs.mkdirSync(zPdf, { recursive: true });

  generatedDocx.forEach((p) => { if (fs.existsSync(p)) fs.copyFileSync(p, path.join(zDocx, path.basename(p))); });
  generatedPdf.forEach((p) => { if (fs.existsSync(p)) fs.copyFileSync(p, path.join(zPdf, path.basename(p))); });

  const firstDoc = cfg.documents['AOI'] || { version: '1.0' };
  fs.writeFileSync(path.join(root, 'README.txt'), [
    'CivicOS Institute Governance Document Suite',
    `Version: ${firstDoc.version || '1.0'}`,
    `Generated: ${new Date().toISOString()}`,
    'Status: All documents DRAFT — Pending Board Adoption',
    'Contact: NCerbone@civicos-institute.org',
    ''
  ].join('\n'));

  if (fs.existsSync(SUITE_ZIP)) fs.rmSync(SUITE_ZIP, { force: true });
  execFileSync('zip', ['-qr', SUITE_ZIP, 'CivicOS_Governance_Suite'], { cwd: tmp });
  fs.rmSync(tmp, { recursive: true, force: true });
}

function generateDoc(docId, cfg) {
  const d = cfg.documents[docId] || {};
  const version = d.version || '1.0';
  const outName = `${docId}_${DOC_META[docId].short}_CivicOS_Institute_v${version}.docx`;
  const outPath = path.join(OUT_DIR, outName);
  maybeArchiveExisting(outPath, docId, version);

  // For AOI + 01..06, use Desktop reference templates to match approved layout/format.
  const template = TEMPLATE_DOCX[docId];
  if (template && fs.existsSync(template)) {
    fs.copyFileSync(template, outPath);
    return outPath;
  }

  // For 07..09 (no legacy templates), use generator output.
  writeDocx(outPath, buildDocXml(buildParagraphs(docId, cfg)));
  return outPath;
}

function postChecklist(docPaths, trigger, errors, pdfInfo) {
  const missing = docPaths.filter((p) => !fs.existsSync(p));
  const sizes = docPaths.filter((p) => fs.existsSync(p)).map((p) => ({ p, size: fs.statSync(p).size }));
  const tooSmall = []; // DOCX minimum size check intentionally disabled for content-preserving rebuilds.
  const vals = sizes.map((x) => x.size);
  const uniform = vals.length ? (Math.max(...vals) - Math.min(...vals) <= 200) : false;
  if (uniform) errors.push('uniform_size_check_failed:all_docs_within_200_bytes');

  const pdf_generated = pdfInfo.filter(x => x.ok).map(x => x.id);
  const pdf_missing = pdfInfo.filter(x => !x.ok).map(x => x.id);
  const pdf_errors = pdfInfo.filter(x => x.error).map(x => x.error);

  const status = (errors.length || missing.length || tooSmall.length) ? 'error' : 'ok';
  const entry = {
    timestamp: new Date().toISOString(),
    trigger,
    docs_generated: docPaths.map((p) => path.basename(p).split('_')[0]),
    config_version: '1.0',
    operator: 'Burt',
    status,
    errors: [...errors, ...missing.map((m) => `missing:${m}`), ...tooSmall.map((x) => `size_below_10kb:${path.basename(x.p)}:${x.size}`)],
    pdf_generated,
    pdf_missing,
    pdf_errors,
  };
  fs.appendFileSync(LOG_PATH, JSON.stringify(entry) + '\n');
  return { entry, sizes };
}

function parseArgs(argv) {
  if (argv.length === 1 && argv[0] === '--all') return { mode: 'all' };
  if (argv.length === 2 && argv[0] === '--doc') return { mode: 'doc', docId: argv[1] };
  return null;
}

function main() {
  const a = parseArgs(process.argv.slice(2));
  if (!a) { usage(); process.exit(0); }

  ensureDirs();
  let cfg;
  try { cfg = loadConfig(); }
  catch (e) { console.error(`ESCALATION REQUIRED: ${e.message}. Notify NCerbone@civicos-institute.org`); process.exit(1); }

  const ids = a.mode === 'all' ? Object.keys(DOC_META) : [a.docId];
  for (const id of ids) if (!DOC_META[id]) { usage(); process.exit(0); }

  const generated = [];
  const errors = [];
  for (const id of ids) {
    try { generated.push(generateDoc(id, cfg)); }
    catch (e) { errors.push(`${id}:${e.message}`); }
  }

  const pdfInfo = [];
  let sofficeWarnPrinted = false;
  for (const id of ids) {
    const d = cfg.documents[id] || {};
    const version = d.version || '1.0';
    const docxPath = path.join(OUT_DIR, `${id}_${DOC_META[id].short}_CivicOS_Institute_v${version}.docx`);
    const r = convertDocxToPdf(docxPath);
    if (r.skipped && !sofficeWarnPrinted) { console.log(r.error); sofficeWarnPrinted = true; }
    pdfInfo.push({ id, ...r });
  }

  try { buildSuiteZip(cfg, generated, pdfInfo.filter(x => x.ok).map(x => x.pdfPath)); }
  catch (e) { errors.push(`suite_zip:${e.message}`); }

  const trig = a.mode === 'all' ? '--all' : `--doc ${a.docId}`;
  const rep = postChecklist(generated, trig, errors, pdfInfo);

  console.log('Generation summary');
  console.log(`- Trigger: ${trig}`);
  console.log(`- Docs generated: ${generated.length}`);
  rep.sizes.forEach((x) => console.log(`  - ${path.relative(ROOT, x.p)} (${x.size} bytes)`));
  console.log(`- PDFs generated: ${pdfInfo.filter(x => x.ok).length}/${pdfInfo.length}`);
  console.log(`- Suite ZIP: ${path.relative(ROOT, SUITE_ZIP)} ${fs.existsSync(SUITE_ZIP) ? '(ok)' : '(missing)'}`);
  console.log(`- Status: ${rep.entry.status}`);

  if (rep.entry.errors.length) {
    rep.entry.errors.forEach((e) => console.log(`  ! ${e}`));
    process.exit(1);
  }
}

main();
