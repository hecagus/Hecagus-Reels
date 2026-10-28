import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateNarration, signedDownload, verifySignedDownload, authorized, sameOrigin } from '../api/_lib.js';
test('validates narrator scenes',()=>{
 assert.equal(validateNarration('Primera escena || Segunda escena'), 'Primera escena || Segunda escena');
 assert.throws(()=>validateNarration(''),/Usa de 1 a 6/);
 assert.throws(()=>validateNarration('a'.repeat(106)),/Usa de 1 a 6/);
 assert.throws(()=>validateNarration('abc ||'.repeat(7)),/Usa de 1 a 6/);
});
test('signed links expire and cannot be modified',()=>{
 const old=process.env.HEC_ACCESS_KEY;
 try{
  process.env.HEC_ACCESS_KEY='test-secret-of-adequate-length';
  const u=new URL(signedDownload('123'),'https://app.example');
  assert.equal(verifySignedDownload(u.searchParams.get('run'),u.searchParams.get('exp'),u.searchParams.get('sig')),true);
  assert.equal(verifySignedDownload('124',u.searchParams.get('exp'),u.searchParams.get('sig')),false);
  assert.equal(verifySignedDownload('123','1000000000',u.searchParams.get('sig')),false);
 }finally{if(old)process.env.HEC_ACCESS_KEY=old;else delete process.env.HEC_ACCESS_KEY;}
});
test('key verification is constant-time digest comparison',()=>{
 const old=process.env.HEC_ACCESS_KEY;
 try{
  process.env.HEC_ACCESS_KEY='some-testing-secret-123';
  assert.equal(authorized({headers:{'x-hec-key':'some-testing-secret-123'}}),true);
  assert.equal(authorized({headers:{'x-hec-key':'wrong'}}),false);
 }finally{if(old)process.env.HEC_ACCESS_KEY=old;else delete process.env.HEC_ACCESS_KEY;}
});
test('rejects a foreign origin',()=>{
 assert.equal(sameOrigin({headers:{origin:'https://attacker.example',host:'reels.example'}}),false);
 assert.equal(sameOrigin({headers:{origin:'https://reels.example',host:'reels.example'}}),true);
});
