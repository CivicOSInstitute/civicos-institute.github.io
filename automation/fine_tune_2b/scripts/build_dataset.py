#!/usr/bin/env python3
import csv, json, pathlib, random, argparse

ROOT = pathlib.Path('/Users/AI-OPS/.openclaw/workspace/automation/fine_tune_2b')
WS = pathlib.Path('/Users/AI-OPS/.openclaw/workspace')


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def _split(rows):
    random.shuffle(rows)
    n=len(rows)
    a=max(1,int(n*0.8)); b=max(a+1,int(n*0.9)) if n>2 else n
    return rows[:a], rows[a:b], rows[b:] if b<n else rows[a:b]


def _fmt(inst, out):
    text = f"### Instruction:\n{inst}\n\n### Response:\n{out}"
    return {"text": text}


def build_outreach():
    src = WS / 'generated/outreach/wpb_90min_ai_workshop_emails.csv'
    rows=[]
    if src.exists():
        for r in csv.DictReader(src.open()):
            inst = f"Write a formal outreach email to {r.get('org_name','the organization')} targeting {r.get('title','leadership')}. Include subject line."
            out = f"Subject: {r.get('subject','Custom AI Workshop')}\n\n{r.get('email_body','').strip()}"
            rows.append(_fmt(inst,out))
    return rows


def build_ops_formatter():
    # Build schema-format examples from available outreach records.
    src = WS / 'generated/outreach/wpb_90min_ai_workshop_contacts.csv'
    rows=[]
    if src.exists():
        for r in csv.DictReader(src.open()):
            inst = (
                "Convert this lead note into strict JSON with keys: org_name, city, county, "
                "contact_name, title, email, fit_note, outreach_angle, priority. "
                f"Lead note: {r.get('org_name')} | {r.get('city')} | {r.get('contact_name')} | {r.get('fit_note')}"
            )
            obj = {
                "org_name": r.get('org_name',''),
                "city": r.get('city',''),
                "county": r.get('county',''),
                "contact_name": r.get('contact_name',''),
                "title": r.get('title',''),
                "email": r.get('email',''),
                "fit_note": r.get('fit_note',''),
                "outreach_angle": r.get('outreach_angle',''),
                "priority": "high" if 'County' in (r.get('org_name') or '') else "medium"
            }
            rows.append(_fmt(inst, json.dumps(obj, ensure_ascii=False)))
    return rows


def build_from_raw_jsonl(specialist):
    raw = ROOT / f'data/{specialist}/raw/examples.jsonl'
    rows=[]
    if raw.exists():
        for ln in raw.read_text(errors='ignore').splitlines():
            ln=ln.strip()
            if not ln:
                continue
            try:
                obj=json.loads(ln)
                inst=(obj.get('instruction') or '').strip()
                inp=(obj.get('input') or '').strip()
                out=(obj.get('output') or '').strip()
                if not inst or not out:
                    continue
                merged = inst if not inp else f"{inst}\n\nInput:\n{inp}"
                rows.append(_fmt(merged, out))
            except Exception:
                continue
    return rows


def build_generic_from_letters(specialist):
    paths=[
        WS / 'letter-from-director.md',
        WS / 'STANDING_TASK_DIRECTORS_LETTER.md',
        WS / 'blog/letter-2026-02-24.md',
        WS / 'blog/letter-2026-02-17.md'
    ]
    text=[]
    for p in paths:
        if p.exists():
            text.append(p.read_text(errors='ignore'))
    corpus='\n\n'.join(text)
    paras=[x.strip() for x in corpus.split('\n\n') if len(x.strip())>120][:200]
    rows=[]
    for p in paras:
        if specialist=='grant_analyst_2b':
            inst='Summarize this passage into a concise grant-fit brief (opportunity, relevance, action).'
        else:
            inst='Review this passage for policy/tone risks and provide pass/fail with one-line fix if needed.'
        rows.append(_fmt(inst,p[:1200]))
    return rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--specialist', required=True)
    args=ap.parse_args()
    sid=args.specialist

    if sid=='outreach_writer_2b':
        rows=build_outreach()
    elif sid=='ops_formatter_2b':
        rows=build_ops_formatter()
    elif sid in {'grant_analyst_2b','policy_qa_guard_2b'}:
        rows=build_from_raw_jsonl(sid)
        if len(rows) < 12:
            rows=build_generic_from_letters(sid)
    else:
        raise SystemExit(f'unknown specialist: {sid}')

    if len(rows)<12:
        raise SystemExit(f'not enough samples for {sid}: {len(rows)}')

    tr,va,te=_split(rows)
    d=ROOT / f'datasets/{sid}'
    _write_jsonl(d/'train.jsonl', tr)
    _write_jsonl(d/'valid.jsonl', va)
    _write_jsonl(d/'test.jsonl', te)
    print(json.dumps({"specialist":sid,"train":len(tr),"valid":len(va),"test":len(te),"dataset_dir":str(d)}))


if __name__=='__main__':
    main()
