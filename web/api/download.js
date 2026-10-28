import {method,guard,gh,respond,errorOut} from './_lib.js';
export default async function handler(req,res){
  if(!method(req,['GET'],res)||!guard(req,res))return;
  try{
    const runId=new URL(req.url,'https://example.com').searchParams.get('run');
    if(!/^\d{1,16}$/.test(runId||'')){respond(res,400,{error:'ID de ejecución inválido.'});return;}
    const response=await gh('/actions/runs/'+runId+'/artifacts?per_page=40');
    const data=await response.json();
    const artifact=(data.artifacts||[]).find(a=>!a.expired&&a.name?.startsWith('HEC-REELS-'));
    if(!artifact){respond(res,404,{error:'No hay artefacto disponible. La ejecución puede estar pendiente o el archivo venció.'});return;}
    const url='https://api.github.com/repos/hecagus/Hecagus-Reels/actions/artifacts/'+artifact.id+'/zip';
    const token=process.env.GITHUB_TOKEN;
    const r=await fetch(url,{headers:{Authorization:'Bearer '+token,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'},redirect:'manual',signal:AbortSignal.timeout(16000)});
    const location=r.headers.get('location');
    if(r.status!==302||!location||!location.startsWith('https://')){
      respond(res,502,{error:'GitHub no entregó un enlace de descarga. Vuelve a intentarlo.'});return;
    }
    res.statusCode=302;
    res.setHeader('Location',location);
    res.setHeader('Cache-Control','no-store');
    res.end();
  }catch(err){errorOut(res,err);}
}
