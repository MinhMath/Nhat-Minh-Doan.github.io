"""Shared counting rules for the collector, Markdown report and dashboard."""
import re
import unicodedata


def clean(value):
    value = unicodedata.normalize("NFKD", str(value or "").replace("đ", "d").replace("Đ", "D"))
    return " ".join(re.findall(r"[a-z0-9]+", value.encode("ascii", "ignore").decode().lower()))


def identifiers(row):
    result = set(row.get("identifiers") or [])
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)", "", str(row.get("doi") or ""), flags=re.I).strip().lower()
    if doi:
        result.add("doi:" + doi)
        arxiv_doi = re.fullmatch(r"10\.48550/arxiv\.(.+)", doi)
        if arxiv_doi:
            result.add("arxiv:" + re.sub(r"v\d+$", "", arxiv_doi[1], flags=re.I))
    aid = re.sub(r"^(?:https?://arxiv\.org/(?:abs|pdf)/|arxiv:)", "", str(row.get("arxiv") or ""), flags=re.I)
    if aid:
        result.add("arxiv:" + re.sub(r"(?:v\d+)?(?:\.pdf)?$", "", aid))
    platform = row.get("platform", "")
    ident = str(row.get("id") or "")
    if platform and ident:
        if platform in ("arxiv", "hexagon"):
            ident = re.sub(r"v\d+$", "", ident)
        if platform == "doi":
            ident = re.sub(r"^https?://doi\.org/", "", ident, flags=re.I).lower()
        result.add(platform + ":" + ident)
    return result


def work_key(row):
    ids = identifiers(row)
    for prefix in ("doi:", "arxiv:", "hexagon:"):
        matches = sorted(i for i in ids if i.startswith(prefix))
        if matches:
            return matches[0]
    return sorted(ids)[0] if ids else "title:" + clean(row.get("title"))


def author_names(value):
    return value if isinstance(value, list) else [a.strip() for a in str(value or "").split(";") if a.strip()]


def author_signature(name):
    return tuple(sorted(clean(name).split()))


def canonicalize(rows):
    """Join identifier bridges transitively, then emit one edge per target/work.

    An exact long title and matching first author can bridge publisher and
    preprint identifiers. Different known first authors are kept separate.
    """
    rows = [dict(r) for r in rows if r.get("target") and r.get("title")]
    parent = list(range(len(rows)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def join(a, b):
        parent[root(a)] = root(b)

    seen = {}
    titles = {}
    for i, row in enumerate(rows):
        for ident in identifiers(row):
            if ident in seen:
                join(i, seen[ident])
            seen[ident] = i
        names = author_names(row.get("authors"))
        title = clean(row["title"])
        if len(title) >= 20 and names:
            key = (title, author_signature(names[0]))
            if key in titles:
                join(i, titles[key])
            titles[key] = i
    families = {}
    for i, row in enumerate(rows):
        families.setdefault(root(i), []).append(row)
    output = []
    for family in families.values():
        all_ids = sorted(set().union(*(identifiers(r) for r in family)))
        work_id = work_key({"identifiers": all_ids, "title": family[0]["title"]})
        targets = {}
        for row in family:
            targets.setdefault(row["target"], []).append(row)
        for target, variants in targets.items():
            variants.sort(key=lambda r: (bool(r.get("verified")), bool(r.get("evidence_excerpt")), len(str(r.get("authors") or ""))), reverse=True)
            best = dict(variants[0])
            evidence = []
            for row in variants:
                for ev in row.get("evidence") or [{k: row[k] for k in ("source", "url", "evidence_url", "evidence_excerpt", "checked_utc") if row.get(k)}]:
                    if ev and ev not in evidence:
                        evidence.append(ev)
                for k in ("doi", "arxiv", "authors", "url"):
                    if not best.get(k) and row.get(k):
                        best[k] = row[k]
            best.update(work_id=work_id, identifiers=all_ids, evidence=evidence,
                        verified=any(r.get("verified") is True for r in variants))
            output.append(best)
    return sorted(output, key=lambda r: (r["target"], r["work_id"]))


def independence(paper, row):
    """Conservative three-way classification; missing names are unknown."""
    own = author_names(paper.get("authors"))
    citing = author_names(row.get("authors"))
    if not own or not citing:
        return "unknown"
    uncertain = False
    for a in own:
        a_tokens = clean(a).split()
        for b in citing:
            b_tokens = clean(b.replace(",", " ")).split()
            if author_signature(a) == author_signature(b):
                return "overlap"
            # Full names can occur in Vietnamese or Western order. Initial-only
            # names with a shared surname cannot establish independence.
            if a_tokens[-1] in b_tokens:
                expected = sorted(t[0] for t in a_tokens[:-1])
                remaining = [t for t in b_tokens if t != a_tokens[-1]]
                if remaining and sorted(t[0] for t in remaining) == expected:
                    return "overlap"
                uncertain = True
    return "unknown" if uncertain else "independent"


def build_ledger(papers, verified, discovered):
    valid = {p["id"] for p in papers}
    rows = canonicalize(verified + discovered.get("citations", []))
    rows = [r for r in rows if r["target"] in valid]
    by_id = {p["id"]: p for p in papers}
    for row in rows:
        row["independence"] = independence(by_id[row["target"]], row)
    checked = [r for r in rows if r["verified"]]
    candidates = [r for r in rows if not r["verified"]]
    counts = {"verified": len(checked),
              "independent": sum(r["independence"] == "independent" for r in checked),
              "overlap": sum(r["independence"] == "overlap" for r in checked),
              "unknown_authorship": sum(r["independence"] == "unknown" for r in checked),
              "unique_citing_works": len({r["work_id"] for r in checked}),
              "candidates": len(candidates), "papers": len(papers)}
    return {"counts": counts, "papers": papers, "citations": rows,
            "generated_utc": discovered.get("generated_utc"),
            "collection_status": discovered.get("collection_status", "not_run"),
            "sources": discovered.get("sources", {}), "errors": discovered.get("errors", []),
            "warning": "Verified lower bounds; missing coverage is not a zero-citation claim."}
