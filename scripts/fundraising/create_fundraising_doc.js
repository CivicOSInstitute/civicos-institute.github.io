#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

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

function render(cfg, input) {
  const req = input.request || {};
  const prog = input.program || {};
  const budget = input.budget || {};
  const kpi = input.kpi || {};

  const title = req.title || '[PROJECT OR REQUEST TITLE]';
  const amount = req.amount || '[$ AMOUNT]';
  const period = req.period || '[START DATE] to [END DATE]';
  const funder = req.funder || '[FUNDER NAME]';

  return `# ${cfg.org.name.toUpperCase()} FUNDRAISING PROPOSAL

**Document ID:** FR-${cfg.defaults.fiscal_year}-[##]  
**Version:** ${cfg.document.version}  
**Status:** ${cfg.document.status}  
**Prepared By:** ${cfg.org.contact_name}, ${cfg.org.contact_title}  
**Date:** [MONTH DAY, YEAR]  
**Funding Type:** ${req.type || cfg.defaults.funding_type}  
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

## ARTICLE III: PROBLEM STATEMENT AND NEED

### Section 3.01: Community Need
${prog.need || '[Define issue in measurable terms.]'}

### Section 3.02: Target Population
${prog.population || '[Who benefits, with local and underserved emphasis.]'}

### Section 3.03: Why Now
${prog.urgency || '[Urgency and timing rationale.]'}

---

## ARTICLE IV: PROGRAM DESIGN

### Section 4.01: Program Goal
${prog.goal || '[Single clear goal statement.]'}

### Section 4.02: Objectives
1. ${prog.obj1 || '[Objective 1]'}
2. ${prog.obj2 || '[Objective 2]'}
3. ${prog.obj3 || '[Objective 3]'}

### Section 4.03: Activities and Workplan
- Phase 1: ${prog.phase1 || '[DATES — ACTIVITIES]'}
- Phase 2: ${prog.phase2 || '[DATES — ACTIVITIES]'}
- Phase 3: ${prog.phase3 || '[DATES — ACTIVITIES]'}

---

## ARTICLE V: OUTCOMES AND MEASUREMENT

### Section 5.01: KPI Targets (12-Month)
- Residents Engaged: ${kpi.residents || '[TARGET]'}
- Active Participants: ${kpi.participants || '[TARGET]'}
- Community Initiatives Supported: ${kpi.initiatives || '[TARGET]'}
- Partner Organizations Activated: ${kpi.partners || '[TARGET]'}
- Civic Actions Completed: ${kpi.actions || '[TARGET]'}

### Section 5.02: Measurement Methods
${kpi.methods || '[Attendance logs, partner reports, surveys, quarterly review.]'}

### Section 5.03: Reporting Cadence
${kpi.reporting || cfg.defaults.reporting_cadence}

---

## ARTICLE VI: BUDGET AND USE OF FUNDS

### Section 6.01: Line-Item Budget Summary
- Personnel/Facilitation: ${budget.personnel || '[$]'}
- Program Operations: ${budget.operations || '[$]'}
- Outreach/Communications: ${budget.outreach || '[$]'}
- Evaluation/Reporting: ${budget.evaluation || '[$]'}
- Administrative/Indirect: ${budget.indirect || '[$]'}
- **Total:** ${budget.total || amount}

### Section 6.02: Budget Narrative
${budget.narrative || '[Explain necessity and reasonableness by category.]'}

---

## ARTICLE VII: ELIGIBILITY AND COMPLIANCE CHECK

### Section 7.01: Eligibility Confirmation
- Geography Eligible: ${req.geo_eligible || '[YES/NO]'}
- Org Type Eligible: ${req.org_eligible || '[YES/NO]'}
- Fiscal Sponsor Allowed: ${req.fiscal_sponsor || '[YES/NO/NA]'}
- Deadline Met: ${req.deadline_met || '[YES/NO]'}

### Section 7.02: Required Attachments Checklist
- [ ] Organization One-Pager
- [ ] Project Narrative
- [ ] Budget + Budget Narrative
- [ ] IRS Determination Letter or Fiscal Sponsor Letter
- [ ] Board/Leadership List
- [ ] Recent Financials (if required)

---

## ARTICLE VIII: APPROVAL AND SUBMISSION CONTROL

### Section 8.01: Internal Review
- Program Lead Review: [DATE / NAME]
- Budget Review: [DATE / NAME]
- Executive Review: [DATE / NAME]

### Section 8.02: Final Submission Record
- Submitted By: [NAME]
- Submission Date/Time: [TIMESTAMP]
- Confirmation Number: [ID]
- Follow-Up Date: [DATE]
`;
}

function main() {
  const inputPath = process.argv[2];
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  const input = inputPath ? JSON.parse(fs.readFileSync(path.resolve(process.cwd(), inputPath), 'utf8')) : {};

  fs.mkdirSync(outDir, { recursive: true });
  const output = render(cfg, input);
  const outFile = path.join(outDir, `fundraising-proposal-${nowStamp()}.md`);
  fs.writeFileSync(outFile, output);
  console.log(outFile);
}

main();
