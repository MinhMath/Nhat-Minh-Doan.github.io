#!/usr/bin/env python3
"""Citation discovery for Nhat Minh Doan. Indexed edges remain candidates.

Requires: requests, beautifulsoup4. Uses OpenAlex and Semantic Scholar APIs.
No inferred citation is counted as bibliographically verified.
"""
import json
import os
import re
import time
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime, timezone
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

DIR=Path(__file__).resolve().parent/"docs"
PAPERS=json.loads((DIR/"papers.json").read_text(encoding="utf-8"))
SEEDS=json.loads((DIR/"verified.json").read_text(encoding="utf-8"))
DEST=DIR/"discovered.json"
STATE=DIR/"scan_state.json"
session=requests.Session()
session.headers["User-Agent"]="NhatMinhDoanCitationAudit/1.0 (noncommercial citation metadata)"
errors=[]

def clean(s):
    return " ".join(re.findall(r"[a-z0-9]+",str(s or "").lower().replace("–","-")))

def get(url,params=None,headers=None):
    for i in range(3):
        try:
            r=session.get(url,params=params,headers=headers,timeout=25)
            if r.status_code==404:return None
            if r.status_code in (429,500,502,503,504):
                time.sleep(2**i)
                continue
            r.raise_for_status()
            return r.json()
        except (requests.RequestException,ValueError) as e:
            if i==2:errors.append(str(e)[:200])
            else:time.sleep(i+1)
    return None

def known(p,work):
    title=clean(work.get("display_name") or work.get("title"))
    variants=[p["title"]]+p.get("aliases",[])
    return any(SequenceMatcher(None,title,clean(v)).ratio()>.86 for v in variants)

def openalex(p):
    out=[]
    token=os.getenv("OPENALEX_API_KEY","")
    auth={"api_key":token} if token else {}
    found=set()
    # Search alternate paper titles, combining publisher/preprint versions.
    for title in [p["title"]]+p.get("aliases",[])[:2]:
        r=get("https://api.openalex.org/works",{"search":title,"per_page":15,**auth})
        if not isinstance(r,dict):continue
        for w in r.get("results",[]):
            if not known(p,w):continue
            names=" ".join(x.get("author",{}).get("display_name","") for x in w.get("authorships",[])).lower()
            if "doan" not in names:continue
            ident=w.get("id","").split("/")[-1]
            if not re.fullmatch(r"W\d+",ident) or ident in found:continue
            found.add(ident)
            for page in range(1,11):
                c=get("https://api.openalex.org/works",{"filter":"cites:"+ident,"per_page":100,"page":page,**auth})
                if not isinstance(c,dict):break
                items=c.get("results",[])
                for v in items:
                    authors=[x.get("author",{}).get("display_name","") for x in v.get("authorships",[])]
                    title=v.get("display_name") or v.get("title")
                    if not title:continue
                    ids=v.get("ids") or {}
                    arxiv=""
                    for loc in v.get("locations") or []:
                        u=loc.get("landing_page_url") or ""
                        mat=re.search(r"arxiv\.org/abs/(\d{4}\.\d{4,5})",u)
                        if mat:arxiv=mat.group(1);break
                    doi=(v.get("doi") or "").removeprefix("https://doi.org/")
                    out.append({"target":p["id"],"title":title,"authors":"; ".join(authors),
                                "doi":doi,"arxiv":arxiv,"platform":"openalex",
                                "id":v.get("id","").split("/")[-1],
                                "url":v.get("doi") or v.get("id"),"source":"OpenAlex indexed reference edge","verified":False})
                if len(items)<100:break
                time.sleep(.15)
    return out

def semantic(p):
    out=[]
    ids=(["ARXIV:"+p["arxiv"]] if p.get("arxiv") else [])+(["DOI:"+p["doi"]] if p.get("doi") else [])
    headers={"x-api-key":os.environ["SEMANTIC_SCHOLAR_API_KEY"]} if os.getenv("SEMANTIC_SCHOLAR_API_KEY") else {}
    for pid in ids:
        meta=get("https://api.semanticscholar.org/graph/v1/paper/"+quote(pid,safe=":"),{"fields":"paperId"},headers)
        if not isinstance(meta,dict) or not meta.get("paperId"):continue
        paperid=meta["paperId"]
        for offset in range(0,2000,100):
            r=get("https://api.semanticscholar.org/graph/v1/paper/"+paperid+"/citations",
                  {"fields":"title,authors,year,url,externalIds","offset":offset,"limit":100},headers)
            if not isinstance(r,dict):break
            items=r.get("data") or []
            for row in items:
                v=row.get("citingPaper") or {}
                if not v.get("title"):continue
                external=v.get("externalIds") or {}
                doi=external.get("DOI","")
                aid=external.get("ArXiv","")
                out.append({"target":p["id"],"title":v["title"],
                            "authors":"; ".join(x.get("name","") for x in v.get("authors") or []),
                            "doi":doi,"arxiv":aid,"platform":"arxiv" if aid else "semantic_scholar",
                            "id":aid or v.get("paperId"),"url":v.get("url") or ("https://doi.org/"+doi if doi else ""),
                            "source":"Semantic Scholar indexed reference edge","verified":False})
            if len(items)<100:break
            time.sleep(.25)
    return out

