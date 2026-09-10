import {fetchData} from './data-cache.js';
import {getLocale} from './i18n.js';
import {escapeHTML as h} from './core.js';
import {readerURL} from './library.js';
const $=id=>document.getElementById(id),params=new URLSearchParams(location.search);
let scope=params.get('source'),entity=params.get('entity'),limit=100,matches=[];
try{
  const [r,c]=await Promise.all([fetchData('data/editorial/identification-review.json'),fetchData('data/catalog.json')]);
  if(!r.ok||!c.ok)throw Error('Review data unavailable');
  const review=await r.json(),catalog=await c.json(),sources=new Map(catalog.sources.map(s=>[s.id,s]));
  function render(){
    const en=getLocale()==='en',needle=$('review-search').value.trim().toLocaleLowerCase(),reason=$('review-reason').value;
    $('review-title').textContent=en?'Identification review':'標註覆核';
    $('review-intro').textContent=en?'Source wording is unchanged. These automatic identifications are withheld pending contextual review, not verified facts.':'原文保持不變。以下是已暫停的自動判定，不是已核實的身分；可循段落返回上下文。';
    matches=review.quarantined.filter(m=>(!scope||m.witness===scope)&&(!entity||m.entity===entity)&&(reason==='all'||m.reason===reason)&&m.quote.toLocaleLowerCase().includes(needle));
    $('review-count').textContent=`${scope?sources.get(scope)?.shortTitle+' · ':''}${matches.length} ${en?'candidates':'筆候選'} · ${en?'showing':'顯示'} ${Math.min(limit,matches.length)}`;
    $('review-results').innerHTML=matches.slice(0,limit).map(m=>`<article class="review-row"><a href="${h(readerURL(m.witness,m.passage))}">${h(sources.get(m.witness)?.shortTitle||m.witness)} · ${h(m.passage)}</a><q>${h(m.quote)}</q><p>${m.reason==='typography-only'?(en?'Italics alone do not establish a work.':'僅據斜體，尚不足以判定為著作。'):(en?'Reign year or context-dependent ruler designation; dynasty and passage need checking.':'可能是紀年或依上下文而定的帝王稱謂，須核對朝代及語境。')}</p><small>${en?'Former suggestion (not accepted)':'原自動候選（未採信）'}：${h(m.entity)} · <code>${h(m.id)}</code></small></article>`).join('');
    $('review-more').hidden=matches.length<=limit;
  }
  $('review-search').oninput=()=>{limit=100;render();};$('review-reason').onchange=()=>{limit=100;render();};
  $('review-more').onclick=()=>{limit+=100;render();};$('review-clear').onclick=()=>{scope=null;entity=null;history.replaceState(null,'',location.pathname);render();};
  $('review-export').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify({schemaVersion:1,status:'needs-review',candidates:matches},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='ren-wen-identification-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  window.addEventListener('renwen:languagechange',render);render();
}catch(e){$('review-results').textContent=e.message;}
