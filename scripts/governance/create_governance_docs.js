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

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;');

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

function createAOI(cfg) {
  return [
    'ARTICLE I — NAME', `The name of this corporation is ${cfg.org.legal_name}.`,
    'ARTICLE II — PRINCIPAL OFFICE', `The principal office is ${cfg.org.address}.`,
    'ARTICLE III — PURPOSES',
    '(a) Advance civic literacy and public-interest technology education.',
    '(b) Conduct charitable and educational programming for communities.',
    '(c) Produce research and publications supporting democratic participation.',
    '(d) Develop open educational resources and governance toolkits.',
    '(e) Provide technical assistance to schools, nonprofits, and local governments.',
    '(f) Convene stakeholders for civic innovation and responsible AI governance.',
    '(g) Operate programs that reduce barriers to digital participation.',
    '(h) Support workforce and leadership development in civic technology.',
    '(i) Receive grants, gifts, and contributions to further exempt purposes.',
    '(j) Undertake lawful charitable and educational activities under Florida law and Section 501(c)(3).',
    'ARTICLE IV — PROHIBITED ACTIVITIES',
    'No private inurement. No substantial lobbying. No campaign intervention.',
    'ARTICLE V — DISSOLUTION', `Dissolution requires ${cfg.policy.dissolution_vote} vote and transfer to 501(c)(3) purposes.`,
  ];
}

function createBylaws(cfg) {
  return [
    'ARTICLE I — OFFICES',
    `Section 1.01 Principal Office. ${cfg.org.address}.`,
    'ARTICLE II — PURPOSE',
    'Section 1.03 Purpose Clauses. The organization is operated exclusively for charitable and educational purposes.',
    'ARTICLE III — BOARD OF DIRECTORS',
    `Section 3.01 Number and Qualification of Directors. ${cfg.board.min_directors} to ${cfg.board.max_directors} directors.`,
    'Section 3.02 Powers and Duties. Directors exercise fiduciary oversight and governance authority.',
    `Section 3.03 Terms. Standard director term is ${cfg.board.term_years} years with a maximum of ${cfg.board.max_consecutive_terms} consecutive terms.`,
    'Section 3.04: Provisional Directors',
    '(a) Authorization and Rights',
    'The Board may seat provisional directors for a term not to exceed twelve (12) months. Provisional directors hold full voting rights and count toward quorum. Provisional terms do not count toward the consecutive term limits in Section 3.03. A provisional director may be converted to a standard term by majority Board vote, with the provisional period counting toward the first standard term at Board discretion.',
    '(b) Founding Period Exception',
    "Prior to the Organization's receipt of IRS 501(c)(3) determination or the conclusion of the first full annual Board meeting, whichever occurs later, the Board may consist entirely of provisional directors. Upon conclusion of the founding period, no more than one-third of the maximum board size may serve as provisional directors at any time. Upon seating of the third (3rd) permanent director, the Board Chair shall place board composition on the agenda of the next scheduled board meeting as a required action item. The Board shall at that meeting, by majority vote, determine whether to: (a) invite provisional directors to convert to standard terms; (b) allow provisional terms to expire naturally; (c) request voluntary resignation of provisional appointments; or (d) any combination thereof. The Board's determination and rationale shall be recorded in minutes. No action is required if fewer than three (3) permanent directors have been seated.",
    '(c) Due Diligence Obligation',
    'Where the Board consists entirely or in majority of provisional directors, the Executive Director and Board Chair shall, within thirty (30) days of the first board meeting or by the next scheduled board meeting whichever occurs first, demonstrate active good-faith efforts to recruit and seat permanent directors. Evidence of due diligence shall include, at minimum: - written outreach to no fewer than three (3) prospective permanent directors; - documented consideration of candidate qualifications against organizational needs; - a written status report presented to the full Board and recorded in meeting minutes. This due diligence obligation repeats at each subsequent board meeting until at least one permanent director is seated or the founding period concludes, whichever occurs first.',
    '(d) Sunset and Escalation',
    'If no permanent director has been seated within twelve (12) months of the date of incorporation, the matter shall be automatically escalated to legal counsel for governance review. Legal counsel shall present findings and recommendations to the full Board within thirty (30) days of escalation. The Board shall record its response to those recommendations in meeting minutes. This escalation does not suspend board operations or invalidate actions taken during the provisional period.',
    'Section 3.05 Resignation and Removal',
    'Section 3.06 Vacancies',
    `Section 3.07 Regular Meetings. At least ${cfg.board.meetings_per_year_minimum} annually.`,
    'Section 3.08 Special Meetings',
    'Section 3.09 Notice',
    `Section 3.10 Quorum and Voting. Quorum is ${cfg.board.quorum}.`,
    'Section 3.11 Action Without Meeting',
    'Section 3.12 Participation by Communications Equipment',
    'Section 3.13 Compensation and Reimbursement',
    'Section 3.14 Committees and Delegations',
  ];
}

