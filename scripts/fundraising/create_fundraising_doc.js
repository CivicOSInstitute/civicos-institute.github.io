#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT = path.resolve(__dirname, '../..');
const cfgPath = path.join(__dirname, 'fundraising_config.json');
const outDir = path.join(ROOT, 'generated', 'fundraising');

function nowStamp() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${y}${m}${day}-${hh}${mm}`;
}

function modeTitle(mode){
  if(mode==='donor-ask') return 'DONOR FUNDRAISING REQUEST';
  if(mode==='corporate-sponsorship') return 'CORPORATE SPONSORSHIP PROPOSAL';
  return 'FUNDRAISING PROPOSAL';
}

function modeFundingType(mode){
  if(mode==='donor-ask') return 'Donor Ask';
  if(mode==='corporate-sponsorship') return 'Corporate Sponsorship';
  return 'Grant';
}

function render(cfg, input, mode) {
  const req = input.request || {};
  const prog = input.program || {};
  const budget = input.budget || {};
  const kpi = input.kpi || {};

  const title = req.title || '[PROJECT OR REQUEST TITLE]';
  const amount = req.amount || '[$ AMOUNT]';
  const period = req.period || '[START DATE] to [END DATE]';
  const funder = req.funder || '[FUNDER/DONOR/SPONSOR NAME]';

  return `# ${cfg.org.name.toUpperCase()} ${modeTitle(mode)}

**Document ID:** FR-${cfg.defaults.fiscal_year}-[##]  
**Version:** ${cfg.document.version}  
**Status:** ${cfg.document.status}  
**Prepared By:** ${cfg.org.contact_name}, ${cfg.org.contact_title}  
**Date:** [MONTH DAY, YEAR]  
**Funding Type:** ${req.type || modeFundingType(mode)}  
**Target Funder:** ${funder}

---

## ARTICLE I: REQUEST SUMMARY

### Section 1.01: Funding Request Title
${title}

### Section 1.02: Total Amount Requested
${amount}

### Section 1.03: Funding Period
${period}

### Section 1.04: Geographic Focus
${req.geography || cfg.defaults.geography}

### Section 1.05: One-Paragraph Summary
${req.summary || '[Provide concise summary of request, beneficiaries, and expected outcomes.]'}

---

## ARTICLE II: ORGANIZATION PROFILE

### Section 2.01: Legal and Organizational Information
- Legal Name: ${cfg.org.name}
- State: ${cfg.org.state}
- Primary Service City: ${cfg.org.city}
- Website: ${cfg.org.website}
- Primary Contact: ${cfg.org.contact_name}, ${cfg.org.contact_title}
- Email: ${cfg.org.contact_email}

### Section 2.02: Mission Alignment Statement
${prog.mission_alignment || '[How this request advances mission and funder priorities.]'}

### Section 2.03: Organizational Capacity
${prog.capacity || '[Leadership, partners, and delivery capacity.]'}

---

## ARTICLE III: PROGRAM DESIGN AND OUTCOMES

### Section 3.01: Program Goal
${prog.goal || '[Single clear goal statement.]'}

### Section 3.02: Objectives
1. ${prog.obj1 || '[Objective 1]'}
2. ${prog.obj2 || '[Objective 2]'}
3. ${prog.obj3 || '[Objective 3]'}

### Section 3.03: KPI Targets (12-Month)
- Residents Engaged: ${kpi.residents || '[TARGET]'}
- Active Participants: ${kpi.participants || '[TARGET]'}
- Community Initiatives Supported: ${kpi.initiatives || '[TARGET]'}
- Partner Organizations Activated: ${kpi.partners || '[TARGET]'}
- Civic Actions Completed: ${kpi.actions || '[TARGET]'}

---

## ARTICLE IV: BUDGET AND USE OF FUNDS

### Section 4.01: Line-Item Budget Summary
- Personnel/Facilitation: ${budget.personnel || '[$]'}
- Program Operations: ${budget.operations || '[$]'}
- Outreach/Communications: ${budget.outreach || '[$]'}
- Evaluation/Reporting: ${budget.evaluation || '[$]'}
- Administrative/Indirect: ${budget.indirect || '[$]'}
- **Total:** ${budget.total || amount}

### Section 4.02: Budget Narrative
${budget.narrative || '[Explain necessity and reasonableness by category.]'}

---

## ARTICLE V: ELIGIBILITY, COMPLIANCE, AND SUBMISSION CONTROL

### Section 5.01: Eligibility Confirmation
- Geography Eligible: ${req.geo_eligible || '[YES/NO]'}
- Org Type Eligible: ${req.org_eligible || '[YES/NO]'}
- Fiscal Sponsor Allowed: ${req.fiscal_sponsor || '[YES/NO/NA]'}
- Deadline Met: ${req.deadline_met || '[YES/NO]'}

### Section 5.02: Final Submission Record
- Submitted By: [NAME]
- Submission Date/Time: [TIMESTAMP]
- Confirmation Number: [ID]
- Follow-Up Date: [DATE]
`;
}

function toDocx(mdPath){
  const docxPath = mdPath.replace(/\.md$/, '.docx');
  try {
    execSync(`pandoc "${mdPath}" -o "${docxPath}"`, { stdio: 'ignore' });
    return docxPath;
  } catch(e) {
    return null;
  }
}

function main() {
  const inputPath = process.argv[2];
  const mode = (process.argv[3] || 'grant').trim();
  const exportDocx = (process.argv[4] || '').includes('--docx');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  const input = inputPath ? JSON.parse(fs.readFileSync(path.resolve(process.cwd(), inputPath), 'utf8')) : {};

  fs.mkdirSync(outDir, { recursive: true });
  const output = render(cfg, input, mode);
  const outFile = path.join(outDir, `${mode}-proposal-${nowStamp()}.md`);
  fs.writeFileSync(outFile, output);
  console.log(outFile);

  if (exportDocx) {
    const docx = toDocx(outFile);
    if (docx) console.log(docx);
    else console.log('DOCX export skipped (pandoc not available)');
  }
}

main();
