/** Show the deployed commit without blocking the reader when metadata is absent. */
const label=document.querySelector('[data-release-info]');
if(label){fetch('deployment.json',{cache:'no-store'}).then(async r=>{
  if(!r.ok)return;const d=await r.json();
  if(/^[a-f0-9]{40}$/.test(d.commit||'')){
    const release=/^r[0-9]{4}\.[0-9]{2}\.[0-9]{2}$/.test(d.release||'')?d.release:'Ren-Wen';
    label.textContent=release+' · '+d.commit.slice(0,7);label.title=d.publishedAt||'';
  }
}).catch(()=>{});}
