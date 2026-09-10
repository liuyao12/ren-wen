import {fetchData} from './data-cache.js';
import {escapeHTML as h} from './core.js';
import {readerURL} from './library.js';
import {profileURL} from './person-display.js';
import {t,getLocale,ui} from './i18n.js';
const $=id=>document.getElementById(id);
try {
  const r=await fetchData('data/collections/eccp-reading-index.json');if(!r.ok)throw Error('目錄無法載入');
  const {entries,counts}=await r.json();
  function render(){
    const english=getLocale()==='en',needle=$('library-search').value.trim().normalize('NFC').toLocaleLowerCase(),kind=$('library-kind').value;
    const matches=entries.filter(e=>(kind==='all'||e.kind===kind)&&`${e.name} ${e.qualifier} ${e.alias} ${e.title}`.normalize('NFC').toLocaleLowerCase().includes(needle));
    $('library-coverage').textContent=english?`${counts.biography} complete biographies · ${counts['cross-reference']} cross-reference entries · ${counts['reference-material']} editorial/reference texts. Annotations are a first-round draft.`:`${counts.biography} 篇完整傳記 · ${counts['cross-reference']} 篇參見條目 · ${counts['reference-material']} 篇編輯／參考資料。標註為第一輪初稿。`;
    $('library-count').textContent=english?`${matches.length} matches`:`共 ${matches.length} 筆`;
    $('library-results').innerHTML=matches.map(e=>`<article class="collection-entry"><h2><a href="${h(readerURL(e.source))}">${h(e.qualifier?'['+e.qualifier+'] ':'')}${h(e.name||e.title)}</a></h2><p>${h(e.title)}</p><nav><a href="${h(readerURL(e.source))}">${english?'Read complete entry':'閱讀全文'}</a>${e.person?`<a href="${h(profileURL(e.person))}">${english?'Person profile':'人物資料'}</a>`:''}</nav>${e.qsg?`<small>${english?'QSG account or opening candidate linked in profile':'人物頁附清史稿相關記錄或開頭配對候選'}</small>`:''}</article>`).join('');
  }
  $('library-search').oninput=render;$('library-kind').onchange=render;window.addEventListener('renwen:languagechange',render);render();
}catch(error){$('library-results').textContent=error.message;}
