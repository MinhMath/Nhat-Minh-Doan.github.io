#!/usr/bin/env python3
"""Generate every published count from the same normalized citation ledger."""
import json
from pathlib import Path
from citation_identity import build_ledger

ROOT=Path(__file__).resolve().parent


def load(path, default):
    file=ROOT/path
    return json.loads(file.read_text(encoding="utf-8")) if file.exists() else default


def citing_url(c):
    if c.get("url"):return c["url"]
    if c.get("platform")=="hexagon":return "https://hexagonmath.org/"+str(c.get("id",""))
    if c.get("platform")=="arxiv":return "https://arxiv.org/abs/"+str(c.get("id",""))
    return ""


def link(p):
    for key,base in (("doi","https://doi.org/"),("arxiv","https://arxiv.org/abs/"),("hexagon","https://hexagonmath.org/")):
        if p.get(key):return base+p[key]
    return ""


def name(s):
    return str(s).replace("|","/").replace("\n"," ").strip()


def main():
    papers=load("docs/papers.json",[])
    ledger=build_ledger(papers,load("docs/verified.json",[]),load("docs/discovered.json",{}))
    (ROOT/"docs/ledger.json").write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    counts=ledger["counts"]
    rows=ledger["citations"]
    verified=[r for r in rows if r["verified"]]
    candidates=[r for r in rows if not r["verified"]]
    lines=["# Citation evidence — Nhat Minh Doan","",
           "> **Verified lower bound, not an exact worldwide total.** Verified references and unverified discoveries are recorded separately. A missing or failed source is not evidence of zero citations.","",
           f"**Verified relationships:** {counts['verified']} | **Independent verified:** {counts['independent']} | **Distinct verified citing works:** {counts['unique_citing_works']} | **Unverified candidates:** {counts['candidates']} | **Papers tracked:** {counts['papers']}","",
           f"Collection status: **{ledger['collection_status']}**. Last saved discovery: {ledger['generated_utc'] or 'not yet completed'}.","",
           "| Canonical paper | Verified citations | Unverified candidates |","|---|---:|---:|"]
    for p in sorted(papers,key=lambda p:sum(r["target"]==p["id"] for r in verified),reverse=True):
        label=name(p["title"])
        url=link(p)
        cell=f"[{label}]({url})" if url else label
        lines.append(f"| {cell} | {sum(r['target']==p['id'] for r in verified)} | {sum(r['target']==p['id'] for r in candidates)} |")
    lines += ["","## Verified bibliography references",""]
    for p in papers:
        matches=[r for r in verified if r["target"]==p["id"]]
        if not matches:continue
        lines += ["### "+name(p["title"]),""]
        for c in sorted(matches,key=lambda c:c["title"]):
            url=citing_url(c)
            label=f"[{name(c['title'])}]({url})" if url else name(c["title"])
            kind={"independent":"independent","overlap":"shared author","unknown":"author overlap unresolved"}[c["independence"]]
            lines.append(f"- {label} — {name(c.get('authors') or 'author unavailable')}; {kind}. {name(c.get('source',''))}.")
            if c.get("evidence_excerpt"):
                lines.append("  Reference excerpt: "+name(c["evidence_excerpt"]))
        lines.append("")
    lines += ["## Collection status", "", "| Source | Status |", "|---|---|"]
    for source,status in ledger["sources"].items():
        lines.append(f"| {name(source)} | {name(status.get('status','unknown'))} |")
    if not ledger["sources"]:lines.append("| Automated scan | No completed discovery snapshot |")
    if ledger["errors"]:
        lines += ["", "Collection limitations:", ""]
        lines.extend("- "+name(error) for error in ledger["errors"])
    lines += ["", "The dashboard and this report use [the same normalized ledger](docs/ledger.json).",
              "Independent citations exclude identified shared authors; incomplete or ambiguous author names are recorded separately.",
              "A citing work that references two target papers contributes two relationships and one distinct citing work.",
              "Google Scholar and ResearchGate totals are not automatically accepted as verified evidence.", ""]
    (ROOT/"CITATIONS.md").write_text("\n".join(lines),encoding="utf-8")
    print("Wrote report and ledger:",counts)


if __name__=="__main__":main()
