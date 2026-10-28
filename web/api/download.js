import {method,gh,respond,errorOut,verifySignedDownload} from './_lib.js';
export default async function handler(req,res){
  if(!method(req,['GET'],res))return;
  try{
    const params=new URL(req.url,'https://example.com').searchParams;
    const runId=params.get('run'),exp=params.get('exp'),sig=params.get('sig');
    if(!verifySignedDownload(runId,exp,sig)){
      respond(res,403,{error:'Enlace de descarga vencido. Recarga el estado del video.'});return;
    }
    const response=await gh('/actions/runs/'+runId+'/artifacts?per_page=40');
    const data=await response.json();
    const artifact=(data.artifacts||[]).find(a=>!a.expired&&a.name?.startsWith('HEC-REELS-'));
    if(!artifact){respond(res,404,{error:'Todavía no existe un video descargable o ha vencido.'});return;}
    const url='https://api.github.com/repos/hecagus/Hecagus-Reels/actions/artifacts/'+artifact.id+'/zip';
    const r=await fetch(url,{headers:{Authorization:'Bearer '+process.env.GITHUB_TOKEN,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'},redirect:'manual',signal:AbortSignal.timeout(16000)});
    const loc=r.headers.get('location');
    if(r.status!==302||!loc||!loc.startsWith('https://')){
      respond(res,502,{error:'GitHub no entregó un enlace de descarga. Vuelve a intentarlo.'});return;
    }
    res.statusCode=302;
    res.setHeader('Location',loc);
    res.setHeader('Cache-Control','no-store');
    res.end();
  }catch(err){errorOut(res,err);}
}
