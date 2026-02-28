#!/usr/bin/env node
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, BorderStyle, WidthType,
  ShadingType, VerticalAlign, HeadingLevel, TabStopType, PageNumberElement,
} = require('docx');
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

const COLOR = { NAVY:'1B2B4B', GOLD:'B8963E', LIGHT_GRAY:'F2F4F7', RULE_GRAY:'D0D5DD', WHITE:'FFFFFF', TEXT:'111111', MUTED:'6B7280' };
const FONT = { SERIF:'Georgia', SANS:'Arial', MONO:'Courier New' };
const PAGE = { WIDTH:12240, HEIGHT:15840, MARGIN:1440, CONTENT_WIDTH:9360 };

const DOC_META = {
  AOI: { short: 'Articles_of_Incorporation', title: 'Articles of Incorporation', subtitle: 'State of Florida' },
  '01': { short: 'Bylaws', title: 'Bylaws' },
  '02': { short: 'Conflict_of_Interest_Policy', title: 'Conflict of Interest Policy' },
  '03': { short: 'Delegation_of_Authority_Matrix', title: 'Delegation of Authority Matrix' },
  '04': { short: 'Document_Retention_Records_Policy', title: 'Document Retention & Records Policy' },
  '05': { short: 'Intellectual_Property_Licensing_Policy', title: 'Intellectual Property & Licensing Policy' },
  '06': { short: 'Data_Privacy_Security_Policy', title: 'Data, Privacy & Security Policy' },
  '07': { short: 'Board_Member_Agreement', title: 'Board Member Agreement', subtitle: 'Individual Director Commitment Document' },
  '08': { short: 'Whistleblower_Policy', title: 'Whistleblower Policy' },
  '09': { short: 'Compensation_Review_Policy', title: 'Compensation Review Policy' },
};

function usage(){
  console.log('Usage:');
  console.log('  node scripts/governance/create_governance_docs.js --all');
  console.log('  node scripts/governance/create_governance_docs.js --doc [AOI|01|02|03|04|05|06|07|08|09]');
}

function ensure(){
  fs.mkdirSync(OUT_DIR,{recursive:true});
  fs.mkdirSync(PDF_DIR,{recursive:true});
  fs.mkdirSync(ARCHIVE_DIR,{recursive:true});
  if(!fs.existsSync(LOG_PATH)) fs.writeFileSync(LOG_PATH,'');
}

function loadConfig(){
  if(!fs.existsSync(CONFIG_PATH)) throw new Error(`Config missing: ${CONFIG_PATH}`);
  const cfg=JSON.parse(fs.readFileSync(CONFIG_PATH,'utf8'));
  for (const k of ['org','leadership','board','financials','policy','documents']) if(!cfg[k]) throw new Error(`Config missing block: ${k}`);
  return cfg;
}

const border=(c=COLOR.RULE_GRAY,s=4)=>({style:BorderStyle.SINGLE,size:s,color:c});

function body(text,opts={}){ return new Paragraph({spacing:{before:80,after:80,line:276},...opts,children:[new TextRun({text,font:FONT.SERIF,size:22,color:COLOR.TEXT,bold:!!opts.bold,italics:!!opts.italic})]}); }
function h1(text){ return new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:320,after:120},border:{bottom:{style:BorderStyle.SINGLE,size:6,color:COLOR.NAVY,space:4}},children:[new TextRun({text,font:FONT.SANS,size:26,bold:true,color:COLOR.NAVY})]}); }
function h2(text){ return new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{before:220,after:80},children:[new TextRun({text,font:FONT.SANS,size:23,bold:true,color:COLOR.NAVY})]}); }
function goldRule(){ return new Paragraph({spacing:{before:160,after:160},border:{bottom:{style:BorderStyle.SINGLE,size:8,color:COLOR.GOLD,space:1}},children:[]}); }
function grayRule(){ return new Paragraph({spacing:{before:80,after:80},border:{bottom:{style:BorderStyle.SINGLE,size:4,color:COLOR.RULE_GRAY,space:1}},children:[]}); }
function spacer(before=120,after=120){ return new Paragraph({spacing:{before,after},children:[]}); }
function sigLine(label,width=52){ return new Paragraph({spacing:{before:200,after:60},children:[new TextRun({text:`${label}: `,font:FONT.SANS,size:20,bold:true,color:COLOR.TEXT}),new TextRun({text:'_'.repeat(width),font:FONT.MONO,size:20,color:COLOR.MUTED})]}); }
function dateLine(){ return new Paragraph({spacing:{before:60,after:160},children:[new TextRun({text:'Date: ',font:FONT.SANS,size:20,bold:true,color:COLOR.TEXT}),new TextRun({text:'_'.repeat(30),font:FONT.MONO,size:20,color:COLOR.MUTED})]}); }
function checkItem(text){ return new Paragraph({spacing:{before:60,after:60},numbering:{reference:'checkboxes',level:0},children:[new TextRun({text,font:FONT.SERIF,size:21,color:COLOR.TEXT})]}); }

