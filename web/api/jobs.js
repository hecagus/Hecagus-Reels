import {method,guard,readBody,gh,respond,errorOut,validateNarration,WORKFLOW,signedDownload} from './_lib.js';
const base='/actions/workflows/'+WORKFLOW;
function safeRun(run){
  return {id:run.id, status:run.status, conclusion:run.conclusion, title:run.display_title,
    created:run.created_at, url:run.html_url, run_number:run.run_number};
}
export default async function handler(req,res){
  if(!method(req,['POST','GET'],res)||!guard(req,res))return;
  try{
    if(req.method==='POST'){
      const body=await readBody(req);
      const texto=validateNarration(body.texto);
      const velocidad=['0.95','1.00','1.05','1.10'].includes(body.velocidad)?body.velocidad:'1.00';
      const folio=typeof body.folio==='string'&&/^[a-zA-Z0-9_-]{6,40}$/.test(body.folio)?body.folio:'web'+Date.now();
      const estilo=body.estilo==='3d'?'3d':'2d';
      const payload={ref:'main',inputs:{modo:'texto',texto,velocidad,folio,estilo}};
      const response=await gh(base+'/dispatches',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const data=response.status===204?{}:await response.json().catch(()=>({}));
      respond(res,202,{accepted:true,folio,runId:data.workflow_run_id||null,runUrl:data.html_url||null});
      return;
    }
    const id=new URL(req.url,'https://example.com').searchParams.get('id');
    if(id){
      if(!/^\d{1,16}$/.test(id)){respond(res,400,{error:'ID inválido.'});return;}
      const run=await(await gh('/actions/runs/'+id)).json();
      respond(res,200,{run:{...safeRun(run),downloadUrl:run.status==='completed'&&run.conclusion==='success'?signedDownload(run.id):null}});return;
    }
    const response=await gh(base+'/runs?event=workflow_dispatch&per_page=20');
    const data=await response.json();
    respond(res,200,{runs:(data.workflow_runs||[]).map(run=>({...safeRun(run),downloadUrl:run.status==='completed'&&run.conclusion==='success'?signedDownload(run.id):null}))});
  }catch(err){errorOut(res,err);}
}
