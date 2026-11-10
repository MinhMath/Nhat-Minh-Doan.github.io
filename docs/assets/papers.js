'use strict';
(()=>{
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safe=value=>{try{const url=new URL(value);return ['https:','http:'].includes(url.protocol)?url.href:'#'}catch{return '#'}};
const link=(url,label,attributes='')=>'<a href="'+esc(safe(url))+'" target="_blank" rel="noopener noreferrer" '+attributes+'>'+esc(label)+'</a>';
const paperUrl=p=>p.doi?'https://doi.org/'+p.doi:p.arxiv?'https://arxiv.org/abs/'+p.arxiv:p.hexagon?'https://hexagonmath.org/'+p.hexagon:'#';
const sourceUrl=c=>c.url||(c.arxiv?'https://arxiv.org/abs/'+c.arxiv:c.hexagon?'https://hexagonmath.org/'+c.hexagon:c.platform==='arxiv'?'https://arxiv.org/abs/'+c.id:c.platform==='hexagon'?'https://hexagonmath.org/'+c.id:c.doi?'https://doi.org/'+c.doi:'#');
const authors=value=>(Array.isArray(value)?value:String(value||'').split(';')).map(name=>{
 const parts=String(name).split(',').map(part=>part.trim());
 return parts.length===2?parts[1]+' '+parts[0]:String(name).trim();
}).filter(Boolean).join(', ');
const dateText=value=>{if(!/^\d{4}-\d{2}-\d{2}$/.test(value||''))return '—';return new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}).format(new Date(value+'T00:00:00Z'))};
const newestFirst=(a,b)=>(b.first_online||'').localeCompare(a.first_online||'')||(a.display_title||a.title).localeCompare(b.display_title||b.title);
const dateLink=p=>p.first_online?link(p.first_online_source||sourceUrl(p),dateText(p.first_online),'title="'+esc(p.first_online_note||'First documented public posting')+'"'):'—';
const punctuate=value=>{const text=String(value||'').trim();return text&&!/[.!?]$/.test(text)?text+'.':text};
const abstractDetails=p=>{
 const text=p.abstract?'<div class="abstract-text">'+esc(p.abstract)+'</div>':'';
 const source=link(p.abstract_source||sourceUrl(p),p.abstract_kind==='summary'?'Abstract summary':'Source');
 return '<details class="abstract-details"><summary>Abstract</summary><div class="detail-content">'+text+'<div class="abstract-source">'+source+'</div></div></details>';
};
const bibliography=(p,url,attributes='')=>{
 const byline=authors(p.authors);
 const venue=String(p.venue||'').replace(/^HexagonMath\s*[,;:]?\s*/i,'');
 const title=punctuate(p.display_title||p.title);
 const separator=byline&&venue?', ':'';
 const publication=punctuate(venue);
 const metadata=esc(byline)+separator+(publication?'<em>'+esc(publication)+'</em>':'');
 return '<div class="paper">'+link(url,title,attributes)+'</div>'
  +'<div class="paper-meta">'+metadata+'</div>'
  +abstractDetails(p);
};

