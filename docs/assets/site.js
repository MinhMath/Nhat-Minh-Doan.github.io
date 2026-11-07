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
