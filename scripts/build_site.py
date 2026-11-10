#!/usr/bin/env python3
"""Build the personal homepage from the shared publication catalogue."""
import html
import json
import hashlib
import re
from shutil import copyfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
BASE='https://minhmath.github.io/'
LEGACY=DOCS/'Nhat-Minh-Doan.github.io'

GOOGLE_TAG = '''<!-- Google tag -->
<script>
 (function(){
  var excluded=window['ga-disable-G-0R548MHC6P']===true;
  var url=new URL(window.location.href);
  var preference=url.searchParams.get('exclude_me');
  var ownerActivation=url.searchParams.get('owner_dashboard')==='1';
  if(preference==='1'||ownerActivation)excluded=true;
  try{
   if(preference==='1'||ownerActivation)localStorage.setItem('nhat-minh-doan:analytics-excluded','1');
   if(preference==='0')localStorage.removeItem('nhat-minh-doan:analytics-excluded');
   excluded=excluded||localStorage.getItem('nhat-minh-doan:analytics-excluded')==='1';
  }catch(error){}
  if(preference!==null){
   url.searchParams.delete('exclude_me');
   window.history.replaceState(null,'',url.pathname+url.search+url.hash);
  }
  window.nhatMinhAnalyticsExcluded=excluded;
  window['ga-disable-G-0R548MHC6P']=excluded;
  window.dataLayer = window.dataLayer || [];
  window.gtag=function(){window.dataLayer.push(arguments);};
  if(excluded)return;
  gtag('js', new Date());
  var tag=document.createElement('script');
  tag.async=true;
  tag.src='https://www.googletagmanager.com/gtm.js?id=GTM-NMHRF7PC';
  document.head.appendChild(tag);
 })();
</script>
<!-- End Google tag -->'''

def add_google_tag(page):
 # Redirect aliases are measured on their destination page.
 if re.search(r"""<meta\b[^>]*http-equiv=["']refresh["']""",page,re.I):
  return page
 page=re.sub(r'\n?<!-- Google tag -->.*?<!-- End Google tag -->', '', page, flags=re.S)
 anchor=r'(<meta\b[^>]*charset=[^>]*>)' if re.search(r'<meta\b[^>]*charset=',page,re.I) else r'(<head\b[^>]*>)'
 tagged,count=re.subn(anchor,lambda match:match[1]+'\n'+GOOGLE_TAG,page,count=1,flags=re.I)
 if count!=1:raise ValueError('Cannot find the page head for Google Analytics')
 return tagged

def escape(value):return html.escape(str(value),quote=True)

def asset_revision(name):return hashlib.sha256((DOCS/'assets'/name).read_bytes()).hexdigest()[:12]

def external(url,label):return f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>'

def url(p):
 for field,base in [('doi','https://doi.org/'),('arxiv','https://arxiv.org/abs/'),('hexagon','https://hexagonmath.org/')]:
  if p.get(field):return base+p[field]
 return '#'

def build_legacy_paths():
 for source in DOCS.rglob('*'):
  if LEGACY in source.parents or not source.is_file() or source==DOCS/'404.html':
   continue
  relative=source.relative_to(DOCS)
  destination=LEGACY/relative
  destination.parent.mkdir(parents=True,exist_ok=True)
  if source.suffix!='.html':
   copyfile(source,destination)
   continue
  path=relative.as_posix()
  target=BASE+path.removesuffix('index.html')
  if path=='homepage/index.html':target=BASE
  destination.write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Nhat Minh Doan</title>
<link rel="canonical" href="{escape(target)}">
<script>location.replace({json.dumps(target)} + location.search + location.hash);</script>
<noscript><meta http-equiv="refresh" content="0;url={escape(target)}"></noscript>
</head><body><a href="{escape(target)}">Continue to the new address</a></body></html>
''',encoding='utf-8')

def header():
 return f'''<a class="skip-link" href="#main">Skip to main content</a>