function citationYear(citation){
 const year=Number(citation.year);
 if(Number.isInteger(year)&&year>=1900&&year<=2100)return year;
 const venueYear=String(citation.venue||'').match(/\b((?:19|20)\d{2})\b/);
 if(venueYear)return Number(venueYear[1]);
 const onlineYear=String(citation.first_online||'').match(/^(\d{4})-/);
 return onlineYear?Number(onlineYear[1]):null;
}
function renderPaperInsights(data){
 const citations=data.citations.filter(citation=>citation.verified||citation.listing_confirmed);
 const counts=new Map();
 for(const citation of citations){
  const year=citationYear(citation);
  if(year===null)continue;
  counts.set(year,(counts.get(year)||0)+1);
 }
 const knownYears=[...counts.keys()].sort((a,b)=>a-b);
 const years=knownYears.length?Array.from({length:knownYears.at(-1)-knownYears[0]+1},(_,index)=>knownYears[0]+index):[];
 if(years.length){
  const maximum=Math.max(...counts.values());
  const ceiling=Math.max(2,Math.ceil(maximum/5)*5);
  const left=28,right=370,top=16,bottom=130,height=bottom-top,step=(right-left)/years.length;
  const ticks=[0,ceiling/2,ceiling];
  const grid=ticks.map(value=>{
   const y=bottom-height*value/ceiling;
   return '<line class="chart-grid" x1="'+left+'" y1="'+y+'" x2="'+right+'" y2="'+y+'"/><text x="'+(left-8)+'" y="'+(y+4)+'" text-anchor="end">'+value+'</text>';
  }).join('');
  const bars=years.map((year,index)=>{
   const value=counts.get(year)||0,x=left+step*(index+0.5),barHeight=height*value/ceiling,width=Math.min(28,step*0.55);
   const label=year+': '+value+' citation'+(value===1?'':'s')+'. Show citation records.';
   return '<g class="citation-year-button" role="button" tabindex="0" data-citation-year="'+year+'" aria-controls="citation-year-records" aria-expanded="false" aria-label="'+label+'"><title>'+label+'</title><rect class="chart-target" x="'+(left+step*index+2)+'" y="4" width="'+(step-4)+'" height="150" rx="3"/><rect class="chart-bar" x="'+(x-width/2)+'" y="'+(bottom-barHeight)+'" width="'+width+'" height="'+barHeight+'"/><text class="bar-value" x="'+x+'" y="'+(bottom-barHeight-6)+'" text-anchor="middle">'+value+'</text><text x="'+x+'" y="'+(bottom+21)+'" text-anchor="middle">'+year+'</text></g>';
  }).join('');
  const description=years.map(year=>year+': '+(counts.get(year)||0)).join('; ');
  document.getElementById('citation-chart').innerHTML='<svg class="citation-chart" viewBox="0 0 380 160" role="group" aria-labelledby="citation-svg-title citation-svg-description"><title id="citation-svg-title">Citations by year</title><desc id="citation-svg-description">'+description+'</desc>'+grid+bars+'</svg>';
 }else{
  document.getElementById('citation-chart').textContent='No dated citations yet.';
 }
 const paperTitles=new Map(data.papers.map(paper=>[paper.id,paper.display_title||paper.title]));
 document.getElementById('citation-year-records').innerHTML=years.map(year=>{
  const records=citations.filter(citation=>citationYear(citation)===year);
  const works=new Map();
  for(const citation of records){
   const key=citation.work_id||sourceUrl(citation);
   if(!works.has(key))works.set(key,{citation,targets:[]});
   works.get(key).targets.push(paperTitles.get(citation.target)||citation.target);
  }
  const items=[...works.values()].map(({citation,targets})=>'<li>'+link(sourceUrl(citation),citation.display_title||citation.title)+'<span class="citation-work-count"> — '+targets.length+' citation'+(targets.length===1?'':'s')+'</span><small>Cites: '+targets.map(esc).join('; ')+'. '+'</small></li>').join('');
  return '<section class="citation-year-audit" data-citation-year-records="'+year+'" hidden><h3>'+year+': '+records.length+' citation'+(records.length===1?'':'s')+' from '+works.size+' citing paper'+(works.size===1?'':'s')+'</h3><ol>'+items+'</ol></section>';
 }).join('');
 const collaborators=new Map();
 for(const paper of data.papers){
  for(const name of new Set((paper.authors||[]).map(name=>authors([name])))){
   if(!name||name==='Nhat Minh Doan')continue;
   collaborators.set(name,(collaborators.get(name)||0)+1);
  }
 }
 const sorted=[...collaborators].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'en'));
 document.getElementById('coauthor-list').innerHTML=sorted.map(([name,count])=>'<li><span class="coauthor-name">'+esc(name)+'</span><span class="joint-count" aria-label="'+count+' joint paper'+(count===1?'':'s')+'">'+count+'</span></li>').join('');
 document.getElementById('paper-insights').hidden=false;
}

const citationChart=document.getElementById('citation-chart');
function toggleCitationYear(button){
 const panel=document.getElementById('citation-year-records');
 const opening=button.getAttribute('aria-expanded')!=='true';
 const year=button.dataset.citationYear;
 citationChart.querySelectorAll('[data-citation-year]').forEach(bar=>bar.setAttribute('aria-expanded',String(opening&&bar===button)));
 panel.querySelectorAll('[data-citation-year-records]').forEach(section=>{section.hidden=!opening||section.dataset.citationYearRecords!==year});
 panel.hidden=!opening;
}
citationChart?.addEventListener('click',event=>{
 const button=event.target.closest('[data-citation-year]');
 if(button)toggleCitationYear(button);
});
citationChart?.addEventListener('keydown',event=>{
 if(event.key!=='Enter'&&event.key!==' ')return;
 const button=event.target.closest('[data-citation-year]');
 if(!button)return;
 event.preventDefault();
 toggleCitationYear(button);
});