function makeTable(rows,colWidths){
  const tableRows=rows.map((row,ri)=>{
    const isHeader=!!row.header; const rowBg=isHeader?COLOR.NAVY:(ri%2===1?COLOR.LIGHT_GRAY:COLOR.WHITE);
    return new TableRow({tableHeader:isHeader,children:row.cells.map((cell,ci)=>new TableCell({
      width:{size:colWidths[ci]||colWidths[colWidths.length-1],type:WidthType.DXA},
      borders:{top:border(),bottom:border(),left:border(),right:border()},
      shading:{fill:cell.bg||rowBg,type:ShadingType.CLEAR},
      margins:{top:100,bottom:100,left:140,right:140},
      verticalAlign:VerticalAlign.CENTER,
      columnSpan:cell.span||1,
      children:[new Paragraph({alignment:cell.align==='center'?AlignmentType.CENTER:cell.align==='right'?AlignmentType.RIGHT:AlignmentType.LEFT,spacing:{before:0,after:0},children:[new TextRun({text:cell.text||'',font:isHeader?FONT.SANS:FONT.SERIF,size:20,bold:isHeader?true:!!cell.bold,color:isHeader?COLOR.WHITE:(cell.color||COLOR.TEXT),italics:!!cell.italic})]})]
    }))});
  });
  return new Table({width:{size:PAGE.CONTENT_WIDTH,type:WidthType.DXA},columnWidths:colWidths,rows:tableRows});
}

function statusBadge(cfg,id){
  const d=cfg.documents[id]||{};
  return (String(d.status||'DRAFT').toUpperCase()==='ADOPTED') ? `ADOPTED · ${d.adopted||''}`.trim() : 'DRAFT — Pending Board Adoption';
}

function buildCover(cfg,doc){
  const d=cfg.documents[doc.id]||{};
  const metaRows=[
    {label:'Document ID',value:doc.id},
    {label:'Version',value:d.version||'1.0'},
    {label:'Status',value:statusBadge(cfg,doc.id)},
    {label:'Contact',value:cfg.org.email_legal},
  ];
  return [
    new Paragraph({spacing:{before:0,after:0},border:{bottom:{style:BorderStyle.SINGLE,size:24,color:COLOR.GOLD,space:1}},children:[]}),
    spacer(480,0),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:0,after:80},children:[new TextRun({text:cfg.org.name.toUpperCase(),font:FONT.SANS,size:28,bold:true,color:COLOR.NAVY,characterSpacing:80})]}),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:40,after:240},border:{bottom:{style:BorderStyle.SINGLE,size:6,color:COLOR.GOLD,space:4}},children:[]}),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:0,after:60},children:[new TextRun({text:'GOVERNANCE DOCUMENT',font:FONT.SANS,size:18,color:COLOR.MUTED,characterSpacing:60})]}),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:0,after:40},children:[new TextRun({text:doc.title,font:FONT.SANS,size:40,bold:true,color:COLOR.NAVY})]}),
    ...(doc.subtitle?[new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:0,after:0},children:[new TextRun({text:doc.subtitle,font:FONT.SERIF,size:22,italics:true,color:COLOR.MUTED})]})]:[]),
    spacer(360,0),grayRule(),spacer(120,0),
    ...metaRows.map(r=>new Paragraph({spacing:{before:60,after:60},children:[new TextRun({text:`${r.label}:  `,font:FONT.SANS,size:20,bold:true,color:COLOR.NAVY}),new TextRun({text:r.value,font:FONT.SERIF,size:20,color:COLOR.TEXT})]})),
    spacer(120,0),grayRule(),spacer(80,0),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:0,after:40},children:[new TextRun({text:cfg.org.address,font:FONT.SANS,size:18,color:COLOR.MUTED})]}),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:0,after:0},children:[new TextRun({text:`${cfg.org.phone}  ·  ${cfg.org.website}`,font:FONT.SANS,size:18,color:COLOR.MUTED})]}),
  ];
}

function buildHeader(cfg,title){ return new Header({children:[new Paragraph({spacing:{before:0,after:80},border:{bottom:{style:BorderStyle.SINGLE,size:6,color:COLOR.NAVY,space:4}},tabStops:[{type:TabStopType.RIGHT,position:PAGE.CONTENT_WIDTH}],children:[new TextRun({text:cfg.org.name,font:FONT.SANS,size:18,bold:true,color:COLOR.NAVY}),new TextRun({text:'\t'}),new TextRun({text:title,font:FONT.SANS,size:18,color:COLOR.MUTED,italics:true})]})]}); }
function buildFooter(cfg,id,ver){ return new Footer({children:[new Paragraph({spacing:{before:80,after:0},border:{top:{style:BorderStyle.SINGLE,size:4,color:COLOR.RULE_GRAY,space:4}},tabStops:[{type:TabStopType.CENTER,position:PAGE.CONTENT_WIDTH/2},{type:TabStopType.RIGHT,position:PAGE.CONTENT_WIDTH}],children:[new TextRun({text:`© ${new Date().getFullYear()} ${cfg.org.name}  ·  Confidential`,font:FONT.SANS,size:16,color:COLOR.MUTED}),new TextRun({text:'\t'}),new TextRun({text:`Doc ${id} v${ver}`,font:FONT.SANS,size:16,color:COLOR.MUTED}),new TextRun({text:'\t'}),new TextRun({text:'Page ',font:FONT.SANS,size:16,color:COLOR.MUTED}),new PageNumberElement()]})]}); }

