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

def main():
    old={}
    if DEST.exists():
        try:old=json.loads(DEST.read_text(encoding="utf-8"))
        except ValueError:pass
    candidates=[c for c in old.get("citations",[]) if not c.get("verified")]
    for p in PAPERS:
        for func in (openalex,semantic):
            try:
                items=func(p)
                candidates.extend(items)
                print(p["id"],func.__name__,len(items),flush=True)
            except Exception as exc:
                errors.append(p["id"]+" "+func.__name__+": "+str(exc))
        time.sleep(.2)
    verifiedkeys={(c["target"],work_key(c)) for c in SEEDS}
    candidates=[c for c in merged(candidates) if (c["target"],work_key(c)) not in verifiedkeys]
    data={"generated_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "citations":candidates,"errors":errors[:30],
          "warning":"Indexed citation edges are candidates, not bibliography-verified counts."}
    DEST.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Indexed candidate citation edges:",len(candidates), "Errors:",len(errors),flush=True)

if __name__=="__main__":
    main()
