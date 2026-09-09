import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {familyHierarchy, familyFocusLayout} from '../assets/family-layout.js';
const edge=(id,subject,predicate,object,status='proposed')=>({id,subject,predicate,object,status,evidence:[{witness:'test',passage:'p1'}]});
const relations=[edge('gf','dad','child-of','grandpa'),edge('f','self','child-of','dad'),edge('w','wife','spouse-of','self'),edge('c','son','child-of','self'),edge('c2','daughter','child-of','self')];
const availableIds=['self','dad','grandpa','wife','son','daughter','other','second','unrelated'];
const defaults={subject:'self',relations,availableIds,sourceIds:availableIds,activeIds:['self']};
const roles=x=>x.members.map(m=>m.role);
test('family hierarchy follows grandparents, parents, self, spouses, children',()=>{
 const f=familyHierarchy('self',relations,availableIds);
 assert.deepEqual(f.members.map(m=>m.id),['grandpa','dad','self','wife','son','daughter']);
 assert.deepEqual(roles(f),['grandparents','parents','self','spouses','children','children']);
});
test('family is drawn from linked records even when absent from current text',()=>{
 const l=familyFocusLayout({...defaults,sourceIds:['self','other']});
 assert.equal(l.family.members.length,6);
});
test('no spouse or grandparent is filled in to complete the picture',()=>{
 assert.deepEqual(familyHierarchy('self',[],availableIds).members,[{id:'self',role:'self'}]);
});
test('rejected, superseded, evidence-free and unavailable relatives are excluded',()=>{
 for(const bad of ['rejected','superseded'])assert.equal(familyHierarchy('self',[edge('x','self','child-of','dad',bad)],availableIds).members.length,1);
 assert.equal(familyHierarchy('self',[{...relations[1],evidence:[]}],availableIds).members.length,1);
 assert.equal(familyHierarchy('self',relations,['self']).members.length,1);
});
test('cycles never duplicate self or run an unbounded ancestor traversal',()=>{
 const f=familyHierarchy('self',[...relations,edge('cycle','grandpa','child-of','self')],availableIds);
 assert.equal(f.members.filter(m=>m.id==='self').length,1);
 assert.equal(new Set(f.members.map(m=>m.id)).size,f.members.length);
});
test('inactive family tiers become compact bands, not unrelated people',()=>{
 const l=familyFocusLayout({...defaults,activeIds:['other']});
 assert.deepEqual(l.rows.filter(r=>r.kind==='summary').map(r=>r.role),['grandparents','parents','spouses','children']);
 assert.equal(l.rows.filter(r=>r.role==='other').length,1);
 assert.equal(l.rows.find(r=>r.key==='self').active,true);
});
test('active people lift towards self as descendants compact',()=>{
 const a=familyFocusLayout({...defaults,activeIds:['self','son','daughter','other']});
 const b=familyFocusLayout({...defaults,activeIds:['self','other'],previous:a.otherOrder});
 assert(b.rows.find(r=>r.key==='other').y<a.rows.find(r=>r.key==='other').y);
 assert(b.rows.find(r=>r.key==='other').y-b.rows.find(r=>r.key==='self').y<=100);
});
test('family stays together above active non-family figures',()=>{
 const l=familyFocusLayout({...defaults,activeIds:['daughter','other','second']});
 const i=l.rows.findIndex(r=>r.role==='other');assert(i>0);
 assert(l.rows.slice(0,i).every(r=>r.role!=='other'));assert(l.rows.slice(i).every(r=>r.role==='other'));
});
test('expanded family keeps all individuals in generation order',()=>{
 const l=familyFocusLayout({...defaults,expanded:true});
 assert(!l.rows.some(r=>r.kind==='summary'));
 assert.deepEqual(l.rows.map(r=>r.key),['grandpa','dad','self','wife','son','daughter']);
});
test('the focus switch can show all source people without destroying family order',()=>{
 const l=familyFocusLayout({...defaults,focus:false});assert.equal(l.rows.length,availableIds.length);
 assert.deepEqual(l.rows.slice(0,6).map(r=>r.key),['grandpa','dad','self','wife','son','daughter']);
});
test('relative ordering of active figures is stable',()=>{
 const l=familyFocusLayout({...defaults,activeIds:['other','second'],previous:['second','other']});
 assert.deepEqual(l.rows.filter(r=>r.role==='other').map(r=>r.key),['second','other']);
});
test('collapsed tiers retain every identity; no source records mutate',()=>{
 const before=JSON.stringify(defaults);const l=familyFocusLayout(defaults);
 assert.equal(JSON.stringify(defaults),before);
 assert.deepEqual(new Set(l.rows.flatMap(r=>r.ids)),new Set(['self','dad','grandpa','wife','son','daughter']));
});
test('known Zeng family records work without new facts or missing-spouse placeholders',()=>{
 const c=JSON.parse(fs.readFileSync(new URL('../data/catalog.json',import.meta.url)));
 const idx=JSON.parse(fs.readFileSync(new URL('../data/people/index.json',import.meta.url)));
 const f=familyHierarchy('person-zeng-guofan',c.relations,idx.profiles.map(n=>n.slice(0,-5)));
 assert.deepEqual(f.members.slice(0,3).map(m=>m.id),['person-zeng-yuping','person-zeng-linshu','person-zeng-guofan']);
 assert.equal(f.members.filter(m=>m.role==='children').length,7);
 assert.equal(f.members.filter(m=>m.role==='spouses').length,0);
});