function sigStandard(cfg){ return [goldRule(),h1('Adoption and Signatures'),body('Adopted by Board on: _______________'),spacer(80),sigLine('Board Chair'),dateLine(),spacer(60),sigLine('Executive Director'),dateLine(),spacer(120),body('Next review due: ____________________', {italic:true})]; }

function buildArticlesOfIncorporation(cfg){
  const doc={id:'AOI',title:'Articles of Incorporation',subtitle:'State of Florida'};
  const purpose=[
    '(a) Advance civic literacy and public-interest technology education.', '(b) Conduct charitable and educational programming for communities.', '(c) Produce research and publications supporting democratic participation.', '(d) Develop open educational resources and governance toolkits.', '(e) Provide technical assistance to schools, nonprofits, and local governments.', '(f) Convene stakeholders for civic innovation and responsible AI governance.', '(g) Operate programs that reduce barriers to digital participation.', '(h) Support workforce and leadership development in civic technology.', '(i) Receive grants, gifts, and contributions to further exempt purposes.', '(j) Undertake lawful charitable and educational activities under Florida law and Section 501(c)(3).',
  ];
  const children=[...buildCover(cfg,doc), new Paragraph({children:[],pageBreakBefore:true}), h1('Article I — Name'), body(`The name of this corporation is ${cfg.org.legal_name}.`), h1('Article II — Duration'), body('The corporation shall have perpetual existence.'), h1('Article III — Purpose'), ...purpose.map(p=>body(p)), h1('Article IV — Prohibited Activities'), body('No part of net earnings shall inure to private benefit; no campaign intervention; no substantial non-exempt lobbying.'), h1('Article V — Dissolution'), body(`Upon dissolution, assets shall transfer to qualifying 501(c)(3) organizations by ${cfg.policy.dissolution_vote} vote.`), h1('Article VI — Registered Agent'), body(`Registered Agent: ${cfg.leadership.registered_agent}`), h1('Article VII — Initial Board'), body(`Initial board composition follows bylaws minimums: ${cfg.board.min_directors} directors.`), h1('Article VIII — Incorporator'), body(`Incorporator: ${cfg.leadership.executive_director}`), goldRule(), h1('Adoption and Signatures'), sigLine('Incorporator'), dateLine(), spacer(60), sigLine('Registered Agent Acceptance'), dateLine()];
  return makeDoc(cfg,doc,children);
}

function buildBylaws(cfg){
  const doc={id:'01',title:'Bylaws'};
  const children=[...buildCover(cfg,doc), new Paragraph({children:[],pageBreakBefore:true}), h1('Article I — Offices'), body('Principal office, registered office, and records office provisions.'), h1('Article II — Purpose'), body('Section 1.03: charitable and educational purpose alignment.'), h1('Article III — Board of Directors'), body('Section 3.01 Number and Qualification of Directors'), body('Section 3.02 Powers and Duties'), body('Section 3.03 Terms'), h2('Section 3.04 Provisional Directors'), body('(a) Authorization and Rights'), body('The Board may seat provisional directors for terms not exceeding 12 months with full voting rights and quorum count.'), body('(b) Founding Period Exception'), body("Prior to IRS 501(c)(3) determination or first full annual board meeting, whichever occurs later, the Board may consist entirely of provisional directors. Upon seating of the third (3rd) permanent director, the Board Chair must place composition on next meeting agenda; board may by majority vote choose conversion, natural expiry, voluntary resignation, or combination thereof. No action required if fewer than three permanent directors are seated."), body('(c) Due Diligence Obligation'), body('(d) Sunset and Escalation'), body('Section 3.05 Resignation and Removal'), body('Section 3.06 Vacancies'), body('Section 3.07 Regular Meetings'), body('Section 3.08 Special Meetings'), body('Section 3.09 Notice'), body('Section 3.10 Quorum and Voting'), body('Section 3.11 Action Without Meeting'), body('Section 3.12 Participation by Communications Equipment'), body('Section 3.13 Compensation and Reimbursement'), body('Section 3.14 Committees and Delegations'), h1('Articles IV–XIII'), body('Officers; Committees; Conflict procedures; Fiscal management; Records; Indemnification; Amendment process; and related governance controls.'), h2('Article IV — Officers'), body('Officer roles include Chair, Treasurer, Secretary, and Executive Director with duties defined by board resolution.'), h2('Article V — Meetings and Notices'), body('Regular meetings occur at least quarterly with notice requirements, agenda posting, and records obligations.'), h2('Article VI — Committees'), body('Standing and ad hoc committees may be constituted by board action with delegated authority limits.'), h2('Article VII — Financial Controls'), body('Budget approval, variance controls, and audit oversight duties are assigned to board and finance leadership.'), h2('Article VIII — Records and Transparency'), body('Minutes, resolutions, and governance records are maintained in accordance with retention policy.'), h2('Article IX — Indemnification'), body('Directors and officers may be indemnified to the maximum extent allowed by law and policy.'), h2('Article X — Amendments'), body('Bylaw amendments require supermajority vote and notice requirements as defined in policy.'), ...sigStandard(cfg)];
  return makeDoc(cfg,doc,children);
}

