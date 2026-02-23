#!/usr/bin/env python3
import argparse
import json
import re
from collections import defaultdict, Counter
from pathlib import Path


ANNOUNCE_PAT = re.compile(r"\b(announce|launch|released|introducing|available now|coming soon)\b", re.I)
PRODUCT_PAT = re.compile(r"\b(product|model|app|platform|feature|agent|api|tool|release)\b", re.I)
LINK_PAT = re.compile(r"https?://\S+|\b\S+\.com/\S*", re.I)
NAME_PAT = re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b")
FILLER_PAT = re.compile(r"\b(um+|uh+|you know|like and subscribe|thanks for watching)\b", re.I)


def sec_to_mmss(sec: float):
    sec = int(sec)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def hms_to_seconds(hms: str) -> float:
    hh, mm, ss = hms.split(":")
    return int(hh) * 3600 + int(mm) * 60 + float(ss)


def clean_text(t: str):
    t = re.sub(r"\s+", " ", t).strip()
    t = FILLER_PAT.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def chunk_entries(entries, window_sec=300):
    buckets = defaultdict(list)
    for e in entries:
        s = hms_to_seconds(e["start"])
        k = int(s // window_sec)
        buckets[k].append(e)
    ordered = []
    for k in sorted(buckets.keys()):
        seg = buckets[k]
        txt = " ".join(clean_text(x["text"]) for x in seg)
        txt = re.sub(r"\s+", " ", txt).strip()
        if not txt:
            continue
        ordered.append({
            "start_sec": hms_to_seconds(seg[0]["start"]),
            "end_sec": hms_to_seconds(seg[-1]["end"]),
            "text": txt,
        })
    return ordered


def summarize_segment(text: str, max_words=45):
    words = text.split()
    return " ".join(words[:max_words]) + ("…" if len(words) > max_words else "")


def extract_lists(entries):
    announcements, products, names, links = [], [], [], []
    for e in entries:
        t = e["text"]
        if ANNOUNCE_PAT.search(t):
            announcements.append((e["start"], t))
        if PRODUCT_PAT.search(t):
            products.append((e["start"], t))
        links += LINK_PAT.findall(t)
        names += NAME_PAT.findall(t)

    # dedupe while preserving order-ish
    def uniq(items, cap=12):
        seen, out = set(), []
        for it in items:
            key = it if isinstance(it, str) else it[1]
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
            if len(out) >= cap:
                break
        return out

    names_top = [n for n, _ in Counter(names).most_common(12)]
    return uniq(announcements, 10), uniq(products, 10), names_top, uniq(links, 20)


def build_markdown(data):
    title = data.get("title", "Untitled")
    duration = int(data.get("duration", 0) or 0)
    entries = data.get("entries", [])

    chunks = chunk_entries(entries, window_sec=300)
    full_text = " ".join(c["text"] for c in chunks)
    overview = summarize_segment(full_text, max_words=90)

    announcements, products, names, links = extract_lists(entries)

    lines = []
    lines.append(f"# YouTube Summary: {title}")
    lines.append("")
    lines.append("## Overview")
    lines.append(overview or "No overview available.")
    lines.append("")

    lines.append("## Section Breakdown (with timestamps)")
    for c in chunks:
        lines.append(f"- **{sec_to_mmss(c['start_sec'])} → {sec_to_mmss(c['end_sec'])}**: {summarize_segment(c['text'])}")
    lines.append("")

    lines.append("## Key Announcements")
    if announcements:
        for ts, t in announcements:
            lines.append(f"- [{ts}] {summarize_segment(t, 35)}")
    else:
        lines.append("- None clearly detected")
    lines.append("")

    lines.append("## Product Launches / Releases")
    if products:
        for ts, t in products:
            lines.append(f"- [{ts}] {summarize_segment(t, 35)}")
    else:
        lines.append("- None clearly detected")
    lines.append("")

    lines.append("## Names Mentioned")
    if names:
        for n in names[:12]:
            lines.append(f"- {n}")
    else:
        lines.append("- None confidently detected")
    lines.append("")

    lines.append("## Links / Resources Referenced")
    if links:
        for l in links[:20]:
            lines.append(f"- {l}")
    else:
        lines.append("- None detected in transcript")
    lines.append("")

    if duration > 1800:
        lines.append("## Top 5 Takeaways")
        # naive: use first 5 chunk summaries as takeaways
        for i, c in enumerate(chunks[:5], start=1):
            lines.append(f"{i}. {summarize_segment(c['text'], 28)}")
        lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--out", default="./artifacts/summary.md")
    args = ap.parse_args()

    data = json.loads(Path(args.transcript).read_text())
    md = build_markdown(data)
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md)
    print(str(out))


if __name__ == "__main__":
    main()
