import {test} from 'node:test';
import assert from 'node:assert/strict';
import {guard} from '../api/_lib.js';
function mockRes(){
 return {statusCode:200,headers:{},setHeader(k,v){this.headers[k]=v;},end(body){this.payload=JSON.parse(body);}};
}
function request(origin='https://hecagus-reels.vercel.app'){
 return {method:'POST',headers:{origin,host:'hecagus-reels.vercel.app'}};
}
test('passwordless gateway fails closed before platform switch is enabled',()=>{
 const old={mode:process.env.HEC_AUTH_MODE,key:process.env.HEC_ACCESS_KEY,token:process.env.GITHUB_TOKEN};
 try{
  process.env.HEC_AUTH_MODE='';
  process.env.HEC_ACCESS_KEY='server-signing-secret-not-shared';
  process.env.GITHUB_TOKEN='github-test-value';
  let res=mockRes();
  assert.equal(guard(request(),res),false);
  assert.equal(res.statusCode,503);
  delete process.env.GITHUB_TOKEN;
  process.env.HEC_AUTH_MODE='vercel';
  res=mockRes();
  assert.equal(guard(request(),res),false);
  assert.equal(res.statusCode,503);
 }finally{
  for(const [field,value] of [['HEC_AUTH_MODE',old.mode],['HEC_ACCESS_KEY',old.key],['GITHUB_TOKEN',old.token]]){
   if(value===undefined)delete process.env[field];else process.env[field]=value;
  }
 }
});
test('no password required after external Vercel protection is explicitly enabled',()=>{
 const old={mode:process.env.HEC_AUTH_MODE,key:process.env.HEC_ACCESS_KEY,token:process.env.GITHUB_TOKEN};
 try{
  process.env.HEC_AUTH_MODE='vercel';
  process.env.HEC_ACCESS_KEY='server-signing-secret-not-shared';
  process.env.GITHUB_TOKEN='github-test-value';
  let res=mockRes();
  assert.equal(guard(request(),res),true);
  res=mockRes();
  assert.equal(guard(request('https://untrusted.example'),res),false);
  assert.equal(res.statusCode,403);
 }finally{
  for(const [field,value] of [['HEC_AUTH_MODE',old.mode],['HEC_ACCESS_KEY',old.key],['GITHUB_TOKEN',old.token]]){
   if(value===undefined)delete process.env[field];else process.env[field]=value;
  }
 }
});