function buildConflictOfInterest(cfg){
  const doc={id:'02',title:'Conflict of Interest Policy'};
  const children=[...buildCover(cfg,doc), new Paragraph({children:[],pageBreakBefore:true}), h1('1. Policy Statement'), body('Decisions must be made in the best interest of the organization.'), h1('2. Covered Persons'), body('Directors, officers, and key employees are covered.'), h1('3. Disclosure and Recusal'), body('Prompt disclosure and recusal are required.'), h1('4. Review Procedures'), body('Independent review and documented determinations required.'), h1('5. Enforcement'), body('Violations may include corrective action up to removal from service.'), h1('6. Annual Disclosure Statement'), ...[1,2,3,4,5,6,7].map(i=>body(`${i}) Annual disclosure question ${i}.`)), h2('Disclosure Thresholds'), makeTable([{header:true,cells:[{text:'Category'},{text:'Threshold'}]},{cells:[{text:'Gift per occurrence'},{text:`$${cfg.policy.gift_disclosure_threshold}`}]},{cells:[{text:'Gift reporting threshold'},{text:`$${cfg.policy.gift_reporting_threshold}`}]},{cells:[{text:'Ownership threshold'},{text:`${cfg.policy.coi_ownership_threshold_pct}%`}]}],[4300,5060]), ...sigStandard(cfg)];
  return makeDoc(cfg,doc,children);
}

function buildDelegationOfAuthority(cfg){
  const doc={id:'03',title:'Delegation of Authority Matrix',subtitle:'Decision-Making Authority and Financial Controls'};
  const f=cfg.financials;
  const children=[...buildCover(cfg,doc), new Paragraph({children:[],pageBreakBefore:true}), h1('1. Purpose and Scope'), body('Defines signing and spending authority levels with controls proportional to risk.'), h1('2. Authority Levels'), makeTable([{header:true,cells:[{text:'Level'},{text:'Role'},{text:'Scope'}]},{cells:[{text:'L1',bold:true},{text:'Board of Directors'},{text:'Unlimited binding commitments'}]},{cells:[{text:'L2',bold:true},{text:'Board Chair'},{text:`Emergency authority up to $${f.threshold_material.toLocaleString()}`}]},{cells:[{text:'L3',bold:true},{text:'Executive Director'},{text:'Operational authority per thresholds'}]},{cells:[{text:'L4',bold:true},{text:'Director/Manager'},{text:'Department-level authority'}]},{cells:[{text:'L5',bold:true},{text:'Staff/Contractor'},{text:'No binding commitments'}]}],[900,2460,6000]), h1('3. Financial Approval Thresholds'), makeTable([{header:true,cells:[{text:'Threshold'},{text:'Amount'},{text:'Approver'},{text:'Documentation'}]},{cells:[{text:'Minor'},{text:`Under $${f.threshold_minor}`},{text:'Staff/Manager'},{text:'Receipt'}]},{cells:[{text:'Moderate'},{text:`$${f.threshold_minor}–$${f.threshold_moderate}`},{text:'Executive Director'},{text:'Invoice + memo'}]},{cells:[{text:'Significant'},{text:`$${f.threshold_moderate}–$${f.threshold_significant}`},{text:'ED + Treasurer'},{text:'Dual approval'}]},{cells:[{text:'Major'},{text:`Over $${f.threshold_significant}`},{text:'Board'},{text:'Board resolution'}]}],[1800,2200,2560,2800]), h2('3.2 Signing Authority'), makeTable([{header:true,cells:[{text:'Transaction Amount'},{text:'Signature Requirement'},{text:'Authorized Signatories'}]},{cells:[{text:`Under $${f.dual_signature_above}`},{text:'Single'},{text:'ED or Treasurer'}]},{cells:[{text:`$${f.dual_signature_above} and above`},{text:'Dual',bold:true},{text:'ED + Chair or Treasurer'}]},{cells:[{text:'Emergency'},{text:`Up to $${f.threshold_significant}`},{text:'Board Chair'}]}],[2800,3000,3560]), h1('4. Prohibited Actions'), ...['Debt/liability above material threshold without Board approval','Multi-year contracts without Board approval','Real property transfer without Board resolution','Tax-exempt status modifications without Board approval','Litigation settlement above threshold without Board approval','Bank account open/close without authorization'].map(x=>body(`• ${x}`)), h1('5. Operational Controls'), body('All commitments must map to approved budgets, authorized signatories, and documented approvals.'), body('Emergency actions require after-action reporting to the board within seventy-two hours.'), h2('5.1 Personnel and Contracting Controls'), body('Hiring, compensation changes, and contractor engagements follow delegated authority and policy constraints.'), h2('5.2 Procurement Controls'), body('Competitive review, conflict screening, and threshold-based escalation are required for procurement actions.'), h1('6. Control Exceptions and Escalation'), body('Any requested exception to this matrix requires written rationale, risk assessment, and approval at the next higher authority tier.'), body('Exception logs are reviewed by finance leadership and summarized for board oversight each quarter.'), h2('6.1 Exception Log Minimum Fields'), makeTable([{header:true,cells:[{text:'Field'},{text:'Requirement'}]},{cells:[{text:'Requester'},{text:'Name and role'}]},{cells:[{text:'Requested Exception'},{text:'Specific authority deviation'}]},{cells:[{text:'Risk Assessment'},{text:'Operational, legal, financial impact'}]},{cells:[{text:'Approver'},{text:'Escalated authority approver'}]},{cells:[{text:'Disposition'},{text:'Approved/Denied with rationale'}]}],[3600,5760]), h1('7. Review and Amendment'), body('Annual review required; amendments require Board majority vote and version update.'), ...sigStandard(cfg)];
  return makeDoc(cfg,doc,children);
}