<header class="site-header">
 <a class="site-name" href="./"><span class="site-avatar"><img class="site-portrait" src="assets/portrait.png?v={asset_revision('portrait.png')}" width="33" height="41" alt=""></span>Nhat Minh Doan (Đoàn Nhật Minh)</a>
 <button class="search-open" type="button" aria-label="Search this site"><svg width="21" height="21" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="1.8"/><path d="m15.5 15.5 5 5" stroke="currentColor" stroke-width="1.8"/></svg></button>
</header>
<dialog class="site-search" aria-labelledby="search-title"><div class="search-heading"><h2 id="search-title">Search this site</h2><button type="button" class="search-close" aria-label="Close search">×</button></div><label for="site-search-input">Search papers</label><input id="site-search-input" type="search" placeholder="Title, author, or journal" autocomplete="off"><div id="search-results" aria-live="polite"></div></dialog>'''

def papers_panel():
 return f'''<div class="papers-content">
<figure class="papers-illustration"><img src="assets/surfaces-banner.png?v={asset_revision("surfaces-banner.png")}" width="2046" height="652" alt="Illustrations of surfaces, curves, and decompositions" loading="lazy"></figure>
<table aria-label="Papers"><thead><tr class="paper-section"><th scope="col"><h2>Papers</h2></th><th scope="col" title="Earliest documented public posting, rather than the journal issue date">First online</th><th scope="col">Cited by</th></tr></thead><tbody id="paper-rows"></tbody></table>
<section class="paper-insights" id="paper-insights" aria-label="Citation history and co-authors" hidden>
 <section class="insight-box" aria-labelledby="coauthors-heading">
  <h2 id="coauthors-heading">Co-authors</h2>
  <ul class="coauthor-list" id="coauthor-list"></ul>
 </section>
 <section class="insight-box" aria-labelledby="citation-chart-heading">
  <div class="insight-heading"><h2 id="citation-chart-heading">Citations by year</h2><div class="totals" id="totals" aria-label="Citation totals"></div></div>
  <div id="citation-chart"></div>
  <div class="citation-audit" id="citation-year-records" hidden></div>
 </section>
