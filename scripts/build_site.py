#!/usr/bin/env python3
"""Build the personal homepage from the shared publication catalogue."""
import html
import json
import hashlib
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
BASE='https://minhmath.github.io/Nhat-Minh-Doan.github.io/'

def escape(value):return html.escape(str(value),quote=True)

def asset_revision(name):return hashlib.sha256((DOCS/'assets'/name).read_bytes()).hexdigest()[:12]

def external(url,label):return f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>'

def url(p):
 for field,base in [('doi','https://doi.org/'),('arxiv','https://arxiv.org/abs/'),('hexagon','https://hexagonmath.org/')]:
  if p.get(field):return base+p[field]
 return '#'

def header(active, prefix=''):
 return f'''<a class="skip-link" href="#main">Skip to main content</a>
<header class="site-header">
 <a class="site-name" href="{prefix or './'}"><span class="site-avatar"><img class="site-portrait" src="{prefix}assets/portrait.png?v={asset_revision('portrait.png')}" width="33" height="41" alt=""></span>Nhat Minh Doan (Đoàn Nhật Minh)</a>
 <button class="nav-toggle" type="button" aria-label="Open navigation" aria-expanded="false" aria-controls="site-navigation"><span></span><span></span><span></span></button>
 <nav id="site-navigation" class="site-navigation" aria-label="Main navigation">
  <a href="{prefix or './'}" {'aria-current="page"' if active=='home' else ''}>Homepage</a>
  <a href="{prefix}papers/" {'aria-current="page"' if active=='papers' else ''}>Papers</a>
  <a href="{prefix}cv/" {'aria-current="page"' if active=='cv' else ''}>CV</a>
  <a href="{prefix}seminars/" {'aria-current="page"' if active=='seminars' else ''}>Online Seminars</a>
  <button class="search-open" type="button" aria-label="Search this site"><svg width="21" height="21" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="1.8"/><path d="m15.5 15.5 5 5" stroke="currentColor" stroke-width="1.8"/></svg></button>
 </nav>
</header>
<dialog class="site-search" aria-labelledby="search-title"><div class="search-heading"><h2 id="search-title">Search this site</h2><button type="button" class="search-close" aria-label="Close search">×</button></div><label for="site-search-input">Search papers</label><input id="site-search-input" type="search" placeholder="Title, author, or journal" autocomplete="off"><div id="search-results" aria-live="polite"></div></dialog>'''

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
<script>if(window.self!==window.top)location.replace('embed.html'+location.search+location.hash);</script>
<script defer src="assets/site.js" data-catalogue="papers.json" data-papers="papers/"></script>
</head>
<body>
{header('home')}
<main id="main">
 <figure class="home-banner content-width"><img src="assets/vietnam-banner.jpg?v={asset_revision('vietnam-banner.jpg')}" width="1489" height="596" alt="Hạ Long Bay, Vietnam" fetchpriority="high"></figure>
 <section class="intro content-width" aria-label="About Minh">
  <h1 class="visually-hidden">Nhat Minh Doan (Đoàn Nhật Minh)</h1>
  <p>Hello! I am Minh, a researcher at the {external('https://vast.gov.vn/web/vietnam-academy-of-science-and-technology/institutes1','Institute of Mathematics, VAST')}. I was a {external('https://snas.org.sg/saseaffellows','SASEA Research Fellow')} at the {external('https://www.math.nus.edu.sg/','National University of Singapore')} under Prof. {external('https://sites.google.com/view/serpeowtan/home','Ser Peow Tan')}. My {external('https://orbilu.uni.lu/handle/10993/50710','PhD thesis')} was completed at the {external('https://www.uni.lu/fstm-en/research-departments/department-of-mathematics/','University of Luxembourg')} under Prof. {external('https://homeweb.unifr.ch/parlierh/pub/index.html','Hugo Parlier')} in 2022.</p>
  <p>My research focuses on hyperbolic surfaces, length spectra, and related topics. I was introduced to hyperbolic geometry during my Master’s (M2) at the {external('https://en.wikipedia.org/wiki/Universit%C3%A9_Nice-Sophia-Antipolis','University of Nice Sophia Antipolis')} in 2017, where Prof. {external('https://flab.perso.math.cnrs.fr/','François Labourie')} supervised my master’s thesis.</p>
  <p>Here is my <a href="papers/">papers</a>, <a href="cv/">CV</a>, and my email address: <a href="mailto:dnminh@math.ac.vn">dnminh@math.ac.vn</a></p>
 </section>
