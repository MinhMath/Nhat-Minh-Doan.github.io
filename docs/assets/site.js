'use strict';
(()=>{
 const script=document.currentScript;

 // Keep old browser-exclusion links working.
 const current=new URL(window.location.href);
 if(current.searchParams.has('owner_dashboard')){
  current.searchParams.delete('owner_dashboard');
  window.history.replaceState(null,'',current.pathname+current.search+current.hash);
 }

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
 // Count deliberate abstract openings from the table.
 document.addEventListener('click',event=>{
  if(!event.isTrusted||event.button!==0)return;
  const summary=event.target.closest?.('summary');
  const details=summary?.parentElement;
  if(!details?.matches('details.abstract-details')||details.open)return;
  const paperId=details.closest('tr[id^="paper-"]')?.id.slice(6);
  if(!paperId)return;
  setTimeout(()=>{
   if(!event.defaultPrevented&&details.open)countAbstractOpen(paperId);
  },0);
 });
 const skipLink=document.querySelector('.skip-link');
 skipLink?.addEventListener('click',event=>{
  if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  const main=document.getElementById('main');
  if(!main)return;
  event.preventDefault();
  main.focus({preventScroll:true});
  main.scrollIntoView({block:'start'});
 });
})();
