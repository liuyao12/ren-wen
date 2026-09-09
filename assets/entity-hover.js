/** Accessible, non-modal navigation cards for annotated people and named works. */
import {escapeHTML as h} from './core.js';
import {loadProfiles,canonicalName} from './profiles.js';
import {westernYearText,chineseYearText,profileURL} from './person-display.js';
import {loadWorks,workURL,readerURL,eccpDestination} from './library.js';

export function linkWorkMentions(reader,works) {
  for(const span of reader.querySelectorAll('[data-entity]')) {
    const id=span.dataset.entity;
    if(!works.has(id) || span.closest('[data-work-link]'))continue;
    let sourceHref=null;
    for(const a of span.querySelectorAll('a')){sourceHref ||= a.getAttribute('href');a.replaceWith(...a.childNodes);}
    const outer=span.closest('a');if(outer){sourceHref ||= outer.getAttribute('href');outer.replaceWith(...outer.childNodes);}
    const a=document.createElement('a');a.href=workURL(id);a.dataset.workLink=id;
    if(sourceHref)a.dataset.sourceHref=sourceHref;
    span.removeAttribute('role');span.removeAttribute('tabindex');span.removeAttribute('title');span.removeAttribute('aria-label');
    span.replaceWith(a);a.append(span);
  }
}