def work_key(c):
    if c.get("doi"):return "doi:"+str(c["doi"]).lower().removeprefix("https://doi.org/")
    if c.get("arxiv"):return "arxiv:"+re.sub(r"v\d+$","",str(c["arxiv"]))
    if c.get("platform") in ("arxiv","hexagon") and c.get("id"):
        return str(c["platform"])+":"+re.sub(r"v\d+$","",str(c["id"]))
    return "title:"+clean(c.get("title"))

def merged(rows):
    result={}
    for c in rows:
        k=c.get("target","")+"|"+work_key(c)
        if k not in result:result[k]=c
        elif c.get("verified"):result[k]=c
        elif not result[k].get("authors") and c.get("authors"):result[k]=c
    # Also merge identical title + first author where publisher/preprint IDs differ.
    ans={}
    for c in result.values():
        a=clean(c.get("authors","")).split()
        first=a[0] if a else ""
        k=c.get("target","")+"|"+clean(c.get("title",""))+"|"+first
        if k not in ans or (c.get("verified") and not ans[k].get("verified")):ans[k]=c
    return list(ans.values())


def bibliography(text):
    """Return only text after the last standalone References/Bibliography heading."""
    found=list(re.finditer(r"(?im)^\s*(?:references|bibliography)\s*$",text))
    return text[found[-1].end():] if found else ""

def matches_target(text,p):
    compact=clean(text)
    for identifier in (p.get("arxiv"),p.get("hexagon"),p.get("doi")):
        if identifier and clean(identifier) in compact:
            return True
    # Only distinctive long titles count as evidence.
    for variant in [p["title"]]+p.get("aliases",[]):
        normalized=clean(variant)
        if len(normalized)>40 and normalized in compact:
            return True
    return False

def inspect_arxiv_pdf(p,c):
    """Verify candidate citation against actual arXiv reference pages."""
    aid=c.get("arxiv")
    if not aid:return None
    from io import BytesIO
    from pypdf import PdfReader
    url="https://arxiv.org/pdf/"+aid
    try:
        response=session.get(url,timeout=28)
        if response.status_code!=200 or not response.content.startswith(b"%PDF"):
            return None
        if len(response.content)>18_000_000:return None
        reader=PdfReader(BytesIO(response.content),strict=False)
        pages=list(reader.pages)[-min(16,len(reader.pages)):]
        tail="\n".join(page.extract_text() or "" for page in pages)
        refs=bibliography(tail)
        if refs and matches_target(refs,p):
            return {**c,"verified":True,"source":"Verified in arXiv PDF bibliography",
                    "url":"https://arxiv.org/abs/"+aid}
    except Exception as exc:
        errors.append("arXiv verification "+aid+": "+str(exc)[:120])
    return None