// Mathematics is loaded only when an opened details panel needs it.
let mathReady,mathQueue=Promise.resolve();
function loadMath(){
 if(!mathReady)mathReady=new Promise((resolve,reject)=>{
  window.MathJax={tex:{inlineMath:[['$','$'],['\\(','\\)']],displayMath:[['$$','$$'],['\\[','\\]']]},startup:{typeset:false}};
  const script=document.createElement('script');script.src='https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js';script.async=true;
  script.onload=()=>window.MathJax.startup.promise.then(resolve,reject);script.onerror=reject;document.head.appendChild(script);
 });
 return mathReady;
}
const tableBody=document.getElementById('paper-rows');

function installPaperSorting(data){
 const table=tableBody.closest('table');
 const headers=[...table.querySelectorAll('thead th')];
 const columns=[{key:'date',header:headers[1],label:'First online'},{key:'citations',header:headers[2],label:'Cited by'}];
 const papersById=new Map(data.papers.map(paper=>[paper.id,paper]));
 const citationCounts=new Map();
 for(const citation of data.citations){
  if(citation.verified||citation.listing_confirmed)citationCounts.set(citation.target,(citationCounts.get(citation.target)||0)+1);
 }
 let group={heading:null,entries:[]};
 const groups=[group];
 for(const row of [...tableBody.children]){
  if(row.classList.contains('paper-section')){
   group={heading:row,entries:[]};groups.push(group);
  }else if(row.id.startsWith('paper-')){
   const id=row.id.slice(6);
   group.entries.push({row,paper:papersById.get(id),citingRow:document.getElementById('cited-'+id)});
  }
 }
 let sortKey='citations',sortDirection='descending';
 const status=document.createElement('p');
 status.className='sort-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');
 table.after(status);
 function updateHeaders(){
  for(const column of columns){
   const active=column.key===sortKey;
   if(active)column.header.setAttribute('aria-sort',sortDirection);
   else column.header.removeAttribute('aria-sort');
   const icon=column.button.querySelector('.sort-indicator');
   icon.textContent=active?(sortDirection==='descending'?'↓':'↑'):'↕';
   const next=active&&sortDirection==='descending'?'ascending':'descending';
   column.button.title=column.key==='date'?(next==='descending'?'Sort newest first':'Sort oldest first'):(next==='descending'?'Sort highest citation count first':'Sort lowest citation count first');
  }
 }
 function compare(a,b){
  let difference;
  if(sortKey==='citations'){
   difference=(citationCounts.get(a.id)||0)-(citationCounts.get(b.id)||0);
  }else{
   const dateA=/^\d{4}-\d{2}-\d{2}$/.test(a.first_online||'')?a.first_online:'';
   const dateB=/^\d{4}-\d{2}-\d{2}$/.test(b.first_online||'')?b.first_online:'';
   if(!dateA||!dateB)return dateA?-1:dateB?1:newestFirst(a,b);
   difference=dateA.localeCompare(dateB);
  }
  return (sortDirection==='descending'?-difference:difference)||newestFirst(a,b)||a.id.localeCompare(b.id);
 }
 function sortRows(){
   const fragment=document.createDocumentFragment();
   for(const section of groups){
    if(section.heading)fragment.append(section.heading);
    for(const entry of [...section.entries].sort((a,b)=>compare(a.paper,b.paper))){
     fragment.append(entry.row);
     if(entry.citingRow)fragment.append(entry.citingRow);
    }
   }
   tableBody.append(fragment);
 }
 for(const column of columns){
  const button=document.createElement('button');
  button.type='button';button.className='paper-sort';button.setAttribute('aria-controls','paper-rows');
  button.append(document.createTextNode(column.label+' '));
  const icon=document.createElement('span');icon.className='sort-indicator';icon.setAttribute('aria-hidden','true');button.append(icon);
  column.header.replaceChildren(button);column.button=button;
  button.addEventListener('click',()=>{
   sortDirection=sortKey===column.key&&sortDirection==='descending'?'ascending':'descending';
   sortKey=column.key;
   sortRows();
   updateHeaders();
   status.textContent='Papers sorted by '+(sortKey==='date'?'first online date, '+(sortDirection==='descending'?'newest first.':'oldest first.'):'citation count, '+(sortDirection==='descending'?'highest first.':'lowest first.'));
  });
 }
 sortRows();
 updateHeaders();
}