function buildDocumentRetention(cfg){
  const doc={id:'04',title:'Document Retention & Records Policy'};
  const children=[...buildCover(cfg,doc), new Paragraph({children:[],pageBreakBefore:true}), h1('Purpose'), body('Defines retention, secure destruction, and legal hold controls.'), h1('Classification'), body('Records are classified by legal and operational requirements.'), h2('Permanent Records'), makeTable([{header:true,cells:[{text:'Record Type'},{text:'Retention'}]},{cells:[{text:'Articles, bylaws, board minutes, tax status letters'},{text:'Permanent'}]}],[7000,2360]), h2('7-Year Records'), makeTable([{header:true,cells:[{text:'Record Type'},{text:'Retention'}]},{cells:[{text:'Financial records, grants, personnel files'},{text:'7 years'}]}],[7000,2360]), h2('3–7 Year Records'), makeTable([{header:true,cells:[{text:'Record Type'},{text:'Retention'}]},{cells:[{text:'Email, project files, routine correspondence'},{text:'3 years'}]}],[7000,2360]), h1('Electronic Records'), body('Apply the same retention standards to digital records and backups.'), h1('Destruction Procedures'), body('Secure destruction methods and logs are required.'), h1('Litigation Hold'), body('All deletion pauses under active legal hold notice.'), h1('Records Custodian'), body('Operations designates a records custodian with annual policy review duty.'), ...sigStandard(cfg)];
  return makeDoc(cfg,doc,children);
}

function buildIPLicensing(cfg){
  const doc={id:'05',title:'Intellectual Property & Licensing Policy'};
  const children=[...buildCover(cfg,doc), new Paragraph({children:[],pageBreakBefore:true}), h1('Purpose'), body('Defines IP ownership and mission-aligned licensing standards.'), h1('Scope'), body('Applies to software, content, data outputs, trademarks, and contributions.'), h2('License Selection Table'), makeTable([{header:true,cells:[{text:'Asset Type'},{text:'Default License'},{text:'Rationale'}]},{cells:[{text:'Software'},{text:'MIT'},{text:'Public benefit interoperability'}]},{cells:[{text:'Content'},{text:'CC BY 4.0'},{text:'Attribution-based open dissemination'}]},{cells:[{text:'Data'},{text:'CC0 (where lawful)'},{text:'Maximum reuse for civic value'}]}],[2200,2200,4960]), h2('Approved License Categories'), makeTable([{header:true,cells:[{text:'Category'},{text:'Status'},{text:'Notes'}]},{cells:[{text:'Permissive'},{text:'Approved'},{text:'Preferred default'}]},{cells:[{text:'Weak copyleft'},{text:'Conditional'},{text:'Case review required'}]},{cells:[{text:'Strong copyleft'},{text:'Restricted'},{text:'Executive + legal review'}]},{cells:[{text:'Prohibited licenses'},{text:'Disallowed'},{text:'Not compatible with policy'}]}],[2200,2200,4960]), h1('Trademark'), body('CivicOS Institute name and logo are protected organizational marks.'), h1('Contributor License Agreement'), body('External contributors must execute CLA before contributions are accepted.'), h1('Third-Party Code'), body('Dependency compliance checks required for license compatibility and attribution.'), h1('Enforcement and Compliance'), body('Violations may trigger remediation, takedown, or legal escalation.'), h1('Key Contacts'), body(`${cfg.org.email_legal} · ${cfg.org.email_ops}`), ...sigStandard(cfg)];
  return makeDoc(cfg,doc,children);
}