def hexagon_scan(papers):
    """Check Hexagon HTML reference lists, plus a rotating queue of PDF bibliographies.

    HTML bibliography references are often missing, even if a PDF cites a paper.
    Successful scans are checkpointed so daily runs prioritize new versions.
    """
    from io import BytesIO
    from pypdf import PdfReader
    from urllib.parse import urljoin
    new=[]
    base="https://hexagonmath.org"
    listing=base+"/search?per_page=100"
    seen_pages=set()
    try:
        state=json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    except ValueError:
        state={}
    completed=set(state.get("hexagon_pages_checked",[]))
    pdf_done=set(state.get("hexagon_pdf_checked",[]))
    pending={r["href"]:r for r in state.get("hexagon_pdf_pending",[]) if isinstance(r,dict) and r.get("href")}
    checked=set(completed)
    for _ in range(20):
        if listing in seen_pages:break
        seen_pages.add(listing)
        try:
            r=session.get(listing,timeout=25)
            if r.status_code!=200:
                errors.append("Hexagon catalog HTTP "+str(r.status_code))
                break
            soup=BeautifulSoup(r.text,"html.parser")
        except requests.RequestException as exc:
            errors.append("Hexagon catalog: "+str(exc)[:160])
            break
        for a in soup.select("a[href]"):
            href=a.get("href","")
            m=re.fullmatch(r"/(\d{4}\.\d{5})(?:v\d+)?",href)
            if not m or href in completed:continue
            try:
                resp=session.get(urljoin(base,href),timeout=25)
                if resp.status_code!=200:continue
                doc=BeautifulSoup(resp.text,"html.parser")
            except requests.RequestException:
                continue
            checked.add(href)
            title=doc.find("h1").get_text(" ",strip=True) if doc.find("h1") else href
            text=doc.get_text("\n",strip=True)
            names=re.search(r"Contributed by\s*\n([^\n]+)",text)
            authors=names.group(1) if names else ""
            headings=[h for h in doc.find_all(["h2","h3"]) if clean(h.get_text(" ",strip=True))=="references"]
            refs=[]
            if headings:
                for node in headings[-1].next_elements:
                    if getattr(node,"name",None) in ("h2","h3"):break
                    if getattr(node,"name",None)=="li":
                        entry=node.get_text(" ",strip=True)
                        if len(entry)>15:refs.append(entry)
            for p in papers:
                if p.get("hexagon")==m.group(1):continue
                if any(matches_target(ref,p) for ref in refs):
                    new.append({"target":p["id"],"title":title,"authors":authors,
                                "platform":"hexagon","id":m.group(1),"verified":True,
                                "source":"Verified in HexagonMath HTML bibliography",
                                "url":urljoin(base,href)})
            # The HTML bibliography may be empty despite citations in the PDF.
            pdf_links=[link for link in doc.select("a[href]")
                       if ("pdf"==clean(link.get_text(" ",strip=True))
                           or "download pdf" in clean(link.get_text(" ",strip=True)))]
            if pdf_links and href not in pdf_done:
                pending[href]={"href":href,"pdf_url":urljoin(base,pdf_links[0]["href"]),
                               "title":title,"authors":authors}
            time.sleep(.12)
        nxt=next((a for a in soup.select("a[href]")
                  if "next 100 works" in clean(a.get_text(" ",strip=True))),None)
        if not nxt:break
        listing=urljoin(base,nxt.get("href",""))
    def priority(item):
        title=clean(item["title"])
        score=sum(w in title for w in ("markov","markoff","geodesic","hyperbolic",
              "simple length","norm ball","farey","ortho","dilogarithm","topograph"))
        return (score,item["href"])
    todo=sorted(pending.values(),key=priority,reverse=True)
    checked_pdf=0
    for entry in todo:
        if checked_pdf>=40:break
        href=entry["href"]
        checked_pdf+=1
        entry["attempts"]=int(entry.get("attempts",0))+1
        if entry["attempts"]>3:
            pdf_done.add(href)
            pending.pop(href,None)
            errors.append("Hexagon PDF skipped after three attempts: "+href)
            continue
        try:
            with session.get(entry["pdf_url"],timeout=35,stream=True) as response:
                if response.status_code!=200:continue
                chunks=[];size=0
                for block in response.iter_content(chunk_size=131072):
                    size+=len(block)
                    if size>18_000_000:break
                    chunks.append(block)
            if size>18_000_000:
                errors.append("Hexagon PDF too large: "+href)
                pdf_done.add(href)
                pending.pop(href,None)
                continue
            data=b"".join(chunks)
            if not data.startswith(b"%PDF"):
                errors.append("Hexagon PDF URL returned non-PDF: "+href)
                pdf_done.add(href)
                pending.pop(href,None)
                continue
            reader=PdfReader(BytesIO(data),strict=False)
            tail="\n".join(page.extract_text() or "" for page in
                           list(reader.pages)[-min(18,len(reader.pages)):])
            references=bibliography(tail)
            for p in papers:
                if p.get("hexagon")==re.search(r"(\d{4}\.\d{5})",href).group(1):continue
                if references and matches_target(references,p):
                    new.append({"target":p["id"],"title":entry["title"],
                                "authors":entry.get("authors",""),"platform":"hexagon",
                                "id":re.search(r"(\d{4}\.\d{5})",href).group(1),
                                "verified":True,"source":"Verified in HexagonMath PDF bibliography",
                                "url":urljoin(base,href)})
            pdf_done.add(href)
            pending.pop(href,None)
        except Exception as exc:
            # Preserve unscanned items for the next run.
            errors.append("Hexagon PDF "+href+": "+str(exc)[:140])
            continue
    STATE.write_text(json.dumps({"hexagon_pages_checked":sorted(checked),
                                "hexagon_pdf_checked":sorted(pdf_done),
                                "hexagon_pdf_pending":list(pending.values()),
                                "last_checked_utc":datetime.now(timezone.utc).isoformat(timespec="seconds")},
                                indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return new

def opencitations(p):
    """OpenCitations incoming DOI edges; independent bibliographic index."""
    if not p.get("doi"):return []
    data=get("https://api.opencitations.net/index/v2/citations/doi:"+p["doi"])
    if not isinstance(data,list):return []
    out=[]
    for item in data[:500]:
        match=re.search(r"doi:(10\.\S+)",item.get("citing",""),flags=re.I)
        if not match:continue
        doi=match.group(1).rstrip(".,;")
        response=get("https://api.crossref.org/works/"+quote(doi,safe="/"))
        meta=response.get("message",{}) if isinstance(response,dict) else {}
        title=(meta.get("title") or [""])[0]
        if not title:continue
        author="; ".join(" ".join([a.get("given",""),a.get("family","")]).strip() for a in meta.get("author",[]))
        out.append({"target":p["id"],"title":title,"authors":author,"doi":doi,
                    "platform":"doi","id":doi,"url":"https://doi.org/"+doi,
                    "source":"OpenCitations reference edge (Crossref metadata)","verified":False})
        time.sleep(.1)
    return out

def zenodo_pdf_scan(papers):
    """Targeted Zenodo API search followed by real PDF reference verification."""
    from io import BytesIO
    from pypdf import PdfReader
    verified=[]
    for p in papers:
        queries=[p["title"]]
        if p.get("arxiv"):queries.append(p["arxiv"])
        if p.get("doi"):queries.append(p["doi"])
        count=0
        for query in queries:
            data=get("https://zenodo.org/api/records",{"q":'"'+query+'"',"size":10})
            if not isinstance(data,dict):continue
            for item in data.get("hits",{}).get("hits",[]):
                if count>=5:break
                meta=item.get("metadata") or {}
                title=meta.get("title","")
                if not title or clean(title)==clean(p["title"]):continue
                description=BeautifulSoup(meta.get("description",""),"html.parser").get_text(" ",strip=True)
                if not matches_target(description,p):continue
                for file in item.get("files",[]):
                    if count>=5:break
                    if not str(file.get("key","")).lower().endswith(".pdf"):continue
                    location=(file.get("links") or {}).get("self")
                    if not location:continue
                    try:
                        response=session.get(location,timeout=30)
                        if response.status_code!=200 or len(response.content)>18_000_000:continue
                        if not response.content.startswith(b"%PDF"):continue
                        count+=1
                        reader=PdfReader(BytesIO(response.content),strict=False)
                        tail="\n".join(x.extract_text() or "" for x in list(reader.pages)[-min(16,len(reader.pages)):])
                        if not matches_target(bibliography(tail),p):continue
                        ident=str(item.get("id",""))
                        verified.append({"target":p["id"],"title":title,
                                         "authors":"; ".join(a.get("name","") for a in meta.get("creators",[])),
                                         "platform":"zenodo","id":ident,
                                         "doi":item.get("doi",""),"verified":True,
                                         "source":"Verified in Zenodo-hosted PDF bibliography",
                                         "url":"https://zenodo.org/records/"+ident})
                    except Exception as exc:
                        errors.append("Zenodo verification: "+str(exc)[:120])
    return verified

def main():
    old={}
    if DEST.exists():
        try:old=json.loads(DEST.read_text(encoding="utf-8"))
        except ValueError:pass
    candidates=[c for c in old.get("citations",[]) if not c.get("verified")]
    for p in PAPERS:
        for func in (openalex,semantic,opencitations):
            try:
                items=func(p)
                candidates.extend(items)
                print(p["id"],func.__name__,len(items),flush=True)
            except Exception as exc:
                errors.append(p["id"]+" "+func.__name__+": "+str(exc))
        time.sleep(.2)
    # Promotion to verified requires inspection of a real bibliography.
    new_verified=[]
    for p in PAPERS:
        attempted=0
        for c in merged(x for x in candidates if x.get("target")==p["id"]):
            if c.get("arxiv") and attempted<12:
                attempted+=1
                finding=inspect_arxiv_pdf(p,c)
                if finding:new_verified.append(finding)
    try:
        new_verified.extend(hexagon_scan(PAPERS))
    except Exception as exc:
        errors.append("Hexagon bibliography scan: "+str(exc)[:150])
    try:
        new_verified.extend(zenodo_pdf_scan(PAPERS))
    except Exception as exc:
        errors.append("Zenodo bibliography scan: "+str(exc)[:150])
    already={(c["target"],work_key(c)) for c in SEEDS}
    for c in merged(new_verified):
        if (c["target"],work_key(c)) not in already:
            SEEDS.append(c)
            already.add((c["target"],work_key(c)))
    (DIR/"verified.json").write_text(json.dumps(SEEDS,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    verifiedkeys={(c["target"],work_key(c)) for c in SEEDS}
    candidates=[c for c in merged(candidates) if (c["target"],work_key(c)) not in verifiedkeys]
    data={"generated_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "citations":candidates,"errors":errors[:30],
          "warning":"Indexed citation edges are candidates, not bibliography-verified counts."}
    DEST.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Indexed candidate citation edges:",len(candidates), "Errors:",len(errors),flush=True)

if __name__=="__main__":
    main()