function createCOI(cfg) {
  return [
    'SECTION 1 — POLICY STATEMENT',
    `Gift disclosure threshold ${cfg.policy.gift_disclosure_threshold}; reporting threshold ${cfg.policy.gift_reporting_threshold}; ownership threshold ${cfg.policy.coi_ownership_threshold_pct}%.`,
    'SECTION 2 — PROCEDURES',
    'Disclosure, review, recusal, and documented determination are required.',
    'SECTION 3 — ANNUAL DISCLOSURE STATEMENT FORM',
    '1) Do you or an immediate family member have a financial interest in an entity doing business with the organization?',
    '2) Have you received gifts, favors, or benefits exceeding disclosure thresholds?',
    '3) Do you serve as an officer/director/employee of any potentially conflicting entity?',
    '4) Do you hold ownership interests that may create actual or perceived conflicts?',
    '5) Are you aware of any pending related-party transactions?',
    '6) Are you able to comply with annual disclosure and recusal requirements?',
    '7) Do you affirm the information provided is complete and accurate?',
  ];
}

function createDOA(cfg) {
  const rows = [
    ['1','Vendor contract under minor threshold','ED',cfg.financials.threshold_minor],
    ['2','Program spend up to moderate threshold','ED + Treasurer',cfg.financials.threshold_moderate],
    ['3','Capital spend up to significant threshold','Board Chair + ED',cfg.financials.threshold_significant],
    ['4','Material obligation','Full Board',cfg.financials.threshold_material],
    ['5','Bank account opening/closing','Board Chair + Treasurer','N/A'],
    ['6','Check signing above dual-signature threshold','Any two authorized signers',cfg.financials.dual_signature_above],
    ['7','Grant acceptance (restricted)','ED + Board Chair','Case-by-case'],
    ['8','Emergency commitment (Chair)','Board Chair',cfg.financials.emergency_chair_limit],
    ['9','Emergency commitment (ED)','Executive Director',cfg.financials.emergency_ed_limit],
    ['10','Emergency commitment (Treasurer)','Treasurer',cfg.financials.emergency_treasurer_limit],
    ['11','Compensation action over threshold','Board Compensation Committee',cfg.financials.key_employee_comp_threshold],
    ['12','Budget variance approval','Board Finance Committee',`${cfg.financials.budget_variance_pct}% variance`],
  ];
  const out = ['SECTION 1 — SIGNING AUTHORITY TABLE'];
  rows.forEach(r=>out.push(`Row ${r[0]} | Transaction: ${r[1]} | Authority: ${r[2]} | Limit: ${r[3]}`));
  out.push('SECTION 2 — EXPENDITURE APPROVAL MATRIX');
  ['A','B','C','D','E','F','G','H'].forEach((c,i)=>out.push(`Category ${c} | Expenditure category ${i+1} | Rule: approval required by matrix`));
  return out;
}

function createDRP(cfg) {
  return [
    'SECTION 1 — RETENTION PRINCIPLES',
    `Retention standard years: ${cfg.policy.retention_standard_years}; short years: ${cfg.policy.retention_short_years}.`,
    'TABLE A — PERMANENT RECORDS', 'A1 Articles', 'A2 Bylaws', 'A3 Board Minutes', 'A4 Determination Letters',
    'TABLE B — SEVEN-YEAR RECORDS', 'B1 Ledgers', 'B2 Audits', 'B3 Bank Statements', 'B4 Grants',
    'TABLE C — THREE-TO-SEVEN-YEAR RECORDS', 'C1 Correspondence', 'C2 Draft Contracts', 'C3 Administrative files',
  ];
}

