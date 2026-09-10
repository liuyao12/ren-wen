/** A visible release label; optional deployment metadata never blocks reading. */
const label=document.querySelector('[data-release-info]');
if(label){fetch('deployment.json',{cache:'no-store'}).then(async r=>{
  if(!r.ok)return;const d=await r.json();
  if(/^[a-f0-9]{40}$/.test(d.commit||'')){label.textContent='r2026.09.09 · '+d.commit.slice(0,7);label.title=d.publishedAt||'';}
}).catch(()=>{});}
