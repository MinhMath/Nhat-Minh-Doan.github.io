'use strict';
(()=>{
 const script=document.currentScript;
 const toggle=document.querySelector('.nav-toggle');
 const nav=document.querySelector('.site-navigation');
 toggle?.addEventListener('click',()=>{const open=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(open));toggle.setAttribute('aria-label',open?'Close navigation':'Open navigation');nav.classList.toggle('is-open',open)});
 const dialog=document.querySelector('.site-search');
 const input=document.getElementById('site-search-input');
 const results=document.getElementById('search-results');
 let catalogue;
 const getPapers=()=>catalogue||(catalogue=fetch(script.dataset.catalogue,{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('Unable to load papers');return r.json()}));
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
 const publicationIndex=getPapers().then(papers=>{
  const index=new Map();
  for(const paper of papers){
   for(const [field,base] of [['doi','https://doi.org/'],['arxiv','https://arxiv.org/abs/'],['hexagon','https://hexagonmath.org/']]){
    if(paper[field])index.set(publicationKey(base+paper[field]),paper);
   }
  }
  return index;
 }).catch(()=>new Map());
 function countPaperClick(event){
  if(event.type==='click'&&event.button!==0)return;
  if(event.type==='auxclick'&&event.button!==1)return;
  if(window.nhatMinhAnalyticsExcluded===true||window['ga-disable-'+analyticsId]===true)return;
  const anchor=event.target.closest?.('a[href]');
  if(!anchor)return;
  const key=publicationKey(anchor.href);
  if(!key)return;
  publicationIndex.then(index=>{
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
 document.querySelector('.search-open')?.addEventListener('click',()=>{dialog.showModal();input.focus();showResults()});
 document.querySelector('.search-close')?.addEventListener('click',()=>dialog.close());
 dialog?.addEventListener('click',e=>{if(e.target===dialog){const b=dialog.getBoundingClientRect();if(e.clientX<b.left||e.clientX>b.right||e.clientY<b.top||e.clientY>b.bottom)dialog.close()}});
 let queryId=0;
 async function showResults(){
  const current=++queryId;
  const query=input.value.trim().toLocaleLowerCase();
  results.replaceChildren();
  if(!query){const p=document.createElement('p');p.className='search-message';p.textContent='Search by title, author, or journal.';results.append(p);return}
  try{
   const papers=await getPapers();if(current!==queryId)return;
   const matches=papers.filter(p=>[p.title,p.display_title,...p.authors,p.venue].filter(Boolean).join(' ').toLocaleLowerCase().includes(query));
   if(!matches.length){const p=document.createElement('p');p.className='search-message';p.textContent='No papers found.';results.append(p)}
   for(const p of matches){const a=document.createElement('a');a.className='search-result';a.href=script.dataset.papers+'#paper-'+encodeURIComponent(p.id);a.append(document.createTextNode(p.display_title||p.title));const detail=document.createElement('small');detail.textContent=p.authors.join(', ');a.append(detail);a.addEventListener('click',()=>dialog.close());results.append(a)}
  }catch{if(current===queryId){results.textContent='Search is unavailable. Please open the Papers page.'}}
 }
 input?.addEventListener('input',showResults);
})();


