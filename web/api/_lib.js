import { createHash, timingSafeEqual } from 'node:crypto';

export const REPO = 'hecagus/Hecagus-Reels';
export const WORKFLOW = 'generar-reel.yml';
export const OWNER = 'hecagus';
export const NAME = 'Hecagus-Reels';

export function respond(res, status, data) {
  res.statusCode = status;
  res.setHeader('Content-Type','application/json; charset=utf-8');
  res.setHeader('Cache-Control','no-store');
  res.setHeader('X-Content-Type-Options','nosniff');
  res.end(JSON.stringify(data));
}
export function method(req, allowed, res) {
  if (allowed.includes(req.method)) return true;
  res.setHeader('Allow', allowed.join(', '));
  respond(res, 405, {error: 'Método no permitido.'});
  return false;
}
export function sameOrigin(req) {
  const origin = req.headers.origin;
  if (!origin) return true; // clients without Origin, still password protected.
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  try {
    return new URL(origin).host === host && new URL(origin).protocol === 'https:';
  } catch {return false;}
}
export function authorized(req) {
  const configured = process.env.HEC_ACCESS_KEY;
  const provided = req.headers['x-hec-key'];
  if (!configured || configured.length < 16 || typeof provided !== 'string' || !provided) return false;
  const left = createHash('sha256').update(configured).digest();
  const right = createHash('sha256').update(provided).digest();
  return timingSafeEqual(left,right);
}
export function guard(req, res) {
  if (!sameOrigin(req)) { respond(res, 403, {error:'Origen no permitido.'}); return false; }
  if (!authorized(req)) { respond(res, 401, {error:'Clave incorrecta o no configurada.'}); return false; }
  return true;
}
export async function readBody(req, max=4000) {
  if (req.body && typeof req.body === 'object') return req.body;
  let raw='';
  for await (const chunk of req) {
    raw += chunk.toString();
    if (raw.length > max) throw new Error('Texto demasiado largo.');
  }
  if (raw.length > max) throw new Error('Texto demasiado largo.');
  return JSON.parse(raw||'{}');
}
export async function gh(path, options={}) {
  const token=process.env.GITHUB_TOKEN;
  if (!token) throw Object.assign(new Error('Falta configurar GITHUB_TOKEN en Vercel.'),{http:503});
  const url='https://api.github.com/repos/'+REPO+path;
  const response=await fetch(url,{
    ...options,
    headers:{
      'Accept':'application/vnd.github+json',
      'Authorization':'Bearer '+token,
      'X-GitHub-Api-Version':'2022-11-28',
      'User-Agent':'HEC-REELS-WEB',
      ...(options.headers||{})
    },
    signal:AbortSignal.timeout(18000)
  });
  if (!response.ok) {
    const text=(await response.text()).slice(0,500);
    const e=new Error('GitHub devolvió '+response.status+(response.status===401||response.status===403?': revisa permisos del token.':'') );
    e.http=response.status>=500?502:response.status===404?404:response.status===401||response.status===403?502:400;
    e.detail=text;
    throw e;
  }
  return response;
}
export function errorOut(res, err) {
  console.error('HEC API:',err?.message);
  respond(res,err?.http||500,{error:err?.message||'Error interno del servidor.'});
}
export function validateNarration(text) {
  if(typeof text!=='string')throw Object.assign(new Error('Escribe la narración.'),{http:400});
  const parts=text.split('||').map(x=>x.replace(/\s+/g,' ').trim());
  if(parts.length<1||parts.length>6||parts.some(x=>x.length<2||x.length>105||x.split(/\s+/).some(w=>w.length>30))) {
    throw Object.assign(new Error('Usa de 1 a 6 escenas (||), cada una de 2 a 105 caracteres y palabras de máximo 30.'),{http:400});
  }
  return parts.join(' || ');
}
