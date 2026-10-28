import {method,readBody,respond,errorOut,sameOrigin} from './_lib.js';
import {buildDraft} from './_draft.js';

export default async function handler(req,res) {
 if(!method(req,['POST'],res)) return;
 if(!sameOrigin(req)) return respond(res,403,{error:'Origen no permitido.'});
 try {
   const body=await readBody(req,1500);
   const result=buildDraft(body?.idea);
   respond(res,200,result);
 } catch(err) {
   if (err instanceof SyntaxError || /idea|Escribe|plantilla|largo/.test(err.message)) {
      respond(res,400,{error:err.message});return;
   }
   errorOut(res,err);
 }
}
