/** One immutable JSON response per URL and page session, shared by reader modules. */
const pending=new Map();
export function fetchData(path) {
  if(typeof path!=='string' || !/^data\/[a-zA-Z0-9_./-]+\.json$/.test(path) || path.includes('..'))return Promise.reject(new Error('Invalid data path.'));
  if(!pending.has(path))pending.set(path,fetch(path).then(async response=>{
    const value=response.ok?await response.json():null;
    return {ok:response.ok,status:response.status,json:async()=>value};
  }).catch(error=>{pending.delete(path);throw error;}));
  return pending.get(path);
}
