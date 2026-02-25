#!/usr/bin/env python3
from datetime import date
from pathlib import Path

ROOT = Path('/Users/AI-OPS/civicos-institute.github.io')
BLOG = ROOT / 'blog'

TOPICS = [
    ('Procurement and Public Accountability', 'public-sector AI procurement standards that keep systems auditable and accountable'),
    ('Algorithmic Transparency in Public Services', 'transparency requirements for AI systems used in eligibility, permitting, and service delivery'),
    ('Open Standards vs Vendor Lock-In', 'why interoperability is essential to democratic oversight and long-term reform'),
    ('Human Oversight at Decision Points', 'ensuring consequential government decisions remain contestable and human-accountable'),
]

def week_num(d: date) -> int:
    return d.isocalendar().week


def render_letter(d: date) -> tuple[str, str, str]:
    week = week_num(d)
    topic_title, topic_summary = TOPICS[week % len(TOPICS)]
    slug = f'letter-{d.isoformat()}'
    title = f'Weekly Update - Week {week}, {d.year}'
    content = f'''---
layout: default
title: "{title}"
date: {d.isoformat()}
permalink: /blog/{slug}/
---

# {title}

**{d.strftime('%B %-d, %Y')}**

Dear Friends,

This week, I want to focus on **{topic_title}**.

Three years from now, we will be living with the consequences of choices being made right now about how AI is deployed in government. The next one thousand days remain a narrow implementation window. If public institutions adopt these systems without enforceable transparency and accountability standards, the defaults will harden in ways that are difficult to reverse.

At CivicOS Institute, we are focused on practical guardrails: public-interest governance, open infrastructure, and standards that can be inspected and improved.

This week, we are emphasizing {topic_summary}. These are not abstract policy debates; they are operational decisions that shape trust, legitimacy, and democratic accountability.

We are committed to helping governments adopt technology that strengthens public institutions instead of obscuring them.

With gratitude and resolve,

**Nicholas A. Cerbone**  
President and Founder  
CivicOS Institute

---

## Previous Letters

- [Weekly Update - Week 8, 2026](/blog/letter-2026-02-24/)
- [Weekly Update - Week 7, 2026](/blog/letter-2026-02-17/)

---

*CivicOS Institute is a Florida nonprofit corporation in formation. Our application for 501(c)(3) federal tax-exempt status is pending with the IRS.*

[Support Our Work](https://www.gofundme.com/f/help-launch-the-civicos-institute) | [Join Our Community](https://discord.gg/tECtT9zeTT)
'''
    summary = f'This week focuses on {topic_summary}, with urgency around the next 1,000 days of AI governance in government.'
    return slug, title, summary, content


def update_index(d: date, slug: str, title: str, summary: str):
    index = BLOG / 'index.md'
    old = index.read_text()

    latest_block = f'''## Latest Letter

**[{title}](/blog/{slug}/)**  
*{d.strftime('%B %-d, %Y')}*  
{summary}
'''

    # Replace Latest Letter block
    start = old.find('## Latest Letter')
    all_letters = old.find('## All Letters')
    if start != -1 and all_letters != -1:
        old = old[:start] + latest_block + '\n---\n\n' + old[all_letters:]

    # Insert row after header row
    row = f"| {d.strftime('%b %-d, %Y')} | [{title}](/blog/{slug}/) | {summary} |\n"
    marker = '|------|-------|---------|\n'
    if marker in old and row not in old:
        old = old.replace(marker, marker + row)

    index.write_text(old)


def main():
    today = date.today()
    slug, title, summary, content = render_letter(today)
    out = BLOG / f'{slug}.md'
    if not out.exists():
        out.write_text(content)
        update_index(today, slug, title, summary)
        print(f'Created {out}')
    else:
        print(f'Already exists: {out}')


if __name__ == '__main__':
    main()
