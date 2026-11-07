# Nhat Minh Doan — automatic citation evidence audit

This repository contains a [citation dashboard](docs/index.html) and a daily GitHub Actions collector for the mathematical publications of Nhat Minh Doan. This is an evidence-backed **lower bound**, not a claim to know an exact worldwide citation total.

## What is monitored

- Canonical publications and aliases: [docs/papers.json](docs/papers.json)
- Verified citation relationships with source links: [docs/verified.json](docs/verified.json)
- Indexed-only discoveries and errors: [docs/discovered.json](docs/discovered.json)
- Collector: [citation_agent.py](citation_agent.py)
- Scheduled GitHub Action: [.github/workflows/citations.yml](.github/workflows/citations.yml)

The collector checks **OpenAlex, Semantic Scholar, OpenCitations, HexagonMath and targeted Zenodo and arXiv PDF bibliographies**. Indexed links are candidates until their bibliography is checked. It deduplicates many identifier/title matches, but some duplicate cross-platform variants can remain; those require manual review. Google Scholar and ResearchGate are not automatically scraped.

There are **13 provisional canonical works** and **7 manually verified citation relationships** in the starter ledger (DLN 6, DDD 1). The starting count is not a completed live census, and further papers and alias corrections may be necessary.

## Activate daily scans

1. Create an OpenAlex API key at https://openalex.org/settings/api and store it as `OPENALEX_API_KEY` at **Repository Settings → Secrets and variables → Actions**. Optional: store a Semantic Scholar key as `SEMANTIC_SCHOLAR_API_KEY`.
2. At **Actions → Daily citation audit**, enable workflows if necessary and choose **Run workflow** for the first scan. The collector also attempts to start on source-code changes. The scheduled run is **08:23 Vietnam time** every day (01:23 UTC). GitHub does not guarantee exact scheduled-start times.
3. Enable **Settings → Pages → Build and deployment → Source: GitHub Actions** and save. The separate `Publish citation dashboard` workflow deploys the `/docs` folder after changes or a completed audit. The expected address, once Pages has published, is https://minhmath.github.io/Nhat-Minh-Doan.github.io/
4. Embed the published URL into https://sites.google.com/view/dnminh/homepage using **Insert → Embed**.

## Definitions

A verified citation relationship is a distinct citing work mentioning a given target paper in its bibliography. If a citing paper references two of your papers, it contributes **two relationships**, not one. References in different versions of the same citing paper should count once. The dashboard shows independent verified citations separately from papers authored by Doan.

The HexagonMath scan records successfully checked versions in `docs/scan_state.json` so later runs concentrate on newly added versions. The automated collector is a **best-effort supplementary discovery system**: APIs can rate-limit, HTML layouts can change, and full-text coverage is incomplete. Inspect any unexpected discoveries before treating the counts as definitive.

## Manual correction

Edit `docs/papers.json` to add or correct target works; record old titles under `aliases`. Edit `docs/verified.json` only after checking a real bibliography or underlying reference data. Each entry should contain `target`, `title`, `authors`, `platform`, `id`, `source`, `verified: true`, and ideally `url`.

## Local run

```bash
python -m pip install -r requirements.txt
python -m py_compile citation_agent.py
python citation_agent.py
python -m http.server 8000 --directory docs
```

Open http://localhost:8000. This repository is distinct from the more extensive downloadable prototype supplied in the ChatGPT conversation.

