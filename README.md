# Papers and citation sources

The [public page](https://minhmath.github.io/Nhat-Minh-Doan.github.io/) lists papers, authors, publication details, First online dates, and a Cited by column. Each number opens the citing works, including authors and publication details. Paper details follow the author’s homepage. The First online column links to the earliest documented public posting, and the list runs from newest to oldest. Citation totals appear at the bottom. The document and iframe title are `Papers`.

The [citation report](CITATIONS.md) and [normalized ledger](docs/ledger.json) contain counts, evidence, and collection limitations. The bibliography-verified count is a lower bound; separately marked Google Scholar listings await full-text verification. Missing coverage does not establish zero citations.

## Discovery and verification

The collector searches OpenAlex, Semantic Scholar, OpenCitations, HexagonMath, Zenodo, and known arXiv bibliographies. Zenodo author monitoring uses Ying Zhang’s ORCID and Hu Tan’s affiliation to reject homonyms; unchanged PDF versions are cached. Full-text search can reveal citing papers whose citation edges are absent from an index. Search matches remain unverified candidates until a bibliography confirms the relationship. ResearchGate and Google Scholar aggregate totals are comparison data. The two author-supplied Google Scholar citing-list screenshots are recorded separately in docs/listed.json; these listings are not labelled as inspected bibliography entries.

Verification uses public PDFs, HexagonMath HTML bibliographies, and publisher-deposited Crossref reference entries. Published references can differ from the arXiv version. Verified records retain the reference excerpt, evidence URL, date, and available version or hash. Exact identifiers and title/author matches merge versions of the same citing work. A work citing two target papers contributes two relationships and one distinct citing work.

The target catalogue and title aliases are in [docs/papers.json](docs/papers.json). Known citing manuscripts are in [docs/citing_sources.json](docs/citing_sources.json). New relationships are saved in [docs/verified.json](docs/verified.json); unverified discoveries and errors are in [docs/discovered.json](docs/discovered.json). The HexagonMath scan continues through catalogue pages across runs and checks PDF links when HTML references are absent.

## Scheduled updates

The GitHub audit runs daily at 08:23 Vietnam time, subject to GitHub scheduling delays. Each run has a seven-minute discovery budget, saves partial results, and rotates the starting target. API failures are recorded as incomplete coverage. The separate publishing workflow updates GitHub Pages after changes and completed audits.

Optional API keys can be stored as repository secrets named `OPENALEX_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`. No Google account credentials are needed.

## Google Sites embed

```html
<iframe src="https://minhmath.github.io/Nhat-Minh-Doan.github.io/" title="Papers" width="100%" height="900" style="border:0;"></iframe>
```

## Local checks

```bash
python -m pip install -r requirements.txt
python -m unittest -v test_citation_agent
python citation_agent.py
python generate_report.py
python -m http.server 8000 --directory docs
```

Self citations count citing works that include Nhat Minh Doan. Citations by collaborators without him count as non-self. Each distinct citing work counts once per target paper, including across Zenodo versions.

The title column takes most of the page width. Authors, publication details, and abstracts open under a “more details” control for each paper and each citing work. Citing lists open across the table width and follow the same newest-first order by first online appearance. External abstracts are concise summaries labelled accordingly; original abstracts are retained for Doan’s papers. Mathematical formulas are typeset when their details panel opens.

For published papers, the abstract comes from the version of record, including publisher-deposited Crossref metadata. Unpublished papers use the latest public arXiv or HexagonMath version. Abstract source, version, and check date are recorded separately from the first-online date; updating an abstract must not change that date. A failed publisher fetch must not replace a published abstract with an older preprint abstract.
