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
from urllib.parse import quote, urlsplit
from citation_identity import clean, work_key, canonicalize as merged

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

RUN_DEADLINE=float("inf")
failed_hosts=set()
sources={}


def within_budget():
    return time.monotonic() < RUN_DEADLINE


def safe_error(message):
    text=str(message)
    for key in ("OPENALEX_API_KEY", "SEMANTIC_SCHOLAR_API_KEY", "OPENCITATIONS_API_KEY"):
        secret=os.getenv(key)
        if secret:
            text=text.replace(secret,"[redacted]")
    return re.sub(r"(?i)(api_key|access_token|token)=([^&\s]+)", r"\1=[redacted]", text)[:300]


def record_error(message):
    message=safe_error(message)
    if message not in errors:
        errors.append(message)


def get(url,params=None,headers=None):
    host=urlsplit(url).netloc
    if host in failed_hosts or not within_budget():
        return None
    failure="request failed"
    for i in range(2):
        if not within_budget():break
        try:
            r=session.get(url,params=params,headers=headers,timeout=min(15,max(1,RUN_DEADLINE-time.monotonic())))
            if r.status_code==404:return None
            if r.status_code in (401,403):
                failure="HTTP "+str(r.status_code)+" (authentication or access required)"
                break
            if r.status_code in (429,500,502,503,504):
                failure="HTTP "+str(r.status_code)
                if i==0:time.sleep(1)
                continue
            r.raise_for_status()
            return r.json()
        except (requests.RequestException,ValueError) as exc:
            failure=type(exc).__name__
    failed_hosts.add(host)
    record_error(host+": "+failure+"; remaining requests to this host deferred until the next run")
    return None

def known(p,work):
    title=clean(work.get("display_name") or work.get("title"))
    variants=[p["title"]]+p.get("aliases",[])
    return any(SequenceMatcher(None,title,clean(v)).ratio()>.86 for v in variants)

def openalex(p):
    out=[]
    token=os.getenv("OPENALEX_API_KEY","")
    auth={}
    headers={"Authorization":"Bearer "+token} if token else {}
    found=set()
    works=[]
    for doi in ([p["doi"]] if p.get("doi") else [])+(["10.48550/arXiv."+p["arxiv"]] if p.get("arxiv") else []):
        work=get("https://api.openalex.org/works/https://doi.org/"+quote(doi,safe="/"),headers=headers)
        if isinstance(work,dict):works.append(work)
    # Search alternate titles as well; older and published versions can be split.
    for title in [p["title"]]+p.get("aliases",[])[:2]:
        if not within_budget():break
        r=get("https://api.openalex.org/works",{"search":title,"per_page":15},headers)
        if not isinstance(r,dict):continue
        for work in r.get("results",[]):
            if not known(p,work):continue
            names=clean(" ".join(x.get("author",{}).get("display_name","") for x in work.get("authorships",[])))
            if "doan" in names:works.append(work)
    for w in works:
        ident=w.get("id","").split("/")[-1]
        if not re.fullmatch(r"W\d+",ident) or ident in found:continue
        found.add(ident)
        for page in range(1,11):
            c=get("https://api.openalex.org/works",{"filter":"cites:"+ident,"per_page":100,"page":page,**auth},headers)
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
        if not within_budget():break
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


def bibliography(text):
    """Extract references, including numbered headings and PDF page prefixes."""
    heading=r"(?im)^[ \t]*(?:\d+[.)]?[ \t]*)?(?:references|bibliography|literature cited)[ \t]*$"
    found=list(re.finditer(heading,text))
    for match in found:
        following=text[match.end():]
        if re.match(r"\s*(?:\[[A-Za-z0-9][^\]\n]{0,24}\]|\d+[.)]\s+[A-Z])",following):
            return following
    return text[found[-1].end():] if found else ""


def reference_entries(text):
    pattern=r"(?m)(?=^[ \t]*\[[A-Za-z0-9][^\]\n]{0,24}\])|\n[ \t]*\n|(?=^[ \t]*\d+[.)][ \t]+[A-Z])"
    return [entry.strip() for entry in re.split(pattern,text) if entry.strip()]