export async function installHover() {
  const reader=document.getElementById('reader');if(!reader)return;
  const [ps,ws,r]=await Promise.all([loadProfiles(),loadWorks(),fetch('data/catalog.json')]);
  if(!r.ok)throw Error('Hover navigation: catalogue unavailable.');
  const catalog=await r.json(),people=new Map(ps.map(p=>[p.id,p])),works=new Map(ws.map(w=>[w.id,w]));
  const card=document.createElement('div');card.id='entity-card';card.className='entity-card';card.hidden=true;
  card.setAttribute('role','dialog');card.setAttribute('aria-label','Profile and source navigation');
  document.body.append(card);
  let active=null,showTimer=null,hideTimer=null,suppressFocus=false;
  const selector='a[data-person-link],a[data-work-link]';
  const observer=new MutationObserver(enhance);
  function enhance(){
    observer.disconnect();
    if(active && !active.isConnected)hide();
    linkWorkMentions(reader,works);
    for(const a of reader.querySelectorAll(selector)) {
      a.removeAttribute('title');a.setAttribute('aria-haspopup','dialog');a.setAttribute('aria-controls',card.id);
      if(a!==active)a.setAttribute('aria-expanded','false');
    }
    observer.observe(reader,{childList:true,subtree:true});
  }
  function hide(restore=false){
    clearTimeout(showTimer);clearTimeout(hideTimer);
    const old=active;active=null;card.hidden=true;
    if(old){old.setAttribute('aria-expanded','false');if(restore && old.isConnected){suppressFocus=true;old.focus();suppressFocus=false;}}
  }
  function position(){
    if(!active || !active.isConnected){hide();return;}
    const rect=active.getBoundingClientRect(),gap=8,margin=10;
    const box=card.getBoundingClientRect();
    let top=rect.bottom+gap;if(top+box.height>innerHeight-margin)top=Math.max(margin,rect.top-box.height-gap);
    const left=Math.max(margin,Math.min(rect.left,innerWidth-box.width-margin));
    card.style.left=`${left}px`;card.style.top=`${top}px`;
  }
  function anchor(url,label,external=false){return `<a href="${h(url)}"${external?' target="_blank" rel="noopener"':''}>${h(label)}${external?' ↗':''}</a>`;}
  function show(a){
    clearTimeout(showTimer);clearTimeout(hideTimer);
    if(active===a && !card.hidden)return;
    if(active)active.setAttribute('aria-expanded','false');
    active=a;const pid=a.dataset.personLink,wid=a.dataset.workLink,mention=a.querySelector('[data-entity]');
    const p=people.get(pid),w=works.get(wid);if(!p && !w){hide();return;}
    const choices=[];let heading,detail;
    if(p){
      heading=canonicalName(p);
      detail=`<p>${h(westernYearText(p,'birth'))}–${h(westernYearText(p,'death'))} AD</p><p class="card-calendar">生：${h(chineseYearText(p.life?.birth))}<br>卒：${h(chineseYearText(p.life?.death))}</p>`;
      choices.push(anchor(profileURL(p.id),'Person profile · 人'));
      const entry=eccpDestination(p,catalog);
      if(entry)choices.push(anchor(entry.url,entry.label,entry.external));
      else choices.push('<span class="card-note">No separate ECCP entry identified.</span>');
      if(entry?.relation==='mentioned-in')choices.push('<span class="card-note">A discussion under another person, not a separate biography.</span>');
    }else{
      heading=w.title;detail=`<p>${h(w.kind || 'work')} · ${h((w.creators||[]).map(c=>`${people.has(c.person)?canonicalName(people.get(c.person)):c.person} (${c.role})`).join(' · ') || 'Authorship not entered')}</p>`;
      choices.push(anchor(workURL(w.id),'Work profile · 文'));
      const m=catalog.mentions.find(m=>m.id===mention?.id) || catalog.mentions.find(m=>m.entity===w.id);
      if(m)choices.push(anchor(readerURL(m.witness,m.passage),'Read this ECCP passage'));
    }
    card.innerHTML=`<button type="button" class="card-close" aria-label="Close navigation">×</button><div class="card-kind">${p?'PERSON · 人':'WORK · 文'}</div><h2>${h(heading)}</h2>${detail}<nav aria-label="Entity destinations">${choices.join('')}</nav>${mention?.id?'<button type="button" class="card-review">Review this occurrence</button>':''}<small>Source-linked draft · awaiting review</small>`;
    card.querySelector('.card-close').onclick=()=>hide(true);
    const review=card.querySelector('.card-review');if(review)review.onclick=()=>{
      const target=mention;hide();target.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,altKey:true}));
    };
    a.setAttribute('aria-expanded','true');card.hidden=false;position();
  }
  function scheduleHide(){clearTimeout(hideTimer);hideTimer=setTimeout(()=>{
    if(!card.matches(':hover') && !card.contains(document.activeElement) && active!==document.activeElement)hide();
  },220);}
  reader.addEventListener('pointerover',e=>{
    if(e.pointerType==='touch')return;
    const a=e.target.closest(selector);if(!a)return;
    clearTimeout(hideTimer);clearTimeout(showTimer);showTimer=setTimeout(()=>show(a),130);
  });
  reader.addEventListener('pointerout',e=>{
    const a=e.target.closest(selector);if(!a || a.contains(e.relatedTarget) || card.contains(e.relatedTarget))return;
    clearTimeout(showTimer);scheduleHide();
  });
  reader.addEventListener('focusin',e=>{if(suppressFocus)return;const a=e.target.closest(selector);if(a)show(a);});
  reader.addEventListener('focusout',e=>{if(!card.contains(e.relatedTarget))scheduleHide();});
  reader.addEventListener('keydown',e=>{
    const a=e.target.closest(selector);if(a && e.key==='ArrowDown'){e.preventDefault();show(a);card.querySelector('a')?.focus();}
  });
  // On touch screens, first tap reveals choices. Desktop clicks retain ordinary link behavior.
  reader.addEventListener('click',e=>{
    const a=e.target.closest(selector);if(!a)return;
    const reviewing=e.altKey || document.getElementById('review-names')?.checked;
    if(reviewing){hide();if(a.dataset.workLink)e.preventDefault();return;}
    const touch=e.pointerType==='touch' || (matchMedia('(hover: none)').matches && e.detail>0);
    if(touch && !e.ctrlKey && !e.metaKey){e.preventDefault();e.stopPropagation();show(a);return;}
    if(a.dataset.workLink)e.stopPropagation();
  },true);
  card.addEventListener('pointerenter',()=>clearTimeout(hideTimer));
  card.addEventListener('pointerleave',scheduleHide);
  card.addEventListener('focusin',()=>clearTimeout(hideTimer));
  card.addEventListener('focusout',e=>{if(!card.contains(e.relatedTarget) && e.relatedTarget!==active)scheduleHide();});
  card.addEventListener('click',e=>{if(e.target.closest('a'))hide();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape' && !card.hidden){e.preventDefault();hide(true);}});
  document.addEventListener('pointerdown',e=>{if(!card.hidden && !card.contains(e.target) && !active?.contains(e.target))hide();});
  reader.addEventListener('scroll',()=>{if(active)hide();},{passive:true});
  window.addEventListener('resize',()=>hide());window.addEventListener('hashchange',()=>hide());
  enhance();
}
if(typeof document!=='undefined')installHover().catch(error=>{
  const s=document.getElementById('status');if(s)s.textContent=error.message;
  console.error(error);
});
