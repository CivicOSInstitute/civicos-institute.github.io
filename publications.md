---
layout: default
title: Publications & Research
permalink: /publications/
---

# Publications & Research

CivicOS Institute produces research, technical specifications, and policy analysis to advance open civic infrastructure. Our work bridges technical implementation and policy impact.

---

## Free AI Learning Kit (Now Available)

We are distributing the **CivicOS AI Learning Kit** for free to help non-technical and technical learners build practical AI literacy and readiness.

### Registration Required for Download Access

<div class="guide-gate-wrap">
  <h3>Download the Free Guide</h3>
  <p class="guide-subhead">Enter your information below to access your free copy. We’ll keep you updated on new resources from CivicOS Institute.</p>

  <form id="guideRegistrationForm" action="https://formspree.io/f/mbdaobda" method="POST" novalidate>
    <input type="hidden" name="_subject" value="Free Guide Download — New Registration">
    <input type="hidden" name="_next" value="https://civicos-institute.org/thank-you-guide">
    <input type="text" name="_gotcha" style="display:none">

    <div class="guide-field">
      <label for="full_name">Full Name</label>
      <input id="full_name" name="full_name" type="text" placeholder="Your full name" required minlength="2">
      <div class="guide-error" id="err_full_name"></div>
    </div>

    <div class="guide-field">
      <label for="email">Email Address</label>
      <input id="email" name="email" type="email" placeholder="your@email.com" required>
      <div class="guide-error" id="err_email"></div>
    </div>

    <div class="guide-field">
      <label for="role">Role / Title</label>
      <input id="role" name="role" type="text" placeholder="e.g. Teacher, Administrator, Curriculum Director" required>
      <div class="guide-error" id="err_role"></div>
    </div>

    <div class="guide-field">
      <label for="organization">Organization</label>
      <input id="organization" name="organization" type="text" placeholder="School, district, or institution name" required>
      <div class="guide-error" id="err_organization"></div>
    </div>

    <button type="submit" id="guideSubmitBtn" disabled>Get Free Access →</button>
    <p class="guide-privacy">We respect your privacy. Your information is never sold or shared with third parties.</p>
  </form>
</div>