function buildDataPrivacySecurity(cfg){
  const doc={id:'06',title:'Data, Privacy & Security Policy'};
  const children=[...buildCover(cfg,doc), new Paragraph({children:[],pageBreakBefore:true}), h1('Purpose'), body('Defines collection, processing, storage, and protection of personal data.'), h1('Collection and Minimization'), body('Collect only necessary data for stated purposes.'), h2('Data Classification Table'), makeTable([{header:true,cells:[{text:'Class'},{text:'Definition'},{text:'Examples'}]},{cells:[{text:'Public'},{text:'No material harm if disclosed'},{text:'Published reports'}]},{cells:[{text:'Internal'},{text:'Operational sensitivity'},{text:'Planning docs'}]},{cells:[{text:'Confidential'},{text:'High sensitivity'},{text:'Personnel/donor data'}]},{cells:[{text:'Restricted'},{text:'Maximum sensitivity'},{text:'Credentials/legal files'}]}],[1800,3600,3960]), h2('Lawful Basis Table'), makeTable([{header:true,cells:[{text:'Basis'},{text:'Usage'}]},{cells:[{text:'Consent'},{text:'Opt-in communications'}]},{cells:[{text:'Contract'},{text:'Service delivery obligations'}]},{cells:[{text:'Legal obligation'},{text:'Regulatory compliance'}]},{cells:[{text:'Vital interests'},{text:'Safety-critical exceptions'}]},{cells:[{text:'Public task'},{text:'Mission operations'}]},{cells:[{text:'Legitimate interests'},{text:'Balanced organizational need'}]}],[3000,6360]), h2('Data Subject Rights Table'), makeTable([{header:true,cells:[{text:'Right'},{text:'Response SLA'}]},{cells:[{text:'Access'},{text:'30 days'}]},{cells:[{text:'Rectification'},{text:'30 days'}]},{cells:[{text:'Erasure'},{text:'30 days'}]},{cells:[{text:'Portability'},{text:'30 days'}]},{cells:[{text:'Restriction'},{text:'30 days'}]},{cells:[{text:'Objection'},{text:'30 days'}]},{cells:[{text:'Complaint'},{text:'30 days'}]}],[4500,4860]), h2('Security Controls Table'), makeTable([{header:true,cells:[{text:'Control'},{text:'Implementation'}]},{cells:[{text:'MFA'},{text:'Required for privileged access'}]},{cells:[{text:'Least privilege'},{text:'Role-based access control'}]},{cells:[{text:'Encryption'},{text:'At rest and in transit'}]},{cells:[{text:'Logging'},{text:'Audit and retention controls'}]},{cells:[{text:'Incident response'},{text:'Defined escalation and recovery'}]},{cells:[{text:'Vendor review'},{text:'Third-party diligence workflow'}]}],[3500,5860]), h1('Breach Response'), body('Regulatory notice target within 72 hours where required.'), h1('Third-Party Sharing'), body('Sharing requires lawful basis and safeguards.'), h1('AI Processing'), body('Personal data is not submitted to external AI models without explicit approved legal basis.'), h1('Privacy Contact'), body(`${cfg.org.email_legal}`), ...sigStandard(cfg)];
  return makeDoc(cfg,doc,children);
}

function buildBoardMemberAgreement(cfg){
  const doc={id:'07',title:'Board Member Agreement',subtitle:'Individual Director Commitment Document'};
  const children=[...buildCover(cfg,doc), new Paragraph({children:[],pageBreakBefore:true}), h1('Director Information'), body('Director Name: ________________________________'), body('Board Role/Title: ________________________________'), h2('Service Type'), checkItem('Standard Term — 3 years per Bylaws Article III Section 3.03'), checkItem('Provisional Term — 12 months per Bylaws Article III Section 3.04'), body('Term Start Date: ___________    Term End Date: ___________'), body('Conversion to standard term eligible: ☐ Yes ☐ No'), body('Conversion requires majority Board vote prior to provisional term expiration.'), h1('Sections 1–11 Commitments'), ...['Fiduciary duties','Governance alignment','Participation and attendance','Conflict obligations','Confidentiality and legal exceptions','Financial stewardship','Public representation','Conduct and culture','Whistleblower non-retaliation','Intellectual property handling','Term renewal and transition'].map((s,i)=>body(`${i+1}. ${s}`)), h2('Conditional Provisional Block'), body('If Provisional Service Type selected: appointment maximum 12 months; conversion requires majority board vote; if term expires without conversion, service concludes without further action.'), h2('Internal Use Checklist'), ...['Orientation completed','COI disclosure form received','Security/privacy onboarding completed','Agreement filed in governance records','Term end date calendared with Board Secretary','Service type marked (Standard/Provisional)','If provisional: conversion vote calendared (Yes/No/N/A)'].map(checkItem), goldRule(), h1('Adoption and Signatures'), sigLine('Director Signature'), sigLine('Printed Name'), dateLine(), spacer(60), sigLine('Board Chair Acknowledgment'), dateLine()];
  return makeDoc(cfg,doc,children);
}

function buildWhistleblowerPolicy(cfg){
  const doc={id:'08',title:'Whistleblower Policy'};
  const children=[...buildCover(cfg,doc), new Paragraph({children:[],pageBreakBefore:true}), h1('1. Purpose'), body('Protect good-faith reporting and prohibit retaliation.'), h1('2. Scope'), body('Applies to directors, officers, employees, contractors, and volunteers.'), h1('3. Good-Faith Standard'), body('Reports must be honest and made in good faith.'), h1('4. Reporting Channels'), body('Anonymous channel: whistleblower@civicos-institute.org routed to Board Chair and one designated independent director.'), h1('5. Non-Retaliation'), body('Retaliation is prohibited and treated as a separate violation.'), h1('6. Intake Acknowledgment'), body('Anonymous reports will be logged and reviewed but may not receive acknowledgment where no contact information is available.'), h1('7. Investigation Process'), h2('7.3 Timeliness'), body('No investigation shall exceed ninety (90) calendar days without mandatory written notification to the Board Chair stating reason for delay and estimated completion date.'), h1('8. Corrective Actions'), body('Corrective action and remediation are documented and tracked.'), h1('9. Confidentiality'), body('Confidentiality maintained to the extent practicable and lawful.'), h1('10. Records Retention'), body('Records managed under retention policy and legal hold requirements.'), h1('11. Board Oversight'), body('No less than annually, at or before the fiscal year-end Board meeting.'), h1('12. Special Cases'), h2('12(a) Board member misconduct track'), body('Where substantiated against a sitting Board member, corrective action follows Bylaws Article III Section 3.05 with subject member recusal from deliberation and voting.'), h1('13. Non-Waiver'), body('No waiver outside formal board action.'), h1('14. Adoption and Review'), body('Policy owner and review cadence documented by board governance process.'), goldRule(), h1('Adoption and Signatures'), sigLine('Board Chair'), dateLine(), spacer(60), sigLine('Executive Director'), dateLine()];
  return makeDoc(cfg,doc,children);
}

