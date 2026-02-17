---
layout: default
title: IP & Licensing Policy
permalink: /governance/ip-licensing-policy/
---

# Intellectual Property & Licensing Policy

**Document Number:** 05  
**Version:** 1.0  
**Effective Date:** [DATE]  
**Last Reviewed:** [DATE]  
**Approved By:** [BOARD/EXECUTIVE BODY]  

---

## 1. Purpose and Scope

### 1.1 Purpose

This Intellectual Property & Licensing Policy establishes guidelines for the creation, protection, management, and licensing of intellectual property assets for [ORGANIZATION NAME] ("Organization"). This policy ensures that IP assets are properly identified, protected, and leveraged to advance the Organization's mission while respecting the rights of others and complying with open source community norms.

### 1.2 Scope

This policy applies to:

- **All Personnel:** Board members, officers, employees, volunteers, contractors, interns, and contributors
- **All IP Types:** Copyrights, trademarks, patents, trade secrets, and proprietary information
- **All Activities:** Research, development, content creation, software development, and collaboration
- **All Works:** Created during organizational activities, using organizational resources, or within scope of engagement

---

## 2. IP Ownership Framework

### 2.1 Work-for-Hire and Assignment

**Employee-Created IP:**
All intellectual property created by employees within the scope of their employment is the exclusive property of the Organization. This includes, but is not limited to:

- Software code and documentation
- Research findings and publications
- Educational materials and curricula
- Designs, graphics, and multimedia content
- Processes, methodologies, and know-how
- Data sets and databases

**Contractor-Created IP:**
All contractor engagements must include explicit IP assignment clauses ensuring Organization ownership of deliverables. Standard contract language requires:

- Assignment of all IP rights in deliverables
- License to underlying pre-existing IP incorporated into deliverables
- Waiver of moral rights where applicable
- Cooperation in registration and enforcement

**Volunteer and Contributor IP:**
Volunteers and external contributors must execute a Contributor License Agreement (CLA) or equivalent assignment before contributions are accepted. See Section 6 for CLA requirements.

### 2.2 Pre-Existing IP

Personnel retain ownership of IP developed:
- Prior to engagement with Organization
- Outside scope of employment/engagement
- Without use of organizational resources
- Unrelated to organizational mission or activities

Personnel must disclose pre-existing IP that may relate to organizational work to avoid conflicts.

### 2.3 Joint Development

When IP is developed jointly with third parties:

- Execute joint development agreement before work commences
- Define ownership splits, licensing rights, and commercialization
- Establish decision-making authority for enforcement and licensing
- Document each party's contributions

---

## 3. Open Source Licensing Policy

### 3.1 Philosophy and Preferences

The Organization is committed to open source principles and supports broad access to its innovations. Our licensing philosophy prioritizes:

1. **Mission advancement** over commercial restrictions
2. **Adoption and impact** through permissive terms
3. **Community collaboration** through standard licenses
4. **Attribution** to recognize contributions

### 3.2 License Selection Framework

**Tier 1: Preferred Licenses (Default)**

| License | Use Case | Requirements |
|---------|----------|--------------|
| **MIT** | Software libraries, tools, standalone applications | Attribution only |
| **Apache 2.0** | Larger software projects, enterprise-grade tools | Attribution + patent grant |
| **CC BY 4.0** | Documentation, educational content, research | Attribution only |
| **CC0** | Data sets, reference implementations, where attribution impractical | No requirements (public domain dedication) |

**Tier 2: Acceptable with Justification**

| License | Use Case | Considerations |
|---------|----------|----------------|
| **BSD 2/3-Clause** | Software | Similar to MIT; acceptable alternative |
| **GPL v3** | Software requiring copyleft derivatives | Requires legal review; contagion risk assessment |
| **LGPL** | Libraries where copyleft of derivatives desired | Linking exceptions acceptable |
| **CC BY-SA** | Content requiring share-alike derivatives | For community content projects |
| **ODbL** | Open databases | For collaboratively maintained data |

**Tier 3: Prohibited or Restricted**

