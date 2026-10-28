import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  validateNarration,signedDownload,verifySignedDownload,
  seal,unseal,ownerSession,guard,sameOrigin
} from '../api/_lib.js';

function mockResponse(){
  return {
    statusCode:200,headers:{},
    setHeader(k,v){this.headers[k]=v;},
    end(data){this.body=data?JSON.parse(data):undefined;}
  };
}
function withSecret(fn){
  const old=process.env.HEC_SESSION_SECRET;
  process.env.HEC_SESSION_SECRET='adequate-session-testing-secret-123';
  try{return fn();}
  finally{if(old===undefined)delete process.env.HEC_SESSION_SECRET;else process.env.HEC_SESSION_SECRET=old;}
}
test('validates narrator scenes',()=>{
 assert.equal(validateNarration('Primera escena || Segunda escena'),'Primera escena || Segunda escena');
 assert.throws(()=>validateNarration(''),/Usa de 1 a 6/);
 assert.throws(()=>validateNarration('a'.repeat(106)),/Usa de 1 a 6/);
});
test('signed links expire and cannot be modified',()=>withSecret(()=>{
 const u=new URL(signedDownload('123'),'https://app.example');
 assert.equal(verifySignedDownload(u.searchParams.get('run'),u.searchParams.get('exp'),u.searchParams.get('sig')),true);
 assert.equal(verifySignedDownload('124',u.searchParams.get('exp'),u.searchParams.get('sig')),false);
 assert.equal(verifySignedDownload('123','1000000000',u.searchParams.get('sig')),false);
}));
test('owner session is signed and cannot be forged',()=>withSecret(()=>{
 const value=seal({login:'hecagus',id:123,exp:Date.now()+60000});
 assert.equal(unseal(value).login,'hecagus');
 assert.equal(ownerSession({headers:{cookie:'hec_session='+value}}).id,123);
 assert.equal(ownerSession({headers:{cookie:'hec_session='+value.slice(0,-1)+'0'}}),null);
 assert.equal(ownerSession({headers:{cookie:'hec_session='+seal({login:'intruder',id:456,exp:Date.now()+60000})}}),null);
 assert.equal(unseal(seal({login:'hecagus',id:123,exp:Date.now()-1000})),null);
}));
test('rejects foreign origin and anonymous render jobs',()=>withSecret(()=>{
 assert.equal(sameOrigin({headers:{origin:'https://attacker.example',host:'reels.example'}}),false);
 assert.equal(sameOrigin({headers:{origin:'https://reels.example',host:'reels.example'}}),true);
 let res=mockResponse();
 assert.equal(guard({headers:{host:'reels.example'}},res),false);
 assert.equal(res.statusCode,401);
 const ticket=seal({login:'hecagus',id:1,exp:Date.now()+60000});
 res=mockResponse();
 assert.equal(guard({headers:{origin:'https://reels.example',host:'reels.example',cookie:'hec_session='+ticket}},res),true);
}));
test('legacy key verification is permanently disabled',async()=>{
 const {default:handler}=await import('../api/verify.js');
 const res=mockResponse();
 await handler({method:'POST',headers:{'x-hec-key':'whatever'}},res);
 assert.equal(res.statusCode,410);
 assert.match(res.body.error,/eliminó/);
});
test('OAuth callback rejects requests without matching state',async()=>{
 const {default:callback}=await import('../api/callback.js');
 const res=mockResponse();
 await callback({method:'GET',headers:{cookie:'hec_oauth_state=abc'},url:'/api/callback?state=wrong'},res);
 assert.equal(res.statusCode,403);
});
