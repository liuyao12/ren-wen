/** A keyed, generation-first timeline, sharing the reader's context and map selection. */
import {escapeHTML as h} from './core.js';
import {t, ui, bindText} from './i18n.js';
import {canonicalName} from './profiles.js';
import {westernYearText, profileURL} from './person-display.js';
import {nameAtYear} from './name-history.js';
import {familyFocusLayout} from './family-layout.js';

const NS='http://www.w3.org/2000/svg';
const roleKeys={grandparents:'Grandparents',parents:'Parents',self:'Self',spouses:'Spouses',children:'Children'};
const name=p=>(p.name.surname||'')+p.name.given;
const year=(p,key)=>{if(!p)return null;const s=westernYearText(p,key);return /^\d+$/.test(s)?Number(s):null;};
const add=(tag,attrs,parent,text)=>{const n=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;parent.append(n);return n;};
const activate=(node,fn)=>{node.onclick=fn;node.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn();}};};

export function createFamilyTimeline({host,catalog,people,onSelect,onEvidence,passageButton}) {
  host.classList.add('family-timeline');
  host.innerHTML=`<div class="context-options"><label><input id="group-people" type="checkbox" checked> ${ui('Follow paragraph focus')}</label><button id="expand-family" aria-pressed="false">${ui('Expand family')}</button><span id="context-people-count"></span></div><div class="family-canvas" tabindex="0"><svg id="context-timeline" role="group" aria-label="${h(t('Family hierarchy'))}"></svg></div><div class="family-other-control"><button id="show-other-people" hidden></button></div><details class="family-evidence"><summary id="family-evidence-title"></summary><div id="context-families" class="context-family-list"></div><p>${ui('Family roles follow recorded relationships. Missing relatives are not filled in.')}</p></details><p class="family-help">${ui('Grey family bands retain known lifespans; expand to see every name.')} ${ui('Name labels open profiles; empty bar space selects journeys.')+ ' '+ui('Scroll horizontally for other years. Unknown lifespans are shown as undated cards.')}</p>`;
  const find=id=>host.querySelector('#'+id),svg=find('context-timeline');
  const bg=add('g',{},svg),grid=add('g',{},svg),kin=add('g',{class:'kin-links'},svg),layer=add('g',{},svg),cursor=add('line',{class:'cursor paragraph-cursor'},svg),cursorLabel=add('text',{class:'paragraph-cursor-label',y:14},svg);
  const nodes=new Map(), positions=new Map();
  let current=null,previous=[],source=null,expanded=false,showOthers=false,animation=0,lastFocus=null;
  const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
  find('group-people').onchange=()=>render();
  find('expand-family').onclick=()=>{expanded=!expanded;render();};
  find('show-other-people').onclick=()=>{showOthers=!showOthers;render();};
  const expand=()=>{expanded=true;render();find('expand-family').focus({preventScroll:true});};

  function render() {
    if(!current)return;
    const active=new Set([...current.context.entityIds,...current.activePeople,current.source.subject]);
    const layout=familyFocusLayout({subject:current.source.subject,relations:catalog.relations,
      availableIds:[...people.keys()],sourceIds:current.people,activeIds:active,previous,
      focus:find('group-people').checked,expanded,showOthers});
    previous=layout.otherOrder;
    const allIds=[...new Set([...current.people,...layout.family.members.map(m=>m.id)])];
    // The x scale is source-wide, not recalculated from the currently expanded rows.
    const dates=allIds.flatMap(id=>['birth','death'].map(key=>year(people.get(id),key))).filter(Number.isFinite);
    const events=catalog.events.filter(e=>e.witness===current.source.id).map(e=>e.time.start);
    const anchors=(current.history?.paragraphAnchors||[]).filter(a=>a.witness===current.source.id).map(a=>a.year);
    const range=[...dates,...events,...anchors];
    const lo=Math.floor((range.length?Math.min(...range):1800)/10)*10-5,hi=Math.ceil((range.length?Math.max(...range):1900)/10)*10+5;
    const slider=document.getElementById('year');slider.min=lo;slider.max=hi;
    const width=Math.max(host.clientWidth-2,(hi-lo)*4+48),barStart=24,barEnd=width-24,x=v=>barStart+(v-lo)/(hi-lo)*(barEnd-barStart);
    const datedYear=current.follow && !current.anchor ? null : current.year;
    svg.style.width=width+'px';
    svg.setAttribute('viewBox',`0 0 ${width} ${layout.height}`);svg.dataset.axis=`${lo}:${hi}`;
    svg.setAttribute('aria-label',t('Family hierarchy'));
    bindText(find('context-people-count'),'{count} in focus',{count:layout.focusedCount});
    bindText(find('expand-family'),expanded?'Compact family':'Expand family');find('expand-family').setAttribute('aria-pressed',String(expanded));
    const otherButton=find('show-other-people');otherButton.hidden=!layout.hiddenOthers&&!showOthers;
    bindText(otherButton,showOthers?'Hide other people':'Show other people ({count})',{count:layout.hiddenOthers});
    otherButton.setAttribute('aria-expanded',String(showOthers));
    bg.replaceChildren();add('rect',{x:0,y:23,width,height:Math.max(30,layout.familyEnd-12),rx:6,class:'family-background'},bg);
    if(layout.dividerY!==null)bindText(add('text',{x:5,y:layout.dividerY,class:'family-divider'},bg),find('group-people').checked&&!showOthers?'Other people in this passage':'Other people in this source');
    const tick=20;
    grid.replaceChildren();
    for(let y=Math.ceil(lo/tick)*tick;y<=hi;y+=tick){add('line',{x1:x(y),x2:x(y),y1:23,y2:layout.height-10,class:'ruler'},grid);add('text',{x:x(y),y:14,'text-anchor':'middle'},grid,String(y));}
    const keys=new Set(layout.rows.map(r=>r.key));
    // Save focused identity before replacing children, so a year change does not lose keyboard focus.
    const focused=document.activeElement?.closest?.('[data-row-key]');
    const focusKey=focused?.dataset.rowKey,focusIsLink=document.activeElement?.tagName?.toLowerCase()==='a';
    for(const[key,node]of nodes)if(!keys.has(key)){node.remove();nodes.delete(key);}
    const endpointRows=new Map(),target=new Map();
    for(const row of layout.rows){
      const oldY=positions.get(row.key)??row.ids.map(id=>positions.get(id)).find(Number.isFinite)??row.y;
      if(!positions.has(row.key))positions.set(row.key,oldY);
      target.set(row.key,row.y);for(const id of row.ids)endpointRows.set(id,row);
      let g=nodes.get(row.key);if(!g){g=add('g',{'data-row-key':row.key},layer);nodes.set(row.key,g);}layer.append(g);g.replaceChildren();
      g.setAttribute('class',`person-row ${row.active?'active':'dim'} ${row.kind==='summary'?'family-summary':''} ${row.role==='self'?'self-row':''}`);
      g.dataset.familyRole=row.role;
      if(row.kind==='summary'){
        g.removeAttribute('data-person-row');g.dataset.familySummary=row.role;
        const title=row.ids.map(id=>`${name(people.get(id))} ${westernYearText(people.get(id),'birth')}–${westernYearText(people.get(id),'death')}`).join('、');
        const button=add('g',{tabindex:0,role:'button','aria-label':`${t('Expand {role}',{role:t(roleKeys[row.role])})}: ${title}`},g);
        add('rect',{x:0,y:-12,width:width-2,height:22,rx:3,class:'summary-hit'},button);
        add('text',{x:5,y:2,class:'family-role'},button,t(roleKeys[row.role]));
        const label=row.ids.length===1?name(people.get(row.ids[0])):t('{count} people',{count:row.ids.length});
        add('text',{x:61,y:2,class:'summary-label'},button,`${label}  ＋`);add('title',{},button,title);activate(button,expand);
        // Miniature bars are individual known lives, never a fictional aggregate lifespan.
        row.ids.forEach((id,i)=>{const p=people.get(id),b=year(p,'birth'),d=year(p,'death');if(b!==null&&d!==null&&d>=b)add('line',{x1:x(b),x2:x(d),y1:-7+i*14/Math.max(1,row.ids.length-1),y2:-7+i*14/Math.max(1,row.ids.length-1),class:'mini-life'},button);});
      } else {
        g.dataset.personRow=row.key;g.removeAttribute('data-family-summary');
        const p=people.get(row.key),b=year(p,'birth'),d=year(p,'death');
        const display=nameAtYear(p,datedYear,current.history), short=display.label;
        const known=b!==null&&d!==null&&d>=b;
        const anchorX=known?x(b):x(current.anchor?.year??current.year);
        if(row.role==='self')add('rect',{x:0,y:-20,width,height:39,rx:4,class:'self-background'},g);
        if(roleKeys[row.role])add('text',{x:anchorX,y:-17,class:'family-role'},g,t(roleKeys[row.role]));
        if(known){
          const w=Math.max(2,x(d)-x(b));
          const bar=add('rect',{x:anchorX,y:-13,width:w,height:28,rx:3,class:'life-bar',tabindex:0,role:'button','aria-label':t('Show journeys for {name}',{name:short})},g);
          add('title',{},bar,`${short} · ${b}–${d}`);activate(bar,()=>onSelect(row.key));
          const a=add('a',{href:profileURL(row.key),'aria-label':short},g);
          // Never stretch a short lifespan to fit its label. Preserve the full label in title/ARIA.
          const maxChars=Math.max(0,Math.floor((w-10)/12));
          const visible=[...short].length>maxChars?(maxChars>1?[...short].slice(0,maxChars-1).join('')+'…':''):short;
          const text=add('text',{x:anchorX+5,y:0,class:'name bar-name','data-label-year':datedYear??'default'},a);
          if(visible===short && display.title){add('tspan',{class:'bar-title'},text,display.title+' ');add('tspan',{},text,display.name);}else text.textContent=visible;
          add('title',{},a,`${short} · ${b}–${d}`);
          if(w>74)add('text',{x:anchorX+5,y:11,class:'bar-dates'},g,`${b}–${d}`);
        } else {
          // An undated card is not a lifespan interval. Its placement is purely for reading.
          const a=add('a',{href:profileURL(row.key),'aria-label':`${short} · ${t('Undated person')}`},g);
          const w=Math.min(220,Math.max(120,[...short].length*11+18));
          add('rect',{x:anchorX,y:-13,width:w,height:28,rx:3,class:'unknown-card'},a);
          add('text',{x:anchorX+6,y:0,class:'name bar-name'},a,[...short].slice(0,17).join(''));
          bindText(add('text',{x:anchorX+6,y:11,class:'unknown-label'},a),'Undated person');
          add('title',{},a,`${short} · ${t('Lifespan unresolved')}`);
        }
        for(const e of current.context.events.filter(e=>e.people.includes(row.key)))add('circle',{cx:x(e.time.start),cy:-1,r:3,class:'event-dot'},g);
      }
    }
    // Paths join rows (or their compact tier), with evidence kept separately accessible.
    const edges=layout.family.links.filter(r=>r.predicate==='child-of'||['spouse-of','wife-of','husband-of'].includes(r.predicate));
    kin.replaceChildren();
    const connectors=edges.map(e=>{
      const spouse=e.predicate!=='child-of',parent=spouse?e.subject:e.object,child=spouse?e.object:e.subject;
      const pr=endpointRows.get(parent),ch=endpointRows.get(child);if(!pr||!ch||pr.key===ch.key)return null;
      const b=year(people.get(child),'birth'),pb=year(people.get(parent),'birth'),pd=year(people.get(parent),'death');
      const aligned=!spouse&&pr.kind==='person'&&ch.kind==='person'&&b!==null&&pb!==null&&pd!==null&&b>=pb&&b<=pd;
      const path=add('path',{class:`family-connector ${e.status==='reviewed'?'reviewed':''} ${spouse?'spouse-connector':''}`,'data-family':e.id,opacity:pr.active&&ch.active?'.85':'.3'},kin);
      add('title',{},path,`${name(people.get(parent))} → ${name(people.get(child))} · ${t(spouse?'spouses':'parent–child')} · ${t(e.status)}`);
      return{node:path,from:pr.key,to:ch.key,x:aligned?x(b):12};
    }).filter(Boolean);
    const evidenceBox=find('context-families');
    bindText(find('family-evidence-title'),'Family evidence ({count})',{count:edges.length});
    evidenceBox.innerHTML=edges.length?edges.map(e=>`<button data-family-evidence="${h(e.id)}">${h(name(people.get(e.predicate==='child-of'?e.object:e.subject)))} → ${h(name(people.get(e.predicate==='child-of'?e.subject:e.object)))} <small>${ui(e.predicate==='child-of'?'parent–child':'spouses')} · ${ui(e.status)}</small></button>`).join(''):`<p>${ui('No additional recorded relatives.')}</p>`;
    evidenceBox.querySelectorAll('button').forEach(b=>b.onclick=()=>{const e=edges.find(r=>r.id===b.dataset.familyEvidence);onEvidence('Family relationship',`<p>${h(canonicalName(people.get(e.predicate==='child-of'?e.object:e.subject)))} → ${h(canonicalName(people.get(e.predicate==='child-of'?e.subject:e.object)))}</p><p>${ui(e.predicate==='child-of'?'Parent → child':'spouses')} · ${ui(e.status)}</p>${e.predicate!=='child-of'?`<p>${ui('A relationship is not a marriage date.')}</p>`:''}${e.evidence.map(v=>`<p>${passageButton(v.witness,v.passage)}</p>`).join('')}`);});
    const hasCursor=Number.isFinite(datedYear);
    cursor.setAttribute('visibility',hasCursor?'visible':'hidden');cursorLabel.setAttribute('visibility',hasCursor?'visible':'hidden');
    cursor.setAttribute('x1',x(current.year));cursor.setAttribute('x2',x(current.year));cursor.setAttribute('y1',23);cursor.setAttribute('y2',layout.height-10);
    cursorLabel.setAttribute('x',x(current.year)+4);cursorLabel.textContent=hasCursor?String(current.year):'';
    const focusYear=hasCursor?current.year:(year(people.get(current.source.subject),'birth')??current.year);
    const focusKeyYear=current.source.id+':'+focusYear;
    if(lastFocus!==focusKeyYear){lastFocus=focusKeyYear;requestAnimationFrame(()=>{
      const box=host.querySelector('.family-canvas');box.scrollLeft=Math.max(0,x(focusYear)-box.clientWidth*.4);
    });}

    cancelAnimationFrame(animation);const start=new Map(positions),t0=performance.now();
    function animate(now){const f=reduced()?1:Math.min(1,(now-t0)/260),ease=f*f*(3-2*f);
      for(const[key,y]of target){const pos=start.get(key)+(y-start.get(key))*ease;positions.set(key,pos);nodes.get(key).setAttribute('transform',`translate(0 ${pos})`);}
      for(const c of connectors){const a=positions.get(c.from),b=positions.get(c.to);c.node.setAttribute('d',`M${c.x-4},${a} H${c.x} V${b} H${c.x+4}`);}
      if(f<1)animation=requestAnimationFrame(animate);
    }
    if(reduced())animate(t0);else animation=requestAnimationFrame(animate);
    if(focusKey&&nodes.has(focusKey))nodes.get(focusKey).querySelector(focusIsLink?'a':'[tabindex]')?.focus({preventScroll:true});
  }
  return {update(context){if(context.source.id!==source){source=context.source.id;previous=[];positions.clear();showOthers=false;lastFocus=null;host.closest('.time-body').scrollTop=0;}const changed=current?.passage!==context.passage;current=context;render();if(changed&&find('group-people').checked)host.closest('.time-body').scrollTop=0;}};
}
