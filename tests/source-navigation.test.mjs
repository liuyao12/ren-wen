import test from 'node:test';
import assert from 'node:assert/strict';
import {sourceFamily,sourceGroup,readingSources,resolveSource} from '../assets/source-navigation.js';
const c={sources:[{id:'a',work:'work-eccp',title:'A-kotun',kind:'biography'},{id:'r',kind:'cross-reference',work:'work-eccp'},{id:'qsg-volume-303',work:'work-qingshigao',title:'清史稿/卷303'},{id:'qsg',work:'work-qingshigao',title:'曾紀澤'}],navigation:{redirects:{r:{target:'a',relation:'printed-cross-reference'}}}};
test('sources remain separate and no redirect is a reading entry',()=>{assert.deepEqual(readingSources(c).map(s=>s.id),['a','qsg-volume-303','qsg']);assert.equal(sourceFamily(c.sources[0]),'eccp');assert.equal(sourceFamily(c.sources[2]),'qsg');});
test('subdivisions are romanized alphabet or QSG volume ranges',()=>{assert.equal(sourceGroup(c.sources[0]),'A');assert.equal(sourceGroup(c.sources[2]),'301');assert.equal(sourceGroup(c.sources[3]),'accounts');assert.equal(sourceGroup({work:'work-eccp',title:'Tsêng Kuo-fan'}),'T');});
test('print alias resolves source, without merging people',()=>{assert.equal(resolveSource(c,'r').id,'a');assert.equal(c.sources[1].id,'r');});
test('redirect cycles fail rather than hanging',()=>{assert.throws(()=>resolveSource({...c,navigation:{redirects:{r:{target:'r'}}}},'r'),/Circular/);});
