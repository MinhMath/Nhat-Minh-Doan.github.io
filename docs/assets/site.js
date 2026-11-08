'use strict';
(()=>{
 const script=document.currentScript;

 // This browser preference reveals a shortcut; the private Site enforces report access.
 function setupPrivateShortcut(){
  const ownerKey='nhat-minh-doan:private-dashboard';
  const current=new URL(window.location.href);
  const preference=current.searchParams.get('owner_dashboard');
  let enabled=preference==='1';
  try{
   if(preference==='1'){
    localStorage.setItem(ownerKey,'1');
    localStorage.setItem('nhat-minh-doan:analytics-excluded','1');
    window.nhatMinhAnalyticsExcluded=true;
    window['ga-disable-G-0R548MHC6P']=true;
   }else if(preference==='0')localStorage.removeItem(ownerKey);
   enabled=enabled||localStorage.getItem(ownerKey)==='1';
  }catch(error){}
  if(preference!==null){current.searchParams.delete('owner_dashboard');window.history.replaceState(null,'',current.pathname+current.search+current.hash)}
  if(!enabled)return;
  const style=document.createElement('style');
  style.textContent='.private-dashboard-shortcut{position:fixed;right:14px;bottom:14px;z-index:30;display:grid;place-items:center;width:27px;height:27px;border:1px solid #dce3eb;border-radius:50%;color:#60758c;background:#fff;opacity:.6;box-shadow:0 1px 5px #0000000a}.private-dashboard-shortcut:hover,.private-dashboard-shortcut:focus-visible{opacity:1;color:#1155cc;outline:2px solid #1155cc;outline-offset:3px}.private-dashboard-shortcut svg{display:block}';
  document.head.appendChild(style);
  const link=document.createElement('a');
  link.className='private-dashboard-shortcut';
  link.href='https://minh-paper-statistics.minhminhminh.chatgpt.site';
  link.target='_blank';link.rel='noopener noreferrer';
  link.setAttribute('aria-label','Private paper statistics');
  link.title='Private paper statistics';
  link.innerHTML='<svg width="13" height="13" viewBox="0 0 20 20" fill="none" aria-hidden="true"><rect x="4" y="9" width="12" height="8" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M6 9V6a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="1.6"/></svg>';
  document.body.appendChild(link);
 }
 setupPrivateShortcut();

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
 // Count deliberate abstract openings, excluding closes and automatic deep-link opens.
 document.addEventListener('click',event=>{
  if(!event.isTrusted||event.button!==0)return;
  const summary=event.target.closest?.('summary');
  const details=summary?.parentElement;
  if(!details?.matches('details.abstract-details')||details.open)return;
  const row=details.closest('tr[id^="paper-"]');
  if(!row)return;
  const paperId=row.id.slice(6);
  setTimeout(()=>{
   if(event.defaultPrevented||!details.open||window.nhatMinhAnalyticsExcluded===true||window['ga-disable-'+analyticsId]===true)return;
   getPapers().then(papers=>{
    const paper=papers.find(item=>item.id.toLowerCase()===paperId.toLowerCase());
    if(!paper||typeof window.gtag!=='function'||window.nhatMinhAnalyticsExcluded===true||window['ga-disable-'+analyticsId]===true)return;
    window.gtag('event','paper_abstract_'+paper.id.toLowerCase().replace(/[^a-z0-9_]/g,'_'),{
     send_to:analyticsId,
     paper_id:paper.id,
     paper_title:(paper.display_title||paper.title).slice(0,100),
     interaction_type:'abstract_open'
    });
   }).catch(()=>{});
  },0);
 });
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



