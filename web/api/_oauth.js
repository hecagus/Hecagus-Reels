import {randomBytes,timingSafeEqual} from 'node:crypto';
import {method,respond,cookies,seal,sessionKey,sameOrigin} from './_lib.js';

const BASE='https://hecagus-reels.vercel.app';
const CALLBACK=BASE+'/api/callback';
const SCOPES='read:user';
const cookie=(name,value,maxAge)=>name+'='+value+'; Path=/; Max-Age='+maxAge+'; Secure; HttpOnly; SameSite=Lax';

export async function login(req,res){
  if(!method(req,['GET'],res))return;
  if(!process.env.GITHUB_OAUTH_CLIENT_ID||!process.env.GITHUB_OAUTH_CLIENT_SECRET||!sessionKey()){
    return respond(res,503,{error:'Falta configurar el inicio de sesión con GitHub en Vercel.'});
  }
  const state=randomBytes(24).toString('hex');
  res.setHeader('Set-Cookie',cookie('hec_oauth_state',state,600));
  const url=new URL('https://github.com/login/oauth/authorize');
  url.searchParams.set('client_id',process.env.GITHUB_OAUTH_CLIENT_ID);
  url.searchParams.set('redirect_uri',CALLBACK);
  url.searchParams.set('scope',SCOPES);
  url.searchParams.set('state',state);
  res.statusCode=302;res.setHeader('Cache-Control','no-store');res.setHeader('Location',url.toString());res.end();
}

export async function callback(req,res){
  if(!method(req,['GET'],res))return;
  res.setHeader('Set-Cookie',cookie('hec_oauth_state','',0));
  try{
    const url=new URL(req.url,BASE);
    const expected=cookies(req).hec_oauth_state;
    const actual=url.searchParams.get('state');
    if(!expected||!actual||expected.length!==actual.length||
       !timingSafeEqual(Buffer.from(expected),Buffer.from(actual))){
      return respond(res,403,{error:'Sesión de GitHub caducada o inválida. Inicia sesión de nuevo.'});
    }
    const code=url.searchParams.get('code');
    if(!code || !process.env.GITHUB_OAUTH_CLIENT_ID || !process.env.GITHUB_OAUTH_CLIENT_SECRET){
      return respond(res,400,{error:'GitHub no autorizó la conexión o falta configurar OAuth.'});
    }
    const tokenResponse=await fetch('https://github.com/login/oauth/access_token',{
      method:'POST',headers:{Accept:'application/json','Content-Type':'application/json'},
      body:JSON.stringify({client_id:process.env.GITHUB_OAUTH_CLIENT_ID,
        client_secret:process.env.GITHUB_OAUTH_CLIENT_SECRET,code,redirect_uri:CALLBACK}),
      signal:AbortSignal.timeout(15000)
    });
    if(!tokenResponse.ok)throw Error('No se pudo verificar la conexión con GitHub.');
    const tokens=await tokenResponse.json();
    if(!tokens.access_token) return respond(res,401,{error:'GitHub rechazó la autorización. Vuelve a intentarlo.'});
    const userResponse=await fetch('https://api.github.com/user',{
      headers:{Accept:'application/vnd.github+json',Authorization:'Bearer '+tokens.access_token,
        'User-Agent':'HEC-REELS-OWNER-AUTH'},
      signal:AbortSignal.timeout(15000)
    });
    if(!userResponse.ok)throw Error('No se pudo comprobar la identidad de GitHub.');
    const user=await userResponse.json();
    if(user.login?.toLowerCase()!=='hecagus'||!Number.isSafeInteger(user.id)){
      return respond(res,403,{error:'Este estudio solo permite generar con la cuenta propietaria hecagus.'});
    }
    const exp=Date.now()+7*24*60*60*1000;
    res.setHeader('Set-Cookie',[
      cookie('hec_oauth_state','',0),
      cookie('hec_session',seal({login:'hecagus',id:user.id,exp}),7*24*60*60)
    ]);
    res.statusCode=302;res.setHeader('Location','/');res.setHeader('Cache-Control','no-store');res.end();
  }catch(err){
    console.error('OAuth:',err.message);
    respond(res,502,{error:'Falló la autorización con GitHub. Intenta nuevamente.'});
  }
}

export async function logout(req,res){
  if(!method(req,['POST'],res))return;
  if(!sameOrigin(req))return respond(res,403,{error:'Origen no permitido.'});
  res.setHeader('Set-Cookie',cookie('hec_session','',0));
  respond(res,200,{ok:true});
}
