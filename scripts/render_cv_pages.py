#!/usr/bin/env python3
"""Render the public CV as sharp, self-contained pages for the CV tab."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'docs/assets/cv.pdf'

def render_cv_pages(pdf=PDF,page_count=None):
 pdf=Path(pdf)
 if page_count is None:
  info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
  match=re.search(r'^Pages:\s+(\d+)',info,re.M)
  if not match:raise ValueError('Cannot determine the CV page count')
  page_count=int(match[1])
 pages=[]
 reader=PdfReader(str(pdf))
 for number in range(1,page_count+1):
  svg=pdf.parent/f'cv-page-{number}.svg'
  subprocess.run(['pdftocairo','-svg','-f',str(number),'-l',str(number),str(pdf),str(svg)],check=True)
  text=subprocess.check_output(['pdftotext','-f',str(number),'-l',str(number),'-layout',str(pdf),'-'],text=True).strip()
  source_page=reader.pages[number-1]
  links=[]
  for ref in source_page.get('/Annots',[]):
   annotation=ref.get_object()
   uri=annotation.get('/A',{}).get('/URI','')
   if str(uri).startswith(('https://','http://','mailto:')) and annotation.get('/Rect'):
    links.append({'url':str(uri),'rect':[float(value) for value in annotation['/Rect']]})
  pages.append({'file':svg.name,'text':text,'width':float(source_page.mediabox.width),'height':float(source_page.mediabox.height),'links':links})
 manifest={'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'pages':pages}
 (pdf.parent/'cv-pages.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print('Rendered',page_count,'CV pages for the website')

if __name__=='__main__':render_cv_pages()
