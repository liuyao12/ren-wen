import test from 'node:test';import assert from 'node:assert/strict';
import {visibleLabelLayers,placeURL} from '../assets/place-model.js';
import {sourceFamily} from '../assets/source-navigation.js';
const layers=[{id:'county-fine',year:1911,level:'county',minViewWidth:0,maxViewWidth:3,file:'assets/maps/chgis-1911-county-names-detail.png'},{id:'county-mid',year:1911,level:'county',minViewWidth:3,maxViewWidth:1000,file:'assets/maps/chgis-1911-county-names-regional.png'},{id:'prefecture',year:1820,level:'prefecture',minViewWidth:0,maxViewWidth:1000,file:'assets/maps/chgis-1820-prefecture-names-detail.png'}];
test('county labels follow scale without duplicate levels',()=>{assert.deepEqual(visibleLabelLayers(layers,1911,2,['province','prefecture','county']).map(r=>r.id),['county-fine']);assert.equal(visibleLabelLayers(layers,1911,5,['county'])[0].id,'county-mid');});
test('snapshot year and visibility are explicit',()=>{assert.equal(visibleLabelLayers(layers,1820,2,['province','prefecture'])[0].id,'prefecture');assert.deepEqual(visibleLabelLayers(layers,1911,2,['county'],false),[]);assert.deepEqual(visibleLabelLayers(layers,1820,2,['county']),[]);});
test('invalid label paths cannot load external images',()=>{assert.deepEqual(visibleLabelLayers([{...layers[0],file:'https://example.org/x.png'}],1911,2,['county']),[]);});
test('place routes are local and reject malformed identities',()=>{assert.equal(placeURL('place-region-hunan'),'places.html#place-region-hunan');assert.equal(placeURL('../x'),null);});
test('both legacy and bulk QSG work IDs have the same navigation family',()=>{assert.equal(sourceFamily({work:'work-qsg'}),'qsg');assert.equal(sourceFamily({work:'work-qingshigao'}),'qsg');});
