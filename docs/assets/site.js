'use strict';
(()=>{
 const script=document.currentScript;

 // Keep old browser-exclusion links working.
 const current=new URL(window.location.href);
 if(current.searchParams.has('owner_dashboard')){
  current.searchParams.delete('owner_dashboard');
  window.history.replaceState(null,'',current.pathname+current.search+current.hash);
 }

 const dialog=document.querySelector('.site-search');
 const input=document.getElementById('site-search-input');
 const results=document.getElementById('search-results');
 let catalogue;
 function getPapers(){
  return catalogue||(catalogue=fetch(script.dataset.catalogue,{cache:'no-store'}).then(r=>{
   if(!r.ok)throw new Error('Unable to load papers');
   return r.json();
  }).catch(error=>{
   catalogue=undefined;
   throw error;
  }));
 }
 const analyticsId='G-0R548MHC6P';
 function publicationKey(value){
  try{
   const url=new URL(value,document.baseURI);
   const host=url.hostname.toLowerCase().replace(/^www\./,'');
   const path=decodeURIComponent(url.pathname).replace(/\/$/,'');
   if(['arxiv.org','export.arxiv.org'].includes(host)){
    const match=path.match(/^\/(?:abs|pdf)\/(.+)$/);
    return match?'arxiv:'+match[1].replace(/\.pdf$/,'').replace(/v\d+$/,'').toLowerCase():null;
   }
   if(['doi.org','dx.doi.org'].includes(host))return 'doi:'+path.slice(1).toLowerCase();
   if(host==='hexagonmath.org')return 'hexagon:'+path.slice(1).replace(/v\d+$/,'').toLowerCase();
  }catch(error){}
  return null;
 }
 let publicationIndex;
 function getPublicationIndex(){
  return publicationIndex||(publicationIndex=getPapers().then(papers=>{
   const index=new Map();
   for(const paper of papers){
    for(const [field,base] of [['doi','https://doi.org/'],['arxiv','https://arxiv.org/abs/'],['hexagon','https://hexagonmath.org/']]){
     if(paper[field])index.set(publicationKey(base+paper[field]),paper);
    }
   }
   return index;
  }).catch(()=>{
   publicationIndex=undefined;
   return new Map();
  }));
 }
 function countPaperClick(event){
  if(event.type==='click'&&event.button!==0)return;
  if(event.type==='auxclick'&&event.button!==1)return;
  if(window.nhatMinhAnalyticsExcluded===true||window['ga-disable-'+analyticsId]===true)return;
  const anchor=event.target.closest?.('a[href]');
  if(!anchor)return;
  const key=publicationKey(anchor.href);
  if(!key)return;
  getPublicationIndex().then(index=>{
   if(window.nhatMinhAnalyticsExcluded===true||window['ga-disable-'+analyticsId]===true)return;
   const paper=index.get(key);
   if(!paper||typeof window.gtag!=='function')return;
   window.gtag('event','paper_click_'+paper.id.toLowerCase().replace(/[^a-z0-9_]/g,'_'),{
    send_to:analyticsId,
    paper_id:paper.id,
    paper_title:(paper.display_title||paper.title).slice(0,100),
    link_url:anchor.href
   });
  });
 }
 document.addEventListener('click',countPaperClick);
 document.addEventListener('auxclick',countPaperClick);
 function analyticsExcluded(){
  return window.nhatMinhAnalyticsExcluded===true||window['ga-disable-'+analyticsId]===true;
 }
 function countAbstractOpen(paperId){
  if(analyticsExcluded())return;
  getPapers().then(papers=>{
   const paper=papers.find(item=>item.id.toLowerCase()===paperId.toLowerCase());
   if(!paper||typeof window.gtag!=='function'||analyticsExcluded())return;
   window.gtag('event','paper_abstract_'+paper.id.toLowerCase().replace(/[^a-z0-9_]/g,'_'),{
    send_to:analyticsId,
    paper_id:paper.id,
    paper_title:(paper.display_title||paper.title).slice(0,100),
    interaction_type:'abstract_open'
   });
  }).catch(()=>{});
 }
 // Count deliberate abstract openings from the table and the selected papers.
 document.addEventListener('click',event=>{
  if(!event.isTrusted||event.button!==0)return;
  const summary=event.target.closest?.('summary');
  const details=summary?.parentElement;
  if(!details?.matches('details.abstract-details')||details.open)return;
  const row=details.closest('tr[id^="paper-"]');
  if(!row)return;
  setTimeout(()=>{
   if(!event.defaultPrevented&&details.open)countAbstractOpen(row.id.slice(6));
  },0);
 });
 function isSameTabClick(event){
  return event.button===0&&!event.metaKey&&!event.ctrlKey&&!event.shiftKey&&!event.altKey;
 }
 function reopenHashLink(event,link){
  if(isSameTabClick(event)&&link.href===location.href){
   event.preventDefault();
   window.dispatchEvent(new HashChangeEvent('hashchange'));
  }
 }
 for(const link of document.querySelectorAll('.homepage-jump')){
  link.addEventListener('click',event=>{
   if(event.isTrusted&&isSameTabClick(event)&&link.dataset.paperAbstract){
    countAbstractOpen(link.dataset.paperAbstract);
   }
   reopenHashLink(event,link);
  });
 }
 for(const button of document.querySelectorAll('.search-open')){
  button.addEventListener('click',()=>{dialog.showModal();input.focus();showResults()});
 }
 document.querySelector('.search-close')?.addEventListener('click',()=>dialog.close());
 dialog?.addEventListener('click',e=>{if(e.target===dialog){const b=dialog.getBoundingClientRect();if(e.clientX<b.left||e.clientX>b.right||e.clientY<b.top||e.clientY>b.bottom)dialog.close()}});
 function searchText(value){
  return String(value||'').normalize('NFKD').toLocaleLowerCase()
   .replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/[‐‑‒–—-]/g,' ');
 }
 let queryId=0;
 async function showResults(){
  const current=++queryId;
  const words=searchText(input.value).trim().split(/\s+/).filter(Boolean);
  results.replaceChildren();
  if(!words.length)return;
  try{
   const papers=await getPapers();if(current!==queryId)return;
   const matches=papers.filter(p=>{
    const text=searchText([p.title,p.display_title,...p.authors,...(p.aliases||[]),p.venue,p.doi,p.arxiv,p.hexagon].join(' '));
    return words.every(word=>text.includes(word));
   });
   if(!matches.length){const p=document.createElement('p');p.className='search-message';p.textContent='No papers found.';results.append(p)}
   for(const p of matches){const a=document.createElement('a');a.className='search-result';a.href='#paper-'+encodeURIComponent(p.id);a.append(document.createTextNode(p.display_title||p.title));const detail=document.createElement('small');detail.textContent=p.authors.join(', ');a.append(detail);a.addEventListener('click',event=>{
    dialog.close();
    reopenHashLink(event,a);
   });results.append(a)}
  }catch{if(current===queryId){results.textContent='Search is unavailable. Please open List of papers on Bio.'}}
 }
 input?.addEventListener('input',showResults);
})();