def matches_target(text,p):
    for entry in reference_entries(text):
        compact=clean(entry)
        joined=compact.replace(" ","")
        for key in ("arxiv","hexagon","doi"):
            identifier=p.get(key)
            suffix=r"(?:v\d+)?(?![a-z0-9])" if key in ("arxiv","hexagon") else r"(?![a-z0-9])"
            if identifier and re.search(r"(?<![a-z0-9])"+re.escape(clean(identifier))+suffix,compact):
                return True
        for variant in [p["title"]]+p.get("aliases",[]):
            normalized=clean(variant)
            if not normalized:continue
            if normalized not in compact and normalized.replace(" ","") not in joined:continue
            # Short titles need the target author's surname in the same entry.
            if len(normalized)<=40 and not re.search(r"\bdoan\b",compact):continue
            # A reference to Some arithmetic aspects of ortho-integral surfaces
            # must not also count as a reference to Ortho-integral surfaces.
            shadowed=False
            for other in PAPERS:
                if other.get("id")==p.get("id"):continue
                for title in [other["title"]]+other.get("aliases",[]):
                    longer=clean(title)
                    if len(longer)>len(normalized) and normalized in longer and longer.replace(" ","") in joined:
                        shadowed=True
            if not shadowed:return True
    return False


def evidence_excerpt(text,p):
    for entry in reference_entries(text):
        if not matches_target(entry,p):continue
        compact=" ".join(entry.split())
        if len(compact)<=650:return compact
        lines=entry.splitlines()
        for i in range(len(lines)):
            window=" ".join(lines[max(0,i-2):i+4])
            if matches_target(window,p) and len(window)<=650:
                return " ".join(window.split())
    return ""


PDF_CACHE={}


def pdf_bibliography(url):
    """Read one public PDF once per run and retain reproducible provenance."""
    if url in PDF_CACHE:return PDF_CACHE[url]
    if not within_budget():return None
    from io import BytesIO
    from hashlib import sha256
    from pypdf import PdfReader
    try:
        with session.get(url,timeout=28,stream=True) as response:
            if response.status_code!=200:
                record_error("PDF HTTP "+str(response.status_code)+": "+url)
                PDF_CACHE[url]=None
                return None
            chunks=[];size=0
            for block in response.iter_content(chunk_size=131072):
                size+=len(block)
                if size>18_000_000:
                    record_error("PDF exceeds size limit: "+url)
                    PDF_CACHE[url]=None
                    return None
                chunks.append(block)
        data=b"".join(chunks)
        if not data.startswith(b"%PDF"):
            record_error("PDF URL returned non-PDF: "+url)
            PDF_CACHE[url]=None
            return None
        reader=PdfReader(BytesIO(data),strict=False)
        start=max(0,len(reader.pages)-24)
        tail="\n".join(page.extract_text() or "" for page in list(reader.pages)[start:])
        refs=bibliography(tail)
        first=reader.pages[0].extract_text() or ""
        version=re.search(r"arXiv[:\s]+(\d{4}\.\d{4,5}v\d+)",first,re.I)
        result={"references":refs,"evidence_url":url,"evidence_sha256":sha256(data).hexdigest(),
                "evidence_version":version.group(1) if version else "",
                "checked_utc":datetime.now(timezone.utc).isoformat(timespec="seconds")}
        if not refs:record_error("Reference heading not found in PDF: "+url)
        PDF_CACHE[url]=result
        return result
    except Exception as exc:
        record_error("PDF verification "+url+": "+str(exc)[:120])
        PDF_CACHE[url]=None
        return None

def same_as_target(p,c):
    from citation_identity import identifiers
    return bool(identifiers(p) & identifiers(c)) or clean(p["title"])==clean(c.get("title"))

def inspect_arxiv_pdf(p,c):
    aid=c.get("arxiv") or (c.get("id") if c.get("platform")=="arxiv" else "")
    if not aid or same_as_target(p,c):return None
    document=pdf_bibliography("https://arxiv.org/pdf/"+aid)
    if document and document["references"] and matches_target(document["references"],p):
        return {**c,**{k:v for k,v in document.items() if k!="references"},
                "verified":True,"source":"Verified in arXiv PDF bibliography",
                "url":"https://arxiv.org/abs/"+aid,
                "evidence_excerpt":evidence_excerpt(document["references"],p)}
    return None