| License | Status | Rationale |
|---------|--------|-----------|
| **GPL v2 only** | Avoid | No patent protection; compatibility issues |
| **AGPL** | Prohibited | Network use triggers copyleft; mission conflict |
| **Proprietary** | Prohibited | Organizational commitment to open source |
| **CC BY-NC / -ND** | Discouraged | Non-commercial restrictions limit mission impact |
| **Custom licenses** | Requires approval | Complexity and incompatibility risks |

### 3.3 License Selection Process

**Default Path (No Legal Review Required):**
1. Evaluate whether Tier 1 license meets needs
2. If yes, apply MIT (software) or CC BY 4.0 (content)
3. Document license choice in project README

**Escalation Path (Requires Legal Review):**
1. Tier 2 license under consideration
2. Multiple license types in single project
3. Mixed proprietary/open source components
4. Third-party code with conflicting licenses

**Approval Authority:**
- [DESIGNATED TECHNICAL LEAD]: Tier 1 licenses
- [DESIGNATED LEGAL COUNSEL]: Tier 2 licenses
- Board of Directors: Tier 3 licenses or exceptions

### 3.4 Dual Licensing

Dual licensing (offering same code under multiple licenses) requires:

- Legal counsel review of compatibility
- Board approval for commercial licensing track
- Clear documentation of terms for each license
- Contributor consent for dual-licensed contributions

### 3.5 License Application Requirements

Every open source release must include:

```
1. LICENSE file with full license text
2. Copyright notice in README and source headers
3. NOTICE file for Apache 2.0 or attribution-required licenses
4. CONTRIBUTING.md with CLA requirements
5. Code of Conduct reference
```