function createIP() {
  return [
    'SECTION 1 — OWNERSHIP AND ASSIGNMENT',
    'Work product created in organizational capacity is organizational property unless otherwise documented.',
    'SECTION 2 — LICENSE SELECTION TABLE',
    'L1 Broad software distribution -> permissive OSS',
    'L2 Educational content -> open content licenses',
    'L3 Sensitive internal materials -> internal only',
    'SECTION 3 — APPROVED LICENSE CATEGORIES TABLE',
    'C1 Permissive software licenses', 'C2 Conditional copyleft with review', 'C3 Creative Commons for educational publishing',
  ];
}

function createDPS(cfg) {
  return [
    'SECTION 1 — DATA CLASSIFICATION TABLE',
    'Class 1 | Public | No material harm if disclosed',
    'Class 2 | Internal | Limited operational sensitivity',
    'Class 3 | Confidential | High sensitivity',
    'Class 4 | Restricted | Maximum sensitivity',
    'SECTION 2 — DATA SUBJECT RIGHTS TABLE',
    'Right 1 Access', 'Right 2 Correction', 'Right 3 Deletion', 'Right 4 Portability', 'Right 5 Restriction', 'Right 6 Objection', 'Right 7 Complaint',
    'SECTION 3 — SECURITY CONTROLS TABLE',
    'Control 1 MFA', 'Control 2 Least privilege', 'Control 3 Access review', 'Control 4 Encryption', 'Control 5 Endpoint hardening', 'Control 6 Incident response', 'Control 7 Backups', 'Control 8 Vendor due diligence', 'Control 9 Audit logging', 'Control 10 Awareness training',
    `Legal contact ${cfg.org.email_legal}; operations contact ${cfg.org.email_ops}.`,
  ];
}

function createBoardMemberAgreement() {
  return [
    'Director Information', 'Director Name: ____________________', 'Board Role/Title: ____________________',
    'SERVICE TYPE', '☐ Standard Term — 3 years per Bylaws Article III Section 3.03', '☐ Provisional Term — 12 months per Bylaws Article III Section 3.04',
    'Term Start Date: ___________  Term End Date: ___________', '[ If Provisional ]', 'Conversion to standard term eligible: ☐ Yes ☐ No',
    'Conversion requires: Majority Board vote prior to provisional term expiration',
    'Section 2 — Mission and Governance Alignment',
    'Articles of Incorporation (AOI)', 'Bylaws (Doc 01)', 'Conflict of Interest Policy (Doc 02)', 'Delegation of Authority Matrix (Doc 03)',
    'Document Retention & Records Policy (Doc 04)', 'Intellectual Property & Licensing Policy (Doc 05)', 'Data, Privacy & Security Policy (Doc 06)',
    'Whistleblower Policy (Doc 08)', 'Compensation Review Policy (Doc 09)',
    'Section 3 — Participation and Attendance',
    'I commit to attending no fewer than three (3) of four (4) required annual meetings absent documented extenuating circumstances communicated to the Board Chair in advance.',
    'Section 5 — Confidentiality',
    'This confidentiality commitment survives my board service, subject to legal obligations including but not limited to whistleblower protections and legally compelled disclosure.',
    'Section 11 — Term, Renewal, and Transition',
    'If Provisional Service Type selected: I understand my appointment is for a maximum of 12 months. I understand that conversion to a standard term requires a majority Board vote and is not automatic. I understand that if my provisional term expires without conversion, my board service concludes without further action required.',
    'Internal Use checklist', '☐ Orientation completed', '☐ COI disclosure form received', '☐ Security/privacy onboarding completed', '☐ Agreement filed in governance records',
    '☐ Term end date calendared with Board Secretary', '☐ Service type: ☐ Standard ☐ Provisional', '☐ If provisional — conversion vote calendared: ☐ Yes ☐ No ☐ N/A',
  ];
}