def bibliography_sources():
    sources=[]
    for paper in PAPERS:
        if paper.get("arxiv"):
            sources.append({**paper,"platform":"arxiv","id":paper["arxiv"],
                            "authors":"; ".join(paper.get("authors",[]))})
    extra=DIR/"citing_sources.json"
    if extra.exists():sources.extend(json.loads(extra.read_text(encoding="utf-8")))
    return sources


def scan_known_bibliographies(candidates,verified):
    """Check known manuscripts directly, including citations missing from indexes."""
    status=sources.setdefault("known_bibliographies",{"status":"running","papers_checked":0,"verified_records":0})
    for source in bibliography_sources():
        if not within_budget():
            status["status"]="deferred_time_budget"
            break
        aid=source.get("arxiv")
        url=source.get("pdf_url") or ("https://arxiv.org/pdf/"+aid if aid else "")
        if not url:continue
        document=pdf_bibliography(url)
        if not document or not document["references"]:continue
        status["papers_checked"]+=1
        for paper in PAPERS:
            if same_as_target(paper,source) or not matches_target(document["references"],paper):continue
            verified.append({**source,"target":paper["id"],"verified":True,
                             "source":"Verified by direct bibliography inspection",
                             "url":source.get("url") or ("https://arxiv.org/abs/"+aid if aid else url),
                             **{k:v for k,v in document.items() if k!="references"},
                             "evidence_excerpt":evidence_excerpt(document["references"],paper)})
            status["verified_records"]+=1
        checkpoint(candidates,verified,"running")
    else:status["status"]="completed_requests"

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
    for _ in range(3):
        if listing in seen_pages or not within_budget():break
        seen_pages.add(listing)
        try:
            r=session.get(listing,timeout=25)
            if r.status_code!=200:
                record_error("Hexagon catalog HTTP "+str(r.status_code))
                break
            soup=BeautifulSoup(r.text,"html.parser")
        except requests.RequestException as exc:
            record_error("Hexagon catalog: "+str(exc)[:160])
            break
        for a in soup.select("a[href]"):
            if not within_budget():break
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
                                "url":urljoin(base,href),
                                "evidence_url":urljoin(base,href),
                                "evidence_excerpt":next((ref[:650] for ref in refs if matches_target(ref,p)),""),
                                "checked_utc":datetime.now(timezone.utc).isoformat(timespec="seconds")})
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
        if checked_pdf>=12 or not within_budget():break
        href=entry["href"]
        checked_pdf+=1
        entry["attempts"]=int(entry.get("attempts",0))+1
        if entry["attempts"]>3:
            pdf_done.add(href)
            pending.pop(href,None)
            record_error("Hexagon PDF skipped after three attempts: "+href)
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
                record_error("Hexagon PDF too large: "+href)
                pdf_done.add(href)
                pending.pop(href,None)
                continue
            data=b"".join(chunks)
            if not data.startswith(b"%PDF"):
                record_error("Hexagon PDF URL returned non-PDF: "+href)
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
                                "url":urljoin(base,href),
                                "evidence_url":entry["pdf_url"],
                                "evidence_excerpt":evidence_excerpt(references,p),
                                "checked_utc":datetime.now(timezone.utc).isoformat(timespec="seconds")})
            pdf_done.add(href)
            pending.pop(href,None)
        except Exception as exc:
            # Preserve unscanned items for the next run.
            record_error("Hexagon PDF "+href+": "+str(exc)[:140])
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
        if not within_budget():break
        queries=[p["title"]]
        if p.get("arxiv"):queries.append(p["arxiv"])
        if p.get("doi"):queries.append(p["doi"])
        count=0
        for query in queries:
            if not within_budget():break
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
                                         "url":"https://zenodo.org/records/"+ident,
                                         "evidence_url":location,
                                         "evidence_excerpt":evidence_excerpt(bibliography(tail),p),
                                         "checked_utc":datetime.now(timezone.utc).isoformat(timespec="seconds")})
                    except Exception as exc:
                        record_error("Zenodo verification: "+str(exc)[:120])
    return verified

def atomic_json(path,data):
    temporary=path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    temporary.replace(path)


