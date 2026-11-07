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
  <button class="search-open" type="button" aria-label="Search this site"><svg width="21" height="21" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="1.8"/><path d="m15.5 15.5 5 5" stroke="currentColor" stroke-width="1.8"/></svg></button>
 </nav>
</header>
<dialog class="site-search" aria-labelledby="search-title"><div class="search-heading"><h2 id="search-title">Search this site</h2><button type="button" class="search-close" aria-label="Close search">×</button></div><label for="site-search-input">Search papers</label><input id="site-search-input" type="search" placeholder="Title, author, or journal" autocomplete="off"><div id="search-results" aria-live="polite"></div></dialog>'''

COAUTHORS={'Ser Peow Tan':'https://sites.google.com/view/serpeowtan/home','Sang-hyun Kim':'https://cayley.kr/','Mong Lung Lang':'https://arxiv.org/search/?searchtype=author&query=Lang%2C+M+L','Hugo Parlier':'https://homeweb.unifr.ch/parlierh/pub/index.html','Khanh Le':'https://sites.google.com/view/khanhqle','Hoang Thanh Nguyen':'https://sites.google.com/site/nthoangmath/home','Hanh Vo':'https://hanhv.github.io/'}

def publication(p):
 title=p.get('display_title',p['title'])
 byline=', '.join(external(COAUTHORS[a],a) if a in COAUTHORS else escape(a) for a in p['authors'])
 return f'''<li value="{p['display_number']}" id="paper-{escape(p['id'])}"><div class="publication-title">{external(url(p),title)}.</div><div class="publication-authors">{byline}.</div><div class="publication-venue">{escape(p['venue'])}</div></li>'''

def main():
 papers=json.loads((DOCS/'papers.json').read_text())
 primary=sorted((p for p in papers if p['section']=='papers'),key=lambda p:p['display_number'],reverse=True)
 other=sorted((p for p in papers if p['section']=='other'),key=lambda p:p['display_number'])
 content=f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nhat Minh Doan (Đoàn Nhật Minh)</title>
<meta name="description" content="Nhat Minh Doan, researcher at the Institute of Mathematics, VAST. Hyperbolic surfaces, length spectra, publications, and contact information.">
<link rel="canonical" href="{BASE}"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="Nhat Minh Doan (Đoàn Nhật Minh)"><meta property="og:type" content="website"><meta property="og:url" content="{BASE}"><meta property="og:image" content="{BASE}assets/ha-long-bay.jpg">
<link rel="stylesheet" href="assets/site.css?v={asset_revision('site.css')}">
<script>if(window.self!==window.top)location.replace('embed.html'+location.search+location.hash);</script>
<script defer src="assets/site.js" data-catalogue="papers.json" data-papers="papers/"></script>
</head>
<body>
{header('home')}
<div class="hero" role="img" aria-label="Boats among the limestone islands of Hạ Long Bay"></div>
<main id="main">
 <section class="intro content-width" aria-label="About Minh">
  <h1 class="visually-hidden">Nhat Minh Doan (Đoàn Nhật Minh)</h1>
  <p>Hello! I am Minh, a researcher at the {external('https://vast.gov.vn/web/vietnam-academy-of-science-and-technology/institutes1','Institute of Mathematics, VAST')}. I was a {external('https://snas.org.sg/saseaffellows','SASEA Research Fellow')} at the {external('https://www.math.nus.edu.sg/','National University of Singapore')} under Prof. {external('https://sites.google.com/view/serpeowtan/home','Ser Peow Tan')}. My {external('https://orbilu.uni.lu/handle/10993/50710','PhD thesis')} was completed at the {external('https://www.uni.lu/fstm-en/research-departments/department-of-mathematics/','University of Luxembourg')} under Prof. {external('https://homeweb.unifr.ch/parlierh/pub/index.html','Hugo Parlier')} in 2022.</p>
  <p>My research focuses on hyperbolic surfaces, length spectra, and related topics. I was introduced to hyperbolic geometry during my Master’s (M2) at the {external('https://en.wikipedia.org/wiki/Universit%C3%A9_Nice-Sophia-Antipolis','University of Nice Sophia Antipolis')} in 2017, where Prof. {external('https://flab.perso.math.cnrs.fr/','François Labourie')} supervised my master’s thesis.</p>
  <p>Here is my <a href="assets/cv.pdf?v={asset_revision('cv.pdf')}" target="_blank" rel="noopener">CV</a> and my email address: <a href="mailto:dnminh@math.ac.vn">dnminh@math.ac.vn</a></p>
 </section>
 <section aria-labelledby="papers-heading">
  <div class="section-heading"><div class="content-width"><h2 id="papers-heading">Papers</h2></div></div>
  <div class="content-width publications"><ol reversed start="{len(primary)}">{''.join(publication(p) for p in primary)}</ol></div>
 </section>
 <section aria-labelledby="other-heading">
  <div class="section-heading"><div class="content-width"><h2 id="other-heading">Other writings</h2></div></div>
  <div class="content-width publications"><ol>{''.join(publication(p) for p in other)}</ol></div>
 </section>
</main>
<footer class="content-width"><a href="https://sites.google.com/view/nhatminhdoan" target="_blank" rel="noopener noreferrer">Online Seminar</a></footer>
</body>
</html>
'''
 (DOCS/'index.html').write_text(content,encoding='utf-8')
 papers_page=DOCS/'papers/index.html'
 if papers_page.exists():
  page,count=re.subn(r'<a class="skip-link".*?</dialog>',header('papers','../'),papers_page.read_text(),count=1,flags=re.S)
  if count!=1:raise ValueError('Cannot find the Papers page navigation')
  page=re.sub(r'href="\.\./assets/site\.css[^"]*"','href="../assets/site.css?v='+asset_revision('site.css')+'"',page,count=1)
  papers_page.write_text(page,encoding='utf-8')
 (DOCS/'homepage/index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Nhat Minh Doan</title><meta http-equiv="refresh" content="0;url=../"><link rel="canonical" href="'+BASE+'"></head><body><a href="../">Homepage</a></body></html>')
 print('Built personal homepage:',len(primary),'papers and',len(other),'other writings')

if __name__=='__main__':main()
