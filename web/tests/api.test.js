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


test('verify endpoint distinguishes a valid key, wrong key and missing configuration', async()=>{
 const {default:handler}=await import('../api/verify.js');
 const old=process.env.HEC_ACCESS_KEY;
 function mockResponse(){
   return {
     statusCode:200,
     headers:{},
     setHeader(k,v){this.headers[k]=v;},
     end(data){this.body=JSON.parse(data);}
   };
 }
 try{
  process.env.HEC_ACCESS_KEY='test-secret-of-adequate-length';
  let res=mockResponse();
  await handler({method:'POST',headers:{origin:'https://reels.test',host:'reels.test','x-hec-key':'test-secret-of-adequate-length'}},res);
  assert.equal(res.statusCode,200);
  assert.equal(res.body.ok,true);
  assert.equal(JSON.stringify(res.body).includes(process.env.HEC_ACCESS_KEY),false);
  res=mockResponse();
  await handler({method:'POST',headers:{origin:'https://reels.test',host:'reels.test','x-hec-key':'not-the-key'}},res);
  assert.equal(res.statusCode,401);
  process.env.HEC_ACCESS_KEY='too-short';
  res=mockResponse();
  await handler({method:'POST',headers:{origin:'https://reels.test',host:'reels.test','x-hec-key':'not-the-key'}},res);
  assert.equal(res.statusCode,503);
 }finally{if(old!==undefined)process.env.HEC_ACCESS_KEY=old;else delete process.env.HEC_ACCESS_KEY;}
});
