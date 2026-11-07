# Nhat Minh Doan — personal website

The [personal homepage](https://minhmath.github.io/Nhat-Minh-Doan.github.io/) preserves the Google Site’s blue navigation, Hạ Long Bay banner, serif typography, and biography. Its closing sentence links to Papers, CV, and the email address. Publication lists are on the Papers page. The [Online Seminars tab](https://minhmath.github.io/Nhat-Minh-Doan.github.io/seminars/) introduces the Hyperbolic Geometry & Related Topics Online Seminar and links to announcements, the seminar website, and the organizer’s email. The public CV is hosted in [docs/assets/cv.pdf](docs/assets/cv.pdf). `scripts/build_site.py` rebuilds the pages during every deployment. Search, navigation, and layouts work on desktop and mobile.

The [Papers page](https://minhmath.github.io/Nhat-Minh-Doan.github.io/papers/) lists papers, authors, publication details, First online dates, and a Cited by column. Each number opens the citing works, including authors and publication details. Paper details follow the author’s homepage. The First online column links to the earliest documented public posting, and the list runs from newest to oldest. Citation totals appear at the bottom. The standalone [embed](https://minhmath.github.io/Nhat-Minh-Doan.github.io/embed.html) retains the minimal `Papers` view. Existing embeds of the root URL are redirected to that view when opened inside an iframe.

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
<iframe src="https://minhmath.github.io/Nhat-Minh-Doan.github.io/embed.html" title="Papers" width="100%" height="1500" style="border:0;"></iframe>
```

## Local checks

```bash
python -m pip install -r requirements.txt
python -m unittest -v test_citation_agent
python citation_agent.py
python generate_report.py
python scripts/build_site.py
python -m http.server 8000 --directory docs
```

## Updating the CV and portrait

The CV uses the shared publication catalogue and [cv/details.json](cv/details.json). Its source generator is [scripts/build_cv.py](scripts/build_cv.py); it requires ReportLab, pypdf, the Liberation Serif font family, and Poppler. To rebuild it, run `python -m pip install reportlab pypdf`, then `python scripts/build_cv.py` and `python scripts/build_site.py`. The November 2026 revision retains the earlier CV’s education, employment, talks, service, advising, teaching, awards, grants, and references, adds the Hebei conference talk, and updates all 13 works. The programme URL and date precision are recorded in the talk metadata.

The third navigation tab, [CV](https://minhmath.github.io/Nhat-Minh-Doan.github.io/cv/), displays all pages as scalable vector artwork in the normal page flow, with clickable links, accessible text, and a PDF download. It has no nested scroll box. `scripts/render_cv_pages.py` exports these pages from the PDF and records its hash; the site build rejects stale page exports.

The original 712 × 716 uploaded portrait is retained in `docs/assets/portrait.png`. A CSS frame crops it for the navigation without altering the image. Content hashes on the portrait, stylesheet, and CV links ensure returning visitors receive revised assets. The homepage and Papers page share the same generated navigation.

Self citations count citing works that include Nhat Minh Doan. Citations by collaborators without him count as non-self. Each distinct citing work counts once per target paper, including across Zenodo versions.

The first column takes most of the page width and uses numbered serif entries with blue titles, visible authors, and bold publication details. The Papers and Other writings sections preserve the homepage’s publication numbering and sort each section by first online appearance, newest first. An “Abstract” disclosure opens only the abstract in a padded panel with justified text, normal paragraph wrapping, and even spacing on both sides. Citing lists use the same bibliography style in lightly shaded, indented panels and remain in newest-first order across the table width. The legacy embed retains a single chronological list. External abstracts are concise summaries labelled accordingly; original abstracts are retained for Doan’s papers. Mathematical formulas are typeset when their abstract opens.

The CV retains the original links to the Maths, Magic and Maryam comic, the doctoral thesis award announcement, and SASEA fellowship page. Its homepage link points to the GitHub site. The embedded vector pages preserve every link in the downloadable PDF.

For published papers, the abstract comes from the version of record, including publisher-deposited Crossref metadata. Unpublished papers use the latest public arXiv or HexagonMath version. Abstract source, version, and check date are recorded separately from the first-online date; updating an abstract must not change that date. A failed publisher fetch must not replace a published abstract with an older preprint abstract.