function buildCompensationReview(cfg){
  const doc={id:'09',title:'Compensation Review Policy'};
  const children=[...buildCover(cfg,doc), new Paragraph({children:[],pageBreakBefore:true}), h1('1. Purpose'), body('Defines compensation governance for ED, officers, and key employees.'), h1('2. Scope'), body('Applies to compensation determinations and review cycles.'), h1('3. Governing Standard'), body('Compensation must be reasonable and documented.'), h1('4. Rebuttable Presumption Procedure'), makeTable([{header:true,cells:[{text:'Element'},{text:'Requirement'}]},{cells:[{text:'Independent approval'},{text:'Disinterested authorized body approval'}]},{cells:[{text:'Comparability data'},{text:'Market benchmarks and documented references'}]},{cells:[{text:'Contemporaneous documentation'},{text:'Minutes and written rationale'}]}],[3200,6160]), h1('5. Approval Authority'), body('Approval levels align with delegation and board governance controls.'), h1('6. Conflict and Recusal'), body('Conflicted individuals disclose and recuse.'), h1('7. Annual Review Cycle'), body('Annual review aligned to budget and fiscal cycle.'), h1('8. Mid-Cycle Adjustments'), body('Requests initiated by the Executive Director for their own compensation review must be submitted in writing to the Board Chair, who convenes the independent review process.'), h1('9. Excess Benefit Prevention'), body('Escalation and remediation controls apply to potential excess benefit events.'), body('Note for legal review: Excess benefit transactions under IRC 4958 may carry excise tax exposure on the disqualified person. Legal counsel should advise whether explicit IRC 4958 citation is appropriate in this policy or should remain in separate legal guidance.',{italic:true}), h1('10. Recordkeeping'), body('Comparability and approval records retained per records policy.'), h1('11. Board Member Compensation'), body('Disinterested review required for any board member compensation action.'), body('Note for legal review: Confirm whether Florida nonprofit law imposes additional constraints on director compensation beyond Bylaws provisions.',{italic:true}), h1('12. Coordination with Other Policies'), body('Read in conjunction with bylaws, COI, and delegation matrix.'), h1('13. Review and Amendment'), body('Board may amend per formal governance process.'), h1('14. Adoption'), body('Adoption and next review dates recorded in governance records.'), h2('Comparability Data Sources'), makeTable([{header:true,cells:[{text:'Source'},{text:'Use'}]},{cells:[{text:'Form 990 peer organizations'},{text:'Role-aligned compensation ranges'}]},{cells:[{text:'Compensation surveys'},{text:'Market benchmarking'}]},{cells:[{text:'Independent studies'},{text:'High-stakes compensation decisions'}]},{cells:[{text:'Recruiting market data'},{text:'Retention and competitiveness context'}]}],[3800,5560]), goldRule(), h1('Adoption and Signatures'), sigLine('Board Chair'), dateLine(), spacer(60), sigLine('Compensation Committee Chair'), dateLine(), spacer(60), sigLine('Executive Director'), dateLine()];
  return makeDoc(cfg,doc,children);
}

function makeDoc(cfg,meta,children){
  const d=cfg.documents[meta.id]||{version:'1.0'};
  return new Document({
    numbering:{config:[
      {reference:'bullets',levels:[{level:0,format:LevelFormat.BULLET,text:'•',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:560,hanging:280}}}}]},
      {reference:'checkboxes',levels:[{level:0,format:LevelFormat.BULLET,text:'☐',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:560,hanging:280}}}}]},
    ]},
    styles:{default:{document:{run:{font:FONT.SERIF,size:22,color:COLOR.TEXT}}}},
    sections:[{properties:{page:{size:{width:PAGE.WIDTH,height:PAGE.HEIGHT},margin:{top:PAGE.MARGIN,right:PAGE.MARGIN,bottom:PAGE.MARGIN,left:PAGE.MARGIN}}},headers:{default:buildHeader(cfg,meta.title)},footers:{default:buildFooter(cfg,meta.id,d.version||'1.0')},children}]
  });
}

async function writeDoc(docId,cfg){
  const builders={AOI:buildArticlesOfIncorporation,'01':buildBylaws,'02':buildConflictOfInterest,'03':buildDelegationOfAuthority,'04':buildDocumentRetention,'05':buildIPLicensing,'06':buildDataPrivacySecurity,'07':buildBoardMemberAgreement,'08':buildWhistleblowerPolicy,'09':buildCompensationReview};
  const d=cfg.documents[docId]||{}; const ver=d.version||'1.0';
  const outName=`${docId}_${DOC_META[docId].short}_CivicOS_Institute_v${ver}.docx`; const outPath=path.join(OUT_DIR,outName);
  if(fs.existsSync(outPath)) fs.copyFileSync(outPath,path.join(ARCHIVE_DIR,`${docId}_v${ver}_${Date.now()}.docx`));
  const buffer=await Packer.toBuffer(builders[docId](cfg));
  fs.writeFileSync(outPath,buffer);
  return outPath;
}

