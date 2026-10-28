import { createHash, createHmac, timingSafeEqual } from 'node:crypto';

export const REPO = 'hecagus/Hecagus-Reels';
export const WORKFLOW = 'generar-reel.yml';
export const OWNER = 'hecagus';
export const OWNER_GITHUB_ID = 132156689;
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
// Session key stays only on Vercel. Existing HEC_ACCESS_KEY is accepted as
// a migration fallback; visitors never enter it or receive it in JavaScript.
export function sessionKey() {
  const secret=process.env.HEC_SESSION_SECRET || process.env.HEC_ACCESS_KEY || process.env.GITHUB_TOKEN;
  return typeof secret==='string' && secret.length>=16 ? secret : null;
}
export function seal(payload) {
  const secret=sessionKey();
  if(!secret)throw Object.assign(new Error('Falta secreto de sesión en el servidor.'),{http:503});
  const value=Buffer.from(JSON.stringify(payload)).toString('base64url');
  const signature=createHmac('sha256',secret).update('session:'+value).digest('hex');
  return value+'.'+signature;
}
export function unseal(value) {
  if(!sessionKey()||typeof value!=='string'||value.length>2000)return null;
  const [data,sig,...extra]=value.split('.');
  if(extra.length||!data||!sig||!/^[a-f0-9]{64}$/.test(sig)||!/^[A-Za-z0-9_-]+$/.test(data))return null;
  const expected=createHmac('sha256',sessionKey()).update('session:'+data).digest('hex');
  if(!timingSafeEqual(Buffer.from(sig),Buffer.from(expected)))return null;
  try {
    const payload=JSON.parse(Buffer.from(data,'base64url').toString('utf8'));
    return Number.isSafeInteger(payload.exp) && payload.exp>Date.now() ? payload : null;
  }catch {return null;}
}
export function cookies(req) {
  return Object.fromEntries(String(req.headers.cookie||'').split(';').map(part=>{
    const i=part.indexOf('=');
    return i<0?[]:[part.slice(0,i).trim(),part.slice(i+1).trim()];
  }).filter(part=>part.length===2));
}
export function ownerSession(req) {
  const data=unseal(cookies(req).hec_session);
  return data?.login==='hecagus' && data.id===OWNER_GITHUB_ID ? data : null;
}
export function guard(req,res) {
  if(!sameOrigin(req)) {respond(res,403,{error:'Origen no permitido.'});return false;}
  if(!ownerSession(req)) {respond(res,401,{error:'Inicia sesión con tu cuenta de GitHub para generar y consultar videos.'});return false;}
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

export function signedDownload(run) {
  const id=String(run);
  if(!/^\d{1,16}$/.test(id))return null;
  const exp=String(Math.floor(Date.now()/1000)+120);
  const sig=createHmac('sha256',sessionKey()||'not-configured').update(id+':'+exp).digest('hex');
  return '/api/download?run='+id+'&exp='+exp+'&sig='+sig;
}
export function verifySignedDownload(id,exp,sig){
  if(!sessionKey()||!/^\d{1,16}$/.test(id||'')||!/^\d{10,12}$/.test(exp||'')||!/^[a-f0-9]{64}$/.test(sig||''))return false;
  if(Number(exp)<Date.now()/1000||Number(exp)>Date.now()/1000+130)return false;
  const digest=createHmac('sha256',sessionKey()).update(id+':'+exp).digest('hex');
  return timingSafeEqual(Buffer.from(digest),Buffer.from(sig));
}