**Standard Copyright Header:**
```
Copyright [YEAR] [ORGANIZATION NAME]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 4. Proprietary IP Protection

### 4.1 Trademark Policy

**Trademark Portfolio:**
The Organization protects its brand through trademark registration and proper use guidelines.

| Element | Status | Registration |
|---------|--------|--------------|
| [ORGANIZATION NAME] | [Primary mark] | [JURISDICTIONS] |
| [LOGO] | [Visual mark] | [JURISDICTIONS] |
| [PRODUCT NAMES] | [Product marks] | [STATUS] |

**Permitted Use (by Others):**
- Reference to Organization in factual, non-trademark manner
- Nominative fair use in comparative or descriptive contexts
- Use under express license or partnership agreement

**Prohibited Use:**
- Use likely to cause confusion with Organization
- Use implying endorsement not granted
- Use in domain names without authorization
- Use of confusingly similar marks

**Trademark Licensing:**
- License agreements required for trademark use
- Quality control provisions required
- Termination for breach or brand harm
- Geographic and scope limitations

### 4.2 Patent Policy

**Patent Strategy:**
The Organization generally avoids patenting innovations, preferring publication and open source release to establish prior art. Patent applications require Board approval and are only pursued when:

- Significant defensive value against patent trolls
- Strategic partnership requires patent protection
- Commercial licensing strategy approved

**Patent Pledge:**
Any Organization patents are licensed royalty-free for:
- Open source implementations
- Non-commercial research and education
- Products furthering Organization mission

**Invention Disclosure:**
Personnel must disclose potentially patentable inventions to [DESIGNATED IP OFFICER] within 30 days of conception.

### 4.3 Trade Secret Protection

**Protected Information:**
- Donor lists and contact information
- Fundraising strategies and donor research
- Unpublished research findings
- Proprietary methodologies (if not open sourced)
- Financial projections and strategic plans
- Personnel records

**Protection Measures:**
- Marking: "CONFIDENTIAL - [ORGANIZATION NAME]"
- Access controls: Role-based, need-to-know
- NDAs required for external disclosure
- Secure storage and transmission
- Annual trade secret inventory

**Duration:**
Trade secrets protected indefinitely while maintaining confidentiality. Upon public disclosure, protection terminates.

---

## 5. Commercial Use Guidelines

### 5.1 Philosophy

The Organization encourages commercial use of its open source outputs to maximize mission impact. Commercial users are welcome and supported.

### 5.2 Permitted Commercial Use

Without restriction, commercial entities may:

- Use Organization software in commercial products
- Integrate Organization content into commercial offerings
- Modify and redistribute under applicable license terms
- Build consulting or support businesses around Organization projects
- Create proprietary derivative works (under permissive licenses)

### 5.3 Commercial Use with Attribution Requirements

Commercial users must:

- Provide attribution as required by license
- Not remove copyright notices
- Include license text in distributions
- Not use Organization trademarks without authorization
- Comply with notice requirements (Apache 2.0)

### 5.4 Prohibited Commercial Activities

Commercial entities may NOT:

- Use Organization trademarks as their own
- Imply Organization endorsement without written consent
- Remove or alter attribution requirements
- Violate terms of copyleft licenses (GPL family)
- Use Organization content in ways violating moral rights

### 5.5 Commercial Partnership Framework

Organizations seeking deeper collaboration may:

- Sponsor specific projects or features
- Enter trademark license agreements
- Participate in advisory councils
- Jointly develop under partnership agreements

Contact: [PARTNERSHIP EMAIL]

---

## 6. Contributor License Agreements

### 6.1 CLA Requirement

All substantial contributions to Organization projects require a signed Contributor License Agreement. "Substantial" means:

- Code contributions exceeding [NUMBER] lines
- Documentation contributions exceeding [NUMBER] words
- Design or creative contributions
- Any contribution not clearly de minimis

**Exceptions:**
- De minimis contributions (typo fixes, minor corrections)
- Contributions from employees (covered by employment agreement)
- Contributions under existing partnership agreements

### 6.2 CLA Types

**Individual CLA (ICLA):**
- For individual contributors
- Grants license and patent rights to Organization
- Warranties contribution is original and rights held
- Covers all contributions to all Organization projects

**Corporate CLA (CCLA):**
- For employees contributing on behalf of employer
- Employer grants license and patent rights
- Lists authorized contributors
- Covers contributions during employment

### 6.3 CLA Content Requirements

CLA must include:

- Grant of copyright license (perpetual, worldwide, royalty-free)
- Grant of patent license (if applicable)
- Representation of authority to grant
- Warranty of originality
- Acknowledgment no compensation expected
- Agreement to follow project Code of Conduct

### 6.4 CLA Administration

**Process:**
1. CLA sent to prospective contributor
2. Signed CLA returned (electronic signature acceptable)
3. CLA recorded in [DESIGNATED SYSTEM]
4. Contributor added to authorized contributors list
5. CLA verification automated in CI/CD pipeline

**Records:**
- CLAs retained for duration of copyright plus [NUMBER] years
- Annual audit of CLA compliance
- Quarterly reconciliation with project contributors

---

## 7. Third-Party Code Usage

### 7.1 Policy Principles

- Respect open source licenses
- Comply with all license obligations
- Maintain accurate inventory of third-party code
- Prohibit use of code with incompatible licenses
- Document all third-party dependencies

### 7.2 Approved License Categories

| Category | Licenses | Use |
|----------|----------|-----|
| **Permissive** | MIT, BSD, Apache 2.0 | Any use, including proprietary |
| **Weak Copyleft** | LGPL, MPL | Dynamic linking allowed in proprietary |
| **Strong Copyleft** | GPL, AGPL | Only in compatible open source projects |
| **Documentation** | CC BY, CC0, GFDL | Content and documentation |

### 7.3 License Compliance Requirements

**For All Third-Party Code:**

1. **Inventory:** Maintain Software Bill of Materials (SBOM)
2. **Verification:** Confirm license compatibility with project license
3. **Documentation:** Include in NOTICES or LICENSE file
4. **Attribution:** Preserve all copyright notices
5. **Source:** Make source available when required by copyleft

**Apache 2.0 Compliance:**
- Include NOTICE file if provided
- State modifications made
- Preserve patent grant

**GPL Compliance:**
- Source code offer for distributed binaries
- License text inclusion
- Written offer valid for 3 years

### 7.4 Prohibited Code

Do NOT use code with:

- Unknown or unclear licenses
- "Research only" or "non-commercial" restrictions
- GPL-incompatible licenses in GPL projects
- Proprietary licenses without express authorization
- Copyleft code in proprietary products (without compliance)

### 7.5 Security Considerations

Third-party code must also meet:

- Security review for critical dependencies
- Maintenance status verification (not abandoned)
- Vulnerability scanning in CI/CD
- Approved source only (no unverified packages)

---

## 8. Attribution Requirements

### 8.1 Internal Attribution

Organization projects must properly attribute:

- Individual contributors (in CONTRIBUTORS file)
- Funding sources (in ACKNOWLEDGMENTS)
- Partner organizations
- Third-party code (in NOTICES)

### 8.2 External Attribution

Users of Organization IP must provide:

**Software:**
```
This product includes software developed by [ORGANIZATION NAME].
[License text or reference]
```

**Content:**
```
[Title] by [ORGANIZATION NAME] is licensed under CC BY 4.0
[Link to original]
```

### 8.3 Moral Rights

The Organization respects moral rights of creators where applicable:

- Right of attribution (paternity)
- Right of integrity (no derogatory treatment)
- Right to anonymity (if requested)

---

## 9. IP Enforcement

### 9.1 Infringement Monitoring

The Organization monitors for:

- Unauthorized trademark use
- License violations (failure to attribute, etc.)
- Plagiarism of content
- Patent infringement claims against Organization

### 9.2 Enforcement Priorities

**High Priority:**
- Trademark confusion harming Organization reputation
- Willful license violations
- Commercial exploitation without attribution

**Medium Priority:**
- Innocent attribution failures (educational response)
- Non-commercial violations

**Low Priority:**
- Technical violations with no harm
- De minimis uses

### 9.3 Enforcement Process

1. **Documentation:** Gather evidence of violation
2. **Evaluation:** Assess priority and best resolution
3. **Contact:** Initial outreach seeking compliance
4. **Escalation:** Formal notice if needed
5. **Resolution:** Compliance or legal action

**Preferred Resolution:**
- Always prefer education over enforcement
- Seek compliance, not damages
- Preserve relationships where possible

### 9.4 Defensive Response

If Organization accused of infringement:

1. Immediate legal counsel consultation
2. Document review and analysis
3. Good faith investigation
4. Remediation if substantiated
5. Defense if unsubstantiated

---

## 10. Education and Compliance

### 10.1 Training Requirements

| Audience | Training Content | Frequency |
|----------|-----------------|-----------|
| All Staff | IP basics, confidentiality | Annually |
| Developers | Open source licensing, CLA process | Annually |
| Managers | Third-party code approval, enforcement | Annually |
| New Hires | IP ownership, disclosure obligations | Within 30 days |

### 10.2 Resources

**Internal Resources:**
- IP policy portal: [URL]
- License decision tree: [URL]
- Approved vendor list: [URL]
- CLA submission system: [URL]

**External Resources:**
- Open Source Initiative: https://opensource.org/licenses
- Choose a License: https://choosealicense.com
- Creative Commons: https://creativecommons.org/choose

### 10.3 Compliance Review

**Quarterly:**
- CLA compliance check
- Trademark usage audit
- Third-party code inventory update

**Annually:**
- Full IP policy review
- Training completion verification
- External IP landscape assessment

---

## 11. Implementation Notes

### 11.1 Immediate Actions (0-30 Days)

- [ ] Inventory existing IP assets
- [ ] Register core trademarks
- [ ] Implement CLA collection system
- [ ] Create license decision tree for developers
- [ ] Audit third-party dependencies in all projects

### 11.2 Short-Term Actions (30-90 Days)

- [ ] Standardize licenses on existing projects
- [ ] Create SBOM for all active projects
- [ ] Develop trademark usage guidelines
- [ ] Establish IP enforcement procedures
- [ ] Deploy training program

### 11.3 Ongoing Actions

- [ ] Quarterly IP audits
- [ ] Annual policy review
- [ ] Continuous CLA processing
- [ ] Trademark monitoring
- [ ] License compliance in CI/CD

### 11.4 Key Contacts

| Role | Name/Email | Responsibilities |
|------|------------|-----------------|
| IP Officer | [EMAIL] | Strategy, enforcement, trademarks |
| Open Source Lead | [EMAIL] | License selection, CLA process |
| Legal Counsel | [EMAIL] | Complex licensing, disputes |
| Compliance Officer | [EMAIL] | Training, audits, policy |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [DATE] | [AUTHOR] | Initial policy |

---

**Acknowledgment**

I have received, read, and understood the Intellectual Property & Licensing Policy. I agree to comply with its requirements and understand that violations may result in disciplinary action.

Employee Name: _________________________  
Signature: _________________________  
Date: _________________________