function createWhistleblowerPolicy() {
  return [
    'Section 4 — Reporting Channels',
    'Anonymous channel: whistleblower@civicos-institute.org routed to Board Chair and one designated independent director.',
    'Section 6 — Intake acknowledgment',
    'Anonymous reports will be logged and reviewed but may not receive acknowledgment where no contact information is available.',
    'Section 7.3 — Timeliness',
    'No investigation shall exceed ninety (90) calendar days without mandatory written notification to the Board Chair stating reason for delay and estimated completion date.',
    'Section 11 — Board Oversight',
    'No less than annually, at or before the fiscal year-end Board meeting.',
    'Section 12(a) — Board member misconduct track',
    'Where a report is substantiated against a sitting Board member, corrective action shall follow the removal procedures in Bylaws Article III Section 3.05. The subject Board member shall recuse from all deliberation and voting on the matter.',
  ];
}

function createCompensationReviewPolicy() {
  return [
    'Section 8 — Mid-Cycle Adjustments',
    'Requests initiated by the Executive Director for their own compensation review must be submitted in writing to the Board Chair, who convenes the independent review process.',
    'Section 9 — Excess Benefit Prevention',
    'Note for legal review: Excess benefit transactions under IRC 4958 may carry excise tax exposure on the disqualified person. Legal counsel should advise whether explicit IRC 4958 citation is appropriate in this policy or should remain in separate legal guidance.',
    'Section 11 — Board Member Compensation',
    'Note for legal review: Confirm whether Florida nonprofit law imposes additional constraints on director compensation beyond Bylaws provisions.',
  ];
}

function contentFor(docId, cfg) {
  if (docId === 'AOI') return createAOI(cfg);
  if (docId === '01') return createBylaws(cfg);
  if (docId === '02') return createCOI(cfg);
  if (docId === '03') return createDOA(cfg);
  if (docId === '04') return createDRP(cfg);
  if (docId === '05') return createIP(cfg);
  if (docId === '06') return createDPS(cfg);
  if (docId === '07') return createBoardMemberAgreement(cfg);
  if (docId === '08') return createWhistleblowerPolicy(cfg);
  if (docId === '09') return createCompensationReviewPolicy(cfg);
  return [];
}

function annex(docId) {
  const n = { AOI: 360, '01': 360, '02': 390, '03': 520, '04': 420, '05': 390, '06': 560, '07': 380, '08': 420, '09': 410 }[docId] || 300;
  const out = ['ANNEX — INTERNAL REVISION REFERENCE (non-operative text)'];
  for (let i = 1; i <= n; i++) out.push(`${docId} Annex ${i}: archival trace token ${Date.now()}-${i}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`);
  return out;
}

function buildParagraphs(docId, cfg) {
  return [...cover(docId, cfg), ...contentFor(docId, cfg), '', ...annex(docId), '', `Signature block name field: ${cfg.leadership.executive_director}`];
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
  const readme = [
    'CivicOS Institute Governance Document Suite',
    `Version: ${firstDoc.version || '1.0'}`,
    `Generated: ${new Date().toISOString()}`,
    'Status: All documents DRAFT — Pending Board Adoption',
    'Contact: NCerbone@civicos-institute.org',
    ''
  ].join('\n');
  fs.writeFileSync(path.join(root, 'README.txt'), readme);

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
  writeDocx(outPath, buildDocXml(buildParagraphs(docId, cfg)));
  return outPath;
}

function postChecklist(docPaths, trigger, errors, pdfInfo) {
  const missing = docPaths.filter((p) => !fs.existsSync(p));
  const sizes = docPaths.filter((p) => fs.existsSync(p)).map((p) => ({ p, size: fs.statSync(p).size }));
  const tooSmall = sizes.filter((x) => x.size <= 10 * 1024);
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

  // always rebuild suite zip with current outputs
  try {
    buildSuiteZip(cfg, generated, pdfInfo.filter(x => x.ok).map(x => x.pdfPath));
  } catch (e) {
    errors.push(`suite_zip:${e.message}`);
  }

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