<style>
  .guide-gate-wrap { background:#FFFFFF; border:1px solid #D0D5DD; border-radius:8px; padding:32px; max-width:560px; box-shadow:0 2px 8px rgba(0,0,0,0.08); margin:18px 0; }
  .guide-gate-wrap h3 { margin-top:0; color:#1B2B4B; font-family:Arial,sans-serif; }
  .guide-subhead { margin-bottom:20px; }
  .guide-field { margin-bottom:14px; }
  .guide-field label { display:block; font-family:Arial,sans-serif; font-size:14px; font-weight:700; color:#1B2B4B; margin-bottom:6px; }
  .guide-field input { width:100%; border:1px solid #D0D5DD; border-radius:4px; padding:10px 14px; font-family:Georgia,serif; font-size:15px; }
  .guide-field input:focus { border-color:#1B2B4B; outline:none; }
  #guideSubmitBtn { background:#1B2B4B; color:white; font-family:Arial,sans-serif; font-weight:700; font-size:16px; padding:12px 24px; border-radius:4px; width:100%; border:none; cursor:pointer; transition:background .2s ease; }
  #guideSubmitBtn:hover:not([disabled]) { background:#B8963E; }
  #guideSubmitBtn[disabled] { opacity:.55; cursor:not-allowed; }
  .guide-privacy { font-family:Arial,sans-serif; font-size:12px; color:#6B7280; text-align:center; margin-top:12px; }
  .guide-error { color:#DC2626; font-family:Arial,sans-serif; font-size:12px; min-height:14px; margin-top:4px; }
  @media (max-width:480px){ .guide-gate-wrap{padding:20px;} }
</style>

<script>
(function(){
  const form = document.getElementById('guideRegistrationForm');
  if(!form) return;
  const fields = {
    full_name: document.getElementById('full_name'),
    email: document.getElementById('email'),
    role: document.getElementById('role'),
    organization: document.getElementById('organization')
  };
  const errs = {
    full_name: document.getElementById('err_full_name'),
    email: document.getElementById('err_email'),
    role: document.getElementById('err_role'),
    organization: document.getElementById('err_organization')
  };
  const submitBtn = document.getElementById('guideSubmitBtn');

  const emailOk = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

  function validateField(name){
    const v = (fields[name].value || '').trim();
    errs[name].textContent = '';
    if(!v){ errs[name].textContent = 'This field is required'; return false; }
    if(name === 'full_name' && v.length < 2){ errs[name].textContent = 'Please enter at least 2 characters'; return false; }
    if(name === 'email' && !emailOk(v)){ errs[name].textContent = 'Please enter a valid email'; return false; }
    return true;
  }

  function updateState(){
    const ok = Object.keys(fields).every(k => {
      const v=(fields[k].value||'').trim();
      if(!v) return false;
      if(k==='full_name' && v.length<2) return false;
      if(k==='email' && !emailOk(v)) return false;
      return true;
    });
    submitBtn.disabled = !ok;
  }

  Object.keys(fields).forEach(k => {
    fields[k].addEventListener('input', () => { validateField(k); updateState(); });
    fields[k].addEventListener('blur', () => validateField(k));
  });

  form.addEventListener('submit', function(e){
    let ok = true;
    Object.keys(fields).forEach(k => { if(!validateField(k)) ok = false; });
    if(!ok){ e.preventDefault(); return false; }
    return true;
  });

  updateState();
})();
</script>

**License/Use:** Free to share for educational use with attribution to CivicOS Institute. No third-party branded course materials are included.

---

## Technical Specifications

### Open Civic Specifications v2.0
**Published:** November 2025  
**Type:** Technical Standard  
**License:** Apache 2.0

The foundational technical specification for the CivicOS ecosystem. Defines open standards for civic interoperability, workflow architectures, and the Logos Engine reference framework.

[View on GitHub](https://github.com/CivicOSInstitute/open-civic-specs)

**Key Topics:**
- Civic data interoperability standards
- Workflow architecture patterns
- Open-source reference implementations
- Municipal integration frameworks

---

## White Papers (Coming Soon)

### The Cost of Opaque Government: A Florida Case Study
**Expected:** March 2026  
**Type:** Policy Analysis

An analysis of FOIA request costs, processing delays, and information asymmetry across Florida municipalities. Quantifies the economic and democratic cost of closed government systems.

**Get early access:** [Subscribe to our newsletter](#newsletter)

---

### 5 Ways AI Can Democratize Local Government
**Expected:** April 2026  
**Type:** Policy Brief

Practical, no-code approaches to using AI for transparency, accessibility, and civic engagement. Includes implementation roadmap for municipalities of all sizes.

**Get early access:** [Subscribe to our newsletter](#newsletter)

---

### Open Data Standards for Municipal Transparency
**Expected:** May 2026  
**Type:** Technical White Paper

A comparative analysis of existing open data standards (Socrata, CKAN, Open311) and recommendations for municipal implementation. Includes cost-benefit analysis and migration pathways for legacy systems.

**Get early access:** [Subscribe to our newsletter](#newsletter)

---

## Commentary & Op-Eds

*Watch this space for published commentary on civic technology, government transparency, and open-source infrastructure.*

---

## Research Partnerships

CivicOS Institute collaborates with:
- Academic institutions studying civic technology
- Municipal governments piloting open-source tools
- Nonprofit organizations advancing government transparency

**Interested in collaborating?** [Contact us](mailto:research@civicos-institute.org)

---

## Get Research Updates

### Newsletter Signup

Be the first to receive our white papers, policy briefs, and research findings.

<form action="https://formspree.io/f/mbdaobda" method="POST">
  <label>
    Email:
    <input type="email" name="email" required placeholder="you@example.com">
  </label>
  <br><br>
  <label>
    First Name:
    <input type="text" name="first_name" placeholder="Optional">
  </label>
  <br><br>
  <label>
    Organization:
    <input type="text" name="organization" placeholder="Optional">
  </label>
  <br><br>
  <label>
    I'm interested in:
    <br>
    <input type="checkbox" name="interests" value="civic_tech"> Civic Technology
    <br>
    <input type="checkbox" name="interests" value="policy"> Policy & Governance
    <br>
    <input type="checkbox" name="interests" value="open_source"> Open Source Development
    <br>
    <input type="checkbox" name="interests" value="grants"> Grant Opportunities
  </label>
  <br><br>
  <button type="submit">Subscribe</button>
</form>

---

## Open Source

All CivicOS Institute research and specifications are open source:

- [Technical Specifications](https://github.com/CivicOSInstitute/open-civic-specs)
- [Research Repository](https://github.com/CivicOSInstitute/research)
- [Documentation](https://github.com/CivicOSInstitute/docs)

---

*Last updated: February 2026*