</section>
</div>'''

def meetings_panel():
 meetings=[
  ('August–September 2026', 'Shijiazhuang, China', 'Hyperbolic 2026 at Hebei Normal University', 'https://ahdoc.github.io/hyperbolic2026shijiazhuang/abstract'),
  ('July–August 2026', 'Jeju, South Korea', '2K-GATE Conference III', 'https://sites.google.com/view/2k-gate-workshop-3/home'),
  ('June 2026', 'Hanoi, Vietnam', 'Seminar, Thang Long Institute of Mathematics and Applied Sciences', None),
  ('May 2026', 'Singapore', 'Topology, Geometry and Dynamics Seminar, NUS', 'https://www.math.nus.edu.sg/category/events/colloquia-seminars/topology-geometry-dynamics/page/2/'),
  ('April 2026', 'Lausanne, Switzerland', 'Geometry and Spectra of Compact Riemann Surfaces, EPFL', 'https://bernoulli.epfl.ch/programs/the-geometry-and-spectra-of-hyperbolic-surfaces-and-other-manifolds/'),
  ('April 2026', 'Hefei, China', 'Teichmüller Theory and Related Topics', 'https://shinpeibaba.com/Teichmueller2026/main.php'),
  ('March 2026', 'Chengdu, China', 'Geometry and Topology Seminar, Southwest Jiaotong University', 'https://faculty.swjtu.edu.cn/lixiaobin1/zh_CN/article/363471/content/1862.htm'),
  ('August 2025', 'Singapore', 'Arithmetic Dynamics and Diophantine Geometry, IMS–NUS', 'https://ims.nus.edu.sg/events/arithmeticdynamics/'),
  ('July 2025', 'Phú Thọ, Vietnam', 'Workshop on Geometry and Related Topics', None),
  ('June 2025', 'Phú Quốc, Vietnam', 'Conference on Quantum Topology and Hyperbolic Geometry, VIASM–Clay', 'https://viasm.edu.vn/en/hdkh/Conf-Topo-Geo-2025'),
  ('April 2025', 'Singapore', 'Graduate Student Seminar, NUS', None),
  ('March 2025', 'Creswick, Australia', 'Teichmüller Theory and Flat Structures, MATRIX', 'https://www.matrix-inst.org.au/events/teichmuller-theory-and-flat-structures/'),
  ('March 2025', 'Singapore', 'Workshop on Dynamics and Related Topics, IMS–NUS', 'https://ims.nus.edu.sg/events/dynamicstopics/'),
  ('January 2025', 'Hanoi, Vietnam', 'Geometry and Dynamics in Low Dimensions', 'https://math.ac.vn/conference/gdld2025'),
  ('September 2024', 'Vĩnh Phúc, Vietnam', 'Gặp gỡ Toán học 2024, workshop for early-career researchers', 'https://math.ac.vn/conference/GGTH2024'),
  ('June 2024', 'Singapore', 'Computational Aspects of Thin Groups, IMS–NUS', 'https://ims.nus.edu.sg/events/computational-aspects-of-thin-groups/'),
  ('May 2024', 'Osaka, Japan', 'IMVAST–OCAMI Joint Conference on Selected Areas in Mathematics', 'https://math.ac.vn/en/conference/imvastocami2024'),
  ('March 2024', 'Seoul, South Korea', 'Geometry and Topology Seminar, KIAS', 'https://www.kias.re.kr/kias/activities/seminars/view.do?edate=&menuNo=402021&mjrcdnm=&pageIndex=1&schoolsCd=M&sdate=2024-03-09&seqno=PGN1720240318-0001'),
  ('December 2023', 'Seoul, South Korea', 'Hyperbolic Geometry of Numbers, KIAS', 'https://sites.google.com/view/hygen2023'),
  ('September 2023', 'Quy Nhơn, Vietnam', 'Topology of Singularities and Related Topics, JSPS–VAST', 'https://sites.google.com/keio.jp/jv2021-2024/jv2023-workshop'),
  ('August 2023', 'Hạ Long, Vietnam', 'Topics in Contemporary Differential Geometry, VIASM–ICTP Summer School workshop', 'https://indico.ictp.it/event/10196/session/7/'),
  ('August 2023', 'Hanoi, Vietnam', 'VIASM–ICTP Summer School on Differential Geometry', 'https://indico.ictp.it/event/10196/'),
  ('April 2023', 'Hà Tĩnh, Vietnam', 'Mathematics and Related Fields, Hà Tĩnh University', 'https://htu.edu.vn/tin-t%E1%BB%A9c-s%E1%BB%B1-ki%E1%BB%87n/1500-h%E1%BB%99i-th%E1%BA%A3o-khoa-h%E1%BB%8Dc-%E2%80%9Cto%C3%A1n-h%E1%BB%8Dc-v%C3%A0-c%C3%A1c-ng%C3%A0nh-li%C3%AAn-quan%E2%80%9D?highlight=WyJ2aVx1MWVjN3QiXQ%3D%3D'),
  ('December 2022', 'Hanoi, Vietnam', 'JSPS–VAST Joint Research Workshop', 'https://sites.google.com/keio.jp/jv2021-2024/jv2022-workshop-in-hanoi'),
  ('November 2022', 'Hanoi, Vietnam', 'Algebra and Number Theory Seminar, Institute of Mathematics, VAST', None),
  ('October 2022', 'Phú Thọ, Vietnam', 'Geometry, Analysis and Applications', 'https://math.ac.vn/en/conference/hoi-thao-khoa-hoc-hinh-hoc-giai-tich-va-ung-dung'),
  ('September 2022', 'Singapore', 'Topology and Geometry Seminar, NUS', 'https://www.math.nus.edu.sg/category/events/colloquia-seminars/topology-geometry-dynamics/page/14/'),
  ('August 2022', 'Vĩnh Phúc, Vietnam', 'Gặp gỡ Toán học 2022, workshop for early-career researchers', 'https://maths.hpu2.edu.vn/hoi-thao-khoa-hoc-cap-khoa--gap-go-toan-hoc-2022--hoi-thao-khoa-hoc-cac-nha-nghien-cuu-tre--thanh-cong-ruc-ro.html'),
  ('January 2022', 'Luxembourg', 'Geometry Winter Workshop and PhD defence, University of Luxembourg', None),
  ('October 2019', 'Bordeaux, France', 'PhD Away Days, University of Luxembourg and University of Bordeaux', 'https://math.uni.lu/docsem/f/away_days2019/2019-PhDAwayDays_Abstracts.pdf'),
  ('July 2019', 'Chiang Mai, Thailand', 'Combinatorial and Algebraic Aspects of Geometric Structures, Chiang Mai University', 'https://www.math.science.cmu.ac.th/lst/Poster2019-05-13.pdf'),
  ('July 2019', 'Luxembourg', 'Interactions between Hyperbolic Geometry and Number Theory, University of Luxembourg', 'https://gaati.org/rahm/InteractionsConference/'),
  ('August 2018', 'Les Diablerets, Switzerland', 'Geometry and Dynamics on Hyperbolic Surfaces, CUSO', 'https://www.cuso.ch/fileadmin/cuso/rapports_annuels/Rapport_CUSO_2018.pdf'),
  ('June 2018', 'Luxembourg', 'QUANTMOD2, Quantization and Moduli Spaces', 'https://math.uni.lu/quantmod/part.html'),
  ('May 2018', 'Heidelberg, Germany', 'PhD Away Days, University of Luxembourg', 'https://math.uni.lu/docsem/away_days/2018.html'),
  ('May 2018', 'Nancy, France', 'Structures on Surfaces (SoS) Kick-off Meeting, Inria–LORIA', 'https://sos.loria.fr/kickoff.html'),
  ('September 2015', 'Hanoi, Vietnam', 'Number Theory from Classical to Modern, VIASM Summer School', 'https://www.viasm.edu.vn/hdkh/sm-lts?userkey=danh-sach-dai-bieu'),
 ]
 rows=[
  f'    <li>{escape(date)} · <strong>{escape(place)}</strong> — {external(href,event) if href else escape(event)}</li>'
  for date,place,event,href in meetings
 ]
 return '\n'.join(['   <ul style="margin:8px 0 0;padding-left:2em;line-height:1.55">', *rows, '   </ul>'])

def cv_panel(papers):
 manifest=json.loads((DOCS/'assets/cv-pages.json').read_text())
 if manifest['pdf_sha256']!=hashlib.sha256((DOCS/'assets/cv.pdf').read_bytes()).hexdigest():
  raise ValueError('Render the CV pages again after changing the PDF')
 sheets=[]
 link_labels={}
 for paper in papers:
  link_labels[url(paper)]=paper.get('display_title',paper['title'])
  if paper.get('arxiv'):link_labels['https://arxiv.org/abs/'+paper['arxiv']]='arXiv version: '+paper.get('display_title',paper['title'])
 for number,page in enumerate(manifest['pages'],1):
  file=page['file']
  links=[]
  for link in page.get('links',[]):
   x1,y1,x2,y2=link['rect'];width=page['width'];height=page['height'];href=link['url']
   if not href.startswith(('https://','http://','mailto:')):continue
   label=link_labels.get(href,href.removeprefix('mailto:'))
   position=f'left:{100*x1/width:.5f}%;top:{100*(height-y2)/height:.5f}%;width:{100*(x2-x1)/width:.5f}%;height:{100*(y2-y1)/height:.5f}%'
   links.append(f'<a class="cv-link" href="{escape(href)}" title="{escape(label)}" aria-label="{escape(label)}" target="_blank" rel="noopener noreferrer" style="{position}"></a>')
  sheets.append(f'<section class="cv-sheet" aria-label="CV page {number} of {len(manifest["pages"])}"><img src="assets/{escape(file)}?v={asset_revision(file)}" width="612" height="792" alt="" aria-hidden="true" loading="lazy"><div class="visually-hidden">{escape(page["text"])}</div>{"".join(links)}</section>')
 return f'''<div class="cv-content">
