#!/usr/bin/env python3
"""Build the public CV from the publication catalogue and cv/details.json.

Run with ReportLab installed: python scripts/build_cv.py
The publication list is shared with the personal website.
"""
from pathlib import Path
from html import escape
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, Table, TableStyle
from reportlab.lib.pagesizes import letter
from render_cv_pages import render_cv_pages

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'docs/assets/cv.pdf'
FONT_DIR=next(p for p in [Path('/usr/share/fonts/truetype/liberation'),Path('/usr/share/fonts/truetype/liberation2')] if (p/'LiberationSerif-Regular.ttf').exists())
for name,file in [('CV','LiberationSerif-Regular.ttf'),('CV-Bold','LiberationSerif-Bold.ttf'),('CV-Italic','LiberationSerif-Italic.ttf')]:
 pdfmetrics.registerFont(TTFont(name,str(FONT_DIR/file)))
pdfmetrics.registerFontFamily('CV',normal='CV',bold='CV-Bold',italic='CV-Italic',boldItalic='CV-Bold')
INK=colors.HexColor('#171717');LINK=colors.HexColor('#10417e')
BODY=ParagraphStyle('Body',fontName='CV',fontSize=10.7,leading=12.9,textColor=INK,spaceAfter=0)
LABEL=ParagraphStyle('Label',parent=BODY,fontName='CV-Bold',fontSize=10.7,leading=12.9)
DATE=ParagraphStyle('Date',parent=BODY,alignment=TA_RIGHT,fontSize=10.2,leading=12.9)
TITLE=ParagraphStyle('Title',parent=BODY,fontName='CV-Bold',fontSize=14.5,alignment=TA_CENTER,leading=19,spaceAfter=12)
FOOT=ParagraphStyle('Foot',parent=BODY,fontSize=8,leading=10,textColor=colors.HexColor('#666666'))
WIDTH=528
LABEL_WIDTH=77
DATE_WIDTH=76
TEXT_WIDTH=WIDTH-LABEL_WIDTH-DATE_WIDTH

def e(text):return escape(str(text),quote=True)
def a(url,label):return '<a href="'+e(url)+'" color="#10417e">'+e(label)+'</a>'
def para(text,style=BODY):return Paragraph(text,style)
def paper_url(p):
 for field,base in [('doi','https://doi.org/'),('arxiv','https://arxiv.org/abs/'),('hexagon','https://hexagonmath.org/')]:
  if p.get(field):return base+p[field]
 return ''

def footer(canvas,doc):
 canvas.saveState();canvas.setFont('CV',8);canvas.setFillColor(colors.HexColor('#666666'))
 canvas.drawString(42,24,'Nhat Minh Doan | Updated '+DETAILS['updated'])
 canvas.drawRightString(570,24,str(doc.page));canvas.restoreState()

DETAILS=json.loads((ROOT/'cv/details.json').read_text())
PAPERS=json.loads((ROOT/'docs/papers.json').read_text())
ROWS=[];SPANS=[]

def row(label,text,date='',wide=False):
 i=len(ROWS)
 ROWS.append([para(e(label),LABEL) if label else '',para(text),para(e(date),DATE) if date else ''])
 if wide:SPANS.append(('SPAN',(1,i),(2,i)))

def gap(points=7):
 i=len(ROWS);ROWS.append(['',Spacer(1,points),'']);SPANS.append(('SPAN',(1,i),(2,i)))

def entries(label,items):
 for i,item in enumerate(items):
  lead=('['+str(item['number'])+'] ') if 'number' in item else ''
  if 'title' in item:
   lead+='<b>'+e(item['title'])+'</b>'
   if item.get('institution'):lead+=', '+e(item['institution'])
  else:lead+=a(item['url'],item['text']) if item.get('url') else e(item['text'])
  details=item.get('detail',[])
  if isinstance(details,str):details=[details]
  text=lead+''.join('<br/>'+e(d) for d in details)
  row(label if i==0 else '',text,item.get('date',''))
 gap()

row('Affiliation','Institute of Mathematics, Vietnam Academy of Science and Technology<br/>Email: '+a('mailto:dnminh@math.ac.vn','dnminh@math.ac.vn')+'<br/>Homepage: '+a('https://minhmath.github.io/Nhat-Minh-Doan.github.io/','minhmath.github.io/Nhat-Minh-Doan.github.io'),wide=True);gap()
row('Research area','Hyperbolic geometry and low-dimensional topology. My current research concerns the multiplicity of simple closed geodesics on hyperbolic surfaces.',wide=True);gap()
entries('Education',DETAILS['education'])
entries('Academic positions',DETAILS['positions'])
for section,label in [('papers','Papers'),('other','Other writings')]:
 papers=sorted((p for p in PAPERS if p['section']==section),key=lambda p:p['display_number'],reverse=section=='papers')
 for i,p in enumerate(papers):
  title=p.get('display_title',p['title'])
  coauthors=[author for author in p['authors'] if author!='Nhat Minh Doan']
  text='['+str(p['display_number'])+'] '+a(paper_url(p),title)
  if coauthors:text+='<br/>(with '+e(', '.join(coauthors[:-1])+' and '+coauthors[-1] if len(coauthors)>1 else coauthors[0])+')'
  text+='<br/>'+e(p['venue'])
  if p.get('arxiv') and p.get('doi'):text+=' '+a('https://arxiv.org/abs/'+p['arxiv'],'arXiv:'+p['arxiv'])
  row(label if i==0 else '',text,str(p['year']))
 gap()
row('Referee work',e('; '.join(DETAILS['referee_work']))+'.',wide=True);gap()
entries('Talks',DETAILS['talks'])
entries('Services',DETAILS['services'])
entries('Advising',DETAILS['advising'])
entries('Teaching',DETAILS['teaching'])
entries('Awards',DETAILS['awards'])
entries('Grants',DETAILS['grants'])
for index in range(0,len(DETAILS['references']),2):
 refs=[]
 for ref in DETAILS['references'][index:index+2]:refs.append(para('<b>'+e(ref['name'])+'</b><br/>'+e(ref['institution'])+'<br/>'+a('mailto:'+ref['email'],ref['email'])))
 table=Table([refs],colWidths=[(WIDTH-LABEL_WIDTH)/2]*2,hAlign='LEFT')
 table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 i=len(ROWS);ROWS.append([para('References',LABEL) if index==0 else '',table,'']);SPANS.append(('SPAN',(1,i),(2,i)))
gap(3)
row('Hobbies',e(DETAILS['hobbies']),wide=True)

table=LongTable(ROWS,colWidths=[LABEL_WIDTH,TEXT_WIDTH,DATE_WIDTH],hAlign='LEFT',splitByRow=1)
table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(0,-1),12),('RIGHTPADDING',(1,0),(1,-1),10),('RIGHTPADDING',(2,0),(2,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),3)]+SPANS))
doc=SimpleDocTemplate(str(DEST),pagesize=letter,rightMargin=42,leftMargin=42,topMargin=36,bottomMargin=42,title='Curriculum vitae - Nhat Minh Doan',author='Nhat Minh Doan',subject='Updated publications and academic activities, '+DETAILS['updated'])
story=[para('Nhat Minh Doan (Đoàn Nhật Minh)',TITLE),Table([['']],colWidths=[WIDTH],style=TableStyle([('LINEBELOW',(0,0),(-1,-1),0.8,INK),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)])),Spacer(1,13),table]
doc.build(story,onFirstPage=footer,onLaterPages=footer)
render_cv_pages(DEST,doc.page)
print('Wrote',DEST)
