import {test} from 'node:test';
import assert from 'node:assert/strict';
import omni, {validateOmniRequest} from '../api/omni.js';

function response() {
  return {statusCode:200, headers:{},
    setHeader(k,v){this.headers[k]=v;},
    end(value){this.body=value?JSON.parse(value):undefined;}
  };
}
test('Omni validates explicit paid consent',()=>{
  assert.deepEqual(
    validateOmniRequest({idea:'  ChatGPT  regaña a HecAgus ',duracion:'60',costoAceptado:true}),
    {idea:'ChatGPT regaña a HecAgus',duracion:'60'});
  for (const bad of [
    {idea:'Una idea buena',duracion:'60',costoAceptado:false},
    {idea:'Una idea buena',duracion:'8',costoAceptado:true},
    {idea:'hola',duracion:'6',costoAceptado:true},
    {idea:'a'.repeat(351),duracion:'6',costoAceptado:true}
  ])assert.throws(()=>validateOmniRequest(bad));
});
test('Omni GET and POST reject anonymous requests before GitHub calls',async()=>{
  for(const method of ['GET','POST']){
    const res=response();
    await omni({method,headers:{host:'hecagus-reels.vercel.app'}},res);
    assert.equal(res.statusCode,401);
  }
});
test('Omni rejects unsupported methods',async()=>{
  const res=response();
  await omni({method:'PUT',headers:{host:'hecagus-reels.vercel.app'}},res);
  assert.equal(res.statusCode,405);
});