</main>
</body>
</html>
'''
 (DOCS/'index.html').write_text(content,encoding='utf-8')
 papers_page=DOCS/'papers/index.html'
 if papers_page.exists():
  page,count=re.subn(r'<a class="skip-link".*?</dialog>',header('papers','../'),papers_page.read_text(),count=1,flags=re.S)
  if count!=1:raise ValueError('Cannot find the Papers page navigation')
  page=re.sub(r'href="\.\./assets/site\.css[^"]*"','href="../assets/site.css?v='+asset_revision('site.css')+'"',page,count=1)
  illustration=f'<figure class="papers-illustration"><img src="../assets/surfaces-banner.png?v={asset_revision("surfaces-banner.png")}" width="2046" height="652" alt="Illustrations of surfaces, curves, and decompositions" fetchpriority="high"></figure>'
  page,count=re.subn(r'(<main id="main" class="papers-content">)(?:\s*<figure class="papers-illustration">.*?</figure>)?',lambda match:match[1]+'\n'+illustration,page,count=1,flags=re.S)
  if count!=1:raise ValueError('Cannot find the Papers page content')
  papers_page.write_text(page,encoding='utf-8')
 (DOCS/'homepage/index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Nhat Minh Doan</title><meta http-equiv="refresh" content="0;url=../"><link rel="canonical" href="'+BASE+'"></head><body><a href="../">Homepage</a></body></html>')
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
  sheets.append(f'<section class="cv-sheet" aria-label="CV page {number} of {len(manifest["pages"])}"><img src="../assets/{escape(file)}?v={asset_revision(file)}" width="612" height="792" alt="" aria-hidden="true" loading="{("eager" if number==1 else "lazy")}"><div class="visually-hidden">{escape(page["text"])}</div>{"".join(links)}</section>')
 cv=f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CV — Nhat Minh Doan</title><meta name="description" content="Curriculum vitae of Nhat Minh Doan: publications, talks, education, teaching, and academic activities.">
<link rel="canonical" href="{BASE}cv/"><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../assets/site.css?v={asset_revision('site.css')}">
<script defer src="../assets/site.js" data-catalogue="../papers.json" data-papers="../papers/"></script>
</head><body class="cv-page">{header('cv','../')}
<main id="main" class="cv-content"><h1 class="visually-hidden">Curriculum vitae — Nhat Minh Doan</h1>
<div class="cv-toolbar"><a href="../assets/cv.pdf?v={asset_revision('cv.pdf')}" target="_blank" rel="noopener" download="Nhat_Minh_Doan_CV.pdf">Download PDF</a></div>
{''.join(sheets)}</main></body></html>'''
 (DOCS/'cv').mkdir(exist_ok=True)
 (DOCS/'cv/index.html').write_text(cv,encoding='utf-8')
 seminars=f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Online Seminars — Nhat Minh Doan</title>
<meta name="description" content="Hyperbolic Geometry and Related Topics Online Seminar, organized by Nhat Minh Doan. Researchers and graduate students are welcome to give a talk.">
<link rel="canonical" href="{BASE}seminars/"><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../assets/site.css?v={asset_revision('site.css')}">
<script defer src="../assets/site.js" data-catalogue="../papers.json" data-papers="../papers/"></script>
</head><body>{header('seminars','../')}
<main id="main">
 <div class="section-heading"><div class="content-width"><h1 class="seminars-title">Online Seminars</h1></div></div>
 <section class="seminar-copy content-width" aria-labelledby="seminar-name">
  <h2 id="seminar-name">{external('https://sites.google.com/view/nhatminhdoan','Hyperbolic Geometry & Related Topics Online Seminar')}</h2>
  <p>I organize this seminar and welcome talks from researchers and graduate students. To give a talk, please email <a href="mailto:dnminh@math.ac.vn">dnminh@math.ac.vn</a>.</p>
 </section>
</main></body></html>'''
 (DOCS/'seminars').mkdir(exist_ok=True)
 (DOCS/'seminars/index.html').write_text(seminars,encoding='utf-8')
 print('Built Homepage, Papers, CV, and Online Seminars')

if __name__=='__main__':main()