tableBody.addEventListener('click',event=>{
 const button=event.target.closest('.citation-toggle');if(!button)return;
 const row=document.getElementById(button.getAttribute('aria-controls'));
 const opening=button.getAttribute('aria-expanded')!=='true';row.hidden=!opening;button.setAttribute('aria-expanded',String(opening));
});
tableBody.addEventListener('toggle',event=>{
 const panel=event.target;
 if(!panel.matches('.abstract-details')||!panel.open||panel.dataset.mathDone)return;
 const abstract=panel.querySelector('.abstract-text');if(!abstract||!/[\$\\]/.test(abstract.textContent))return;
 mathQueue=mathQueue.then(()=>loadMath()).then(()=>window.MathJax.typesetPromise([abstract])).then(()=>{panel.dataset.mathDone='true'}).catch(()=>{});
},true);
const papersPanel=document.getElementById('papers');
let requestedPapers=false;
function loadPapers(){
 if(requestedPapers)return;
 requestedPapers=true;
 fetch('ledger.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error();return r.json()}).then(data=>{
  const allPapers=[...data.papers].sort(newestFirst);
  const renderPaper=p=>{
   const citations=data.citations.filter(c=>c.target===p.id&&(c.verified||c.listing_confirmed)).sort(newestFirst);
   const id='cited-'+p.id;
   const count=citations.length;
   const label=count+' citing '+(count===1?'work':'works');
   const control=count?'<button type="button" class="citation-toggle" aria-expanded="false" aria-controls="'+esc(id)+'" aria-label="'+label+'">'+count+'</button>':'<span class="empty">—</span>';
   const main='<tr id="paper-'+esc(p.id)+'"><td><div class="paper-copy">'+bibliography(p,paperUrl(p))+'</div></td><td class="date">'+dateLink(p)+'</td><td class="citation-count">'+control+'</td></tr>';
   const list=citations.length?'<tr class="citing-row" id="'+esc(id)+'" hidden><td colspan="3"><ul class="citation-list">'+citations.map(c=>'<li><div class="citing-heading"><div class="paper-copy">'+bibliography(c,sourceUrl(c),'title="'+esc(c.bibliography_status||'Bibliography reference verified')+'"')+'</div><div class="citing-date">'+dateLink(c)+'</div></div></li>').join('')+'</ul></td></tr>':'';
   return main+list;
  };
  const sections=papersPanel?[
   {papers:allPapers.filter(p=>p.section!=='other')},
   {title:'Other writings',papers:allPapers.filter(p=>p.section==='other')}
  ]:[{papers:allPapers}];
  tableBody.innerHTML=sections.filter(section=>section.papers.length).map(section=>
   (section.title?'<tr class="paper-section"><td colspan="3"><h2>'+esc(section.title)+'</h2></td></tr>':'')+section.papers.map(renderPaper).join('')
  ).join('');
  installPaperSorting(data);
  document.getElementById('totals').innerHTML='<span>Total citations: <strong>'+data.counts.total_citations+'</strong></span>';
  if(citationChart)renderPaperInsights(data);
  if(!papersPanel||papersPanel.open)selectPaperFromHash();
}).catch(()=>{const error=document.createElement('p');error.setAttribute('role','alert');error.textContent='Papers could not be loaded. Please refresh the page.';tableBody.closest('table').after(error)});
}
function selectPaperFromHash(){
 let id;
 try{id=decodeURIComponent(location.hash.slice(1))}catch{return}
 document.querySelectorAll('.paper-selected').forEach(row=>row.classList.remove('paper-selected'));
 if(!id.startsWith('paper-'))return;
 if(papersPanel)papersPanel.open=true;
 loadPapers();
 const row=document.getElementById(id);if(!row)return;
 row.classList.add('paper-selected');const details=row.querySelector('.abstract-details');if(details)details.open=true;row.scrollIntoView({block:'start'});
}
papersPanel?.addEventListener('toggle',()=>{if(papersPanel.open)loadPapers()});
if(!papersPanel||papersPanel.open)loadPapers();
selectPaperFromHash();
window.addEventListener('hashchange',selectPaperFromHash);
})();