<div class="cv-toolbar"><a href="assets/cv.pdf?v={asset_revision('cv.pdf')}" target="_blank" rel="noopener" download="Nhat_Minh_Doan_CV.pdf">Download PDF</a></div>
{''.join(sheets)}</div>'''

def redirect_section(section, label):
 target=f'../#{section}'
 # Keep a paper deep link or tracking query from existing bookmarks.
 fragment="(location.hash.startsWith('#paper-') ? location.hash : '#papers')" if section=='papers' else json.dumps('#'+section)
 return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{label} — Nhat Minh Doan</title><link rel="canonical" href="{BASE}">
<script>location.replace('../' + location.search + {fragment});</script>
<noscript><meta http-equiv="refresh" content="0;url={target}"></noscript>
</head><body><a href="{target}">Open {label} on Bio</a></body></html>'''

def main():
 papers=json.loads((DOCS/'papers.json').read_text())
 content=f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nhat Minh Doan (Đoàn Nhật Minh)</title>
<meta name="description" content="Nhat Minh Doan, researcher at the Institute of Mathematics, VAST. Hyperbolic surfaces, length spectra, publications, and contact information.">
<link rel="canonical" href="{BASE}"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="Nhat Minh Doan (Đoàn Nhật Minh)"><meta property="og:type" content="website"><meta property="og:url" content="{BASE}"><meta property="og:image" content="{BASE}assets/vietnam-banner.jpg">
<link rel="stylesheet" href="assets/site.css?v={asset_revision('site.css')}">
<link rel="stylesheet" href="assets/papers.css?v={asset_revision('papers.css')}">
<style>.email-toggle{{display:list-item;list-style-position:inside;cursor:pointer}}.email-disclosure{{white-space:nowrap}}.email-disclosure[open]>.email-toggle{{float:left;margin-inline-end:2em}}</style>
<script>if(window.self!==window.top)location.replace('embed.html'+location.search+location.hash);</script>
<script defer src="assets/site.js?v={asset_revision('site.js')}" data-catalogue="papers.json" data-papers="./"></script>
<script defer src="assets/papers.js?v={asset_revision('papers.js')}"></script>
</head>
<body>
{header()}
<main id="main">
 <section class="intro content-width" aria-label="About Minh" style="max-width:860px">
  <h1 class="visually-hidden">Nhat Minh Doan (Đoàn Nhật Minh)</h1>
  <p style="margin-bottom:12px">Hello! I’m Minh. I study hyperbolic surfaces and their length spectra.</p>
  <div style="margin-bottom:12px">
   <details class="email-disclosure" name="bio-section" style="display:inline-block;vertical-align:top">
    <summary class="email-toggle">Email</summary>
    <a href="mailto:dnminh@math.ac.vn">dnminh@math.ac.vn</a>
   </details>
   <span id="email-copy-status" role="status" style="margin-inline-start:.5em"></span>
   <script>
    const emailDisclosure = document.querySelector('.email-disclosure');
    const emailSummary = emailDisclosure.querySelector('summary');
    const emailAddress = emailDisclosure.querySelector('a');
    const emailCopyStatus = document.getElementById('email-copy-status');
    emailDisclosure.addEventListener('toggle', () => {{
     if (!emailDisclosure.open) emailCopyStatus.textContent = '';
    }});
    emailSummary.addEventListener('click', async () => {{
     emailCopyStatus.textContent = '';
     if (emailDisclosure.open || !navigator.clipboard) return;
     try {{
      await navigator.clipboard.writeText(emailAddress.textContent.trim());
      if (emailDisclosure.open) emailCopyStatus.textContent = 'Copied';
     }} catch {{
      // The revealed address is still available to copy manually.
     }}
    }});
   </script>
  </div>
  <details class="bio-section" name="bio-section" id="academic-background">
   <summary>Academic background and links</summary>
   <figure style="margin:12px 0 16px">
    <img src="assets/minh-academic-path.webp?v={asset_revision('minh-academic-path.webp')}" width="1620" height="1148" alt="Illustrated academic timeline from Ho Chi Minh City through Nice and Luxembourg to VAST, with a Singapore fellowship branching off the ongoing VAST appointment. A hyperbolic triangle says it is missing some degrees." style="display:block;width:100%;height:auto" loading="lazy" decoding="async">
   </figure>
   <ul>
    <li>Researcher (2022–present) at the {external('https://math.ac.vn/en','Institute of Mathematics, VAST')}.</li>
    <li>{external('https://snas.org.sg/saseaffellows','SASEA Research Fellow')} (2024–2026) at the {external('https://www.math.nus.edu.sg/','National University of Singapore')}, where I worked with {external('https://sites.google.com/view/serpeowtan/home','Ser Peow Tan')}.</li>
    <li>PhD (2018–2022) at the {external('https://www.uni.lu/fstm-en/research-departments/department-of-mathematics/','University of Luxembourg')}, where {external('https://homeweb.unifr.ch/parlierh/pub/index.html','Hugo Parlier')} supervised my {external('https://orbilu.uni.lu/handle/10993/50710','thesis')}.</li>
    <li>Master’s (2016–2017) at the {external('https://en.wikipedia.org/wiki/Universit%C3%A9_Nice-Sophia-Antipolis','University of Nice Sophia Antipolis')}, supervised by {external('https://flab.perso.math.cnrs.fr/','François Labourie')}.</li>
    <li>BA in Mathematics (2013–2015) at the University of Education, Ho Chi Minh City, Vietnam.</li>
   </ul>
  </details>
  <details class="bio-section" name="bio-section" id="papers">
   <summary>Papers</summary>
   {papers_panel()}
  </details>
  <details class="bio-section" name="bio-section" id="cv">
   <summary>CV</summary>
   {cv_panel(papers)}
  </details>
  <details class="bio-section" name="bio-section" id="where-we-may-have-met">
   <summary>Where we may have met</summary>
{meetings_panel()}
  </details>
  <details class="bio-section" name="bio-section" id="seminars">
   <summary>Online Seminars</summary>
   <div style="margin:6px 0 0 1em">{external('https://sites.google.com/view/nhatminhdoan','Hyperbolic Geometry & Related Topics Online Seminar')}</div>
  </details>
  <script>
   function openBioSectionFromHash() {{
    const section = document.getElementById(location.hash.slice(1));
    if (!section?.matches('details.bio-section')) return;
    section.open = true;
    requestAnimationFrame(() => section.scrollIntoView({{block: 'start'}}));
   }}
   openBioSectionFromHash();
   window.addEventListener('hashchange', openBioSectionFromHash);
  </script>
 </section>