def checkpoint(candidates,verified,status):
    # Count all sources together so a preprint identifier can bridge a DOI edge.
    rows=merged(verified+candidates)
    verified[:]=[r for r in rows if r.get("verified")]
    candidates[:]=[r for r in rows if not r.get("verified")]
    atomic_json(DIR/"verified.json",verified)
    atomic_json(DEST,{"generated_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "collection_status":status,"sources":sources,
                     "citations":candidates,"errors":errors[-100:],
                     "warning":"Indexed edges are candidates. Partial or failed coverage is not evidence of zero citations."})


def main():
    global RUN_DEADLINE
    RUN_DEADLINE=time.monotonic()+int(os.getenv("CITATION_SCAN_SECONDS","720"))
    errors.clear();failed_hosts.clear();sources.clear();PDF_CACHE.clear()
    old={}
    if DEST.exists():
        try:old=json.loads(DEST.read_text(encoding="utf-8"))
        except ValueError:pass
    candidates=old.get("citations",[])
    verified=list(SEEDS)
    # Rotate target order after interrupted runs so recent papers cannot starve
    # older publications of their turn at each source.
    state={}
    if STATE.exists():
        try:state=json.loads(STATE.read_text(encoding="utf-8"))
        except ValueError:pass
    offset=int(state.get("paper_offset",0))%len(PAPERS)
    ordered=PAPERS[offset:]+PAPERS[:offset]
    last_offset=offset
    try:
        scan_known_bibliographies(candidates,verified)
        for number,p in enumerate(ordered):
            if not within_budget():break
            last_offset=(offset+number+1)%len(PAPERS)
            for func in (openalex,semantic,opencitations):
                if not within_budget():break
                host={"openalex":"api.openalex.org","semantic":"api.semanticscholar.org","opencitations":"api.opencitations.net"}[func.__name__]
                status=sources.setdefault(func.__name__,{"papers_attempted":0,"new_records":0,"status":"running"})
                if host in failed_hosts:
                    status["status"]="deferred_after_error"
                    continue
                before=len(errors)
                status["papers_attempted"]+=1
                try:
                    items=func(p)
                    candidates.extend(c for c in items if not same_as_target(p,c))
                    status["new_records"]+=len(items)
                    status["status"]="partial" if len(errors)>before else "completed_requests"
                    print(p["id"],func.__name__,len(items),flush=True)
                except Exception as exc:
                    record_error(p["id"]+" "+func.__name__+": "+str(exc))
                    status["status"]="partial"
                checkpoint(candidates,verified,"running")
        for p in PAPERS:
            if not within_budget():break
            attempted=0
            retry_evidence=[c for c in verified if c.get("target")==p["id"]
                            and not matches_target(c.get("evidence_excerpt",""),p)]
            for c in merged(c for c in candidates+retry_evidence if c.get("target")==p["id"]):
                if not within_budget():break
                if (c.get("arxiv") or c.get("platform")=="arxiv") and attempted<12:
                    attempted+=1
                    if not c.get("arxiv"):c["arxiv"]=c["id"]
                    finding=inspect_arxiv_pdf(p,c)
                    if finding:verified.append(finding)
            checkpoint(candidates,verified,"running")
        for label,func in (("hexagon",hexagon_scan),("zenodo",zenodo_pdf_scan)):
            if not within_budget():
                sources[label]={"status":"deferred_time_budget"}
                continue
            before=len(errors)
            try:
                items=func(PAPERS)
                verified.extend(items)
                sources[label]={"status":"partial" if len(errors)>before else "completed_requests","verified_records":len(items)}
            except Exception as exc:
                record_error(label+": "+str(exc))
                sources[label]={"status":"partial"}
            checkpoint(candidates,verified,"running")
    finally:
        # hexagon_scan may have updated the same state file.
        if STATE.exists():
            try:state=json.loads(STATE.read_text(encoding="utf-8"))
            except ValueError:pass
        state["paper_offset"]=last_offset
        atomic_json(STATE,state)
        partial=bool(errors) or not within_budget()
        checkpoint(candidates,verified,"partial" if partial else "completed_bounded_scan")
        print("Saved verified relationships:",len(verified),"Candidates:",len(candidates),"Errors:",len(errors),flush=True)


if __name__=="__main__":
    main()
