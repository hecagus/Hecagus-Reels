import {method,respond,sameOrigin,authorized} from './_lib.js';

export default async function handler(req,res){
  if(!method(req,['POST'],res)) return;
  if(!sameOrigin(req)) return respond(res,403,{error:'Origen no permitido.'});
  const configured=process.env.HEC_ACCESS_KEY;
  if(typeof configured!=='string'||configured.length<16)
    return respond(res,503,{error:'La clave del estudio no está configurada correctamente en Production.'});
  if(!authorized(req))
    return respond(res,401,{error:'No coincide con HEC_ACCESS_KEY. Revisa el valor exacto, incluidas mayúsculas, espacios y caracteres especiales. Si no lo recuerdas, cámbialo en Vercel y vuelve a desplegar.'});
  respond(res,200,{ok:true,message:'Clave válida. Ya puedes generar el video.'});
}