let _soffice=null;
function hasSoffice(){ if(_soffice!==null) return _soffice; _soffice=spawnSync('soffice',['--version']).status===0; return _soffice; }
function convert(docx){ const outPdf=path.join(PDF_DIR,path.basename(docx).replace(/\.docx$/i,'.pdf')); if(!hasSoffice()) return {ok:false,skip:true,pdf:outPdf,error:'PDF generation skipped: soffice not found. Install LibreOffice to enable PDF output.'}; try{execFileSync('soffice',['--headless','--convert-to','pdf',docx,'--outdir',PDF_DIR],{stdio:'pipe'}); return {ok:fs.existsSync(outPdf),skip:false,pdf:outPdf,error:fs.existsSync(outPdf)?null:'PDF not produced'};}catch(e){return {ok:false,skip:false,pdf:outPdf,error:`PDF conversion failed: ${e.message}`};}}

function buildZip(cfg,docx,pdf){
  const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'govsuite-')); const root=path.join(tmp,'CivicOS_Governance_Suite'); const ddir=path.join(root,'docx'); const pdir=path.join(root,'pdf');
  fs.mkdirSync(ddir,{recursive:true}); fs.mkdirSync(pdir,{recursive:true});
  docx.forEach(p=>fs.existsSync(p)&&fs.copyFileSync(p,path.join(ddir,path.basename(p))));
  pdf.forEach(p=>fs.existsSync(p)&&fs.copyFileSync(p,path.join(pdir,path.basename(p))));
  fs.writeFileSync(path.join(root,'README.txt'),`CivicOS Institute Governance Document Suite\nVersion: ${(cfg.documents['AOI']||{}).version||'1.0'}\nGenerated: ${new Date().toISOString()}\nStatus: All documents DRAFT — Pending Board Adoption\nContact: NCerbone@civicos-institute.org\n`);
  if(fs.existsSync(SUITE_ZIP)) fs.rmSync(SUITE_ZIP,{force:true});
  execFileSync('zip',['-qr',SUITE_ZIP,'CivicOS_Governance_Suite'],{cwd:tmp});
  fs.rmSync(tmp,{recursive:true,force:true});
}

function parseArgs(argv){ if(argv.length===1&&argv[0]==='--all') return {mode:'all'}; if(argv.length===2&&argv[0]==='--doc') return {mode:'doc',docId:argv[1]}; return null; }

async function main(){
  const args=parseArgs(process.argv.slice(2)); if(!args){usage();process.exit(0);} ensure();
  let cfg; try{cfg=loadConfig();}catch(e){console.error(`ESCALATION REQUIRED: ${e.message}. Notify NCerbone@civicos-institute.org`);process.exit(1);} 
  const ids=args.mode==='all'?Object.keys(DOC_META):[args.docId]; if(ids.some(x=>!DOC_META[x])){usage();process.exit(0);} 
  const docx=[]; const errors=[];
  for(const id of ids){ try{ docx.push(await writeDoc(id,cfg)); }catch(e){ errors.push(`${id}:${e.message}`);} }
  const pdfStatus=[]; let warned=false;
  for(const id of ids){ const d=cfg.documents[id]||{}; const p=path.join(OUT_DIR,`${id}_${DOC_META[id].short}_CivicOS_Institute_v${d.version||'1.0'}.docx`); const r=convert(p); if(r.skip&&!warned){console.log(r.error); warned=true;} pdfStatus.push({id,...r}); }
  try{buildZip(cfg,docx,pdfStatus.filter(x=>x.ok).map(x=>x.pdf));}catch(e){errors.push(`suite_zip:${e.message}`);} 
  const sizes=docx.filter(p=>fs.existsSync(p)).map(p=>({p,size:fs.statSync(p).size}));
  const uniform=(sizes.length>1)?(Math.max(...sizes.map(x=>x.size))-Math.min(...sizes.map(x=>x.size))<=200):false; if(uniform) errors.push('uniform_size_check_failed:all_docs_within_200_bytes');
  const entry={timestamp:new Date().toISOString(),trigger:args.mode==='all'?'--all':`--doc ${args.docId}`,docs_generated:docx.map(p=>path.basename(p).split('_')[0]),config_version:'1.0',operator:'Burt',status:errors.length?'error':'ok',errors,pdf_generated:pdfStatus.filter(x=>x.ok).map(x=>x.id),pdf_missing:pdfStatus.filter(x=>!x.ok).map(x=>x.id),pdf_errors:pdfStatus.filter(x=>x.error).map(x=>x.error)};
  fs.appendFileSync(LOG_PATH,JSON.stringify(entry)+'\n');
  console.log('Generation summary'); console.log(`- Trigger: ${entry.trigger}`); console.log(`- Docs generated: ${docx.length}`); sizes.forEach(x=>console.log(`  - ${path.relative(ROOT,x.p)} (${x.size} bytes)`)); console.log(`- PDFs generated: ${entry.pdf_generated.length}/${pdfStatus.length}`); console.log(`- Suite ZIP: ${path.relative(ROOT,SUITE_ZIP)} ${fs.existsSync(SUITE_ZIP)?'(ok)':'(missing)'}`); console.log(`- Status: ${entry.status}`); if(errors.length){errors.forEach(e=>console.log(`  ! ${e}`)); process.exit(1);} 
}

main().catch(e=>{console.error(e);process.exit(1)});
