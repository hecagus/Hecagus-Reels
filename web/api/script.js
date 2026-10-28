import {method,guard,readBody,respond,errorOut,validateNarration} from './_lib.js';
export const maxDuration=45;
export default async function handler(req,res) {
 if(!method(req,['POST'],res)||!guard(req,res))return;
 try {
  if(!process.env.OPENAI_API_KEY){
    respond(res,503,{error:'Para convertir ideas en guiones, configura OPENAI_API_KEY en Vercel. El modo Guion escrito funciona sin ella.'});return;
  }
  const data=await readBody(req);
  const idea=typeof data.idea==='string'?data.idea.trim():'';
  if(idea.length<8||idea.length>350){respond(res,400,{error:'Describe una idea de 8 a 350 caracteres.'});return;}
  const resp=await fetch('https://api.openai.com/v1/responses',{
    method:'POST',
    headers:{'Authorization':'Bearer '+process.env.OPENAI_API_KEY,'Content-Type':'application/json'},
    body:JSON.stringify({
      model:process.env.OPENAI_MODEL||'gpt-5-mini',
      max_output_tokens:700,
      instructions:[
        'Eres guionista de videos explicativos cortos en español de México.',
        'Genera entre 3 y 5 escenas narradas. Máximo 100 caracteres cada una.',
        'Frases naturales, informativas y concretas; no clichés de marketing.',
        'No inventes datos, referencias ni cifras. Si la idea es demasiado vaga, quédate en hechos generales.',
        'La voz narrará literalmente cada escena. No agregues indicaciones visuales ni notas.',
        'Responde SOLO con JSON válido: {"scenes":["texto escena 1", "..."]}.'
      ].join(' '),
      input:idea,
      text:{format:{type:'json_object'}}
    }),
    signal:AbortSignal.timeout(38000)
  });
  if(!resp.ok){
    const error=await resp.text();
    console.error('AI response error',resp.status,error.slice(0,250));
    respond(res,502,{error:'No se pudo generar el guion con IA (HTTP '+resp.status+').'});return;
  }
  const parsed=await resp.json();
  const output=(parsed.output||[]).flatMap(x=>(x.content||[]).filter(c=>c.type==='output_text').map(c=>c.text)).join('');
  if(!output){respond(res,502,{error:'La IA no entregó texto. Reintenta.'});return;}
  let json;
  try{json=JSON.parse(output);}catch{respond(res,502,{error:'La IA devolvió un formato no válido.'});return;}
  const scenes=json?.scenes;
  if(!Array.isArray(scenes)||scenes.length<3||scenes.length>5||scenes.some(x=>typeof x!=='string')){
    respond(res,502,{error:'El guion generado tiene escenas inválidas. Reintenta.'});return;
  }
  let texto;
  try{texto=validateNarration(scenes.join(' || '));}catch{
    respond(res,502,{error:'El guion supera los límites del motor. Solicita otro.'});return;
  }
  respond(res,200,{texto,scenes});
 }catch(err){errorOut(res,err);}
}