</main>
</body>
</html>
'''
 (DOCS/'index.html').write_text(content,encoding='utf-8')
 for section,label in [('papers','Papers'),('cv','CV'),('seminars','Online Seminars')]:
  directory=DOCS/section
  directory.mkdir(exist_ok=True)
  (directory/'index.html').write_text(redirect_section(section,label),encoding='utf-8')
 (DOCS/'homepage/index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Nhat Minh Doan</title><meta http-equiv="refresh" content="0;url=../"><link rel="canonical" href="'+BASE+'"></head><body><a href="../">Bio</a></body></html>')
 for page_path in DOCS.rglob('*.html'):
  if LEGACY in page_path.parents:continue
  original=page_path.read_text(encoding='utf-8')
  page=original
  if page_path==DOCS/'embed.html' and 'assets/site.js' not in page:
   page=page.replace('</head>',f'<script defer src="assets/site.js?v={asset_revision("site.js")}" data-catalogue="papers.json" data-papers="papers/"></script>\n</head>',1)
  page=re.sub(r'(?<=src=")((?:\.\./)?assets/site\.js)(?:\?[^" ]*)?',lambda match:match[1]+'?v='+asset_revision('site.js'),page)
  tagged=add_google_tag(page)
  if tagged!=original:page_path.write_text(tagged,encoding='utf-8')
 build_legacy_paths()
 print('Built Bio and the old section redirects')

if __name__=='__main__':main()



