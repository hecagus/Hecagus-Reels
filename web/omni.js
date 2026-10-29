const $=id=>document.getElementById(id);
let signedIn=false, busy=false, timer=null, waitingFolio=null;
const feedback=(msg,type='')=>{const e=$('message-omni');e.textContent=msg;e.className='feedback '+type;};
async function api(path,method='GET',body){
 const r=await fetch(path,{method,credentials:'same-origin',cache:'no-store',
   headers:body?{'Content-Type':'application/json'}:{},
   ...(body?{body:JSON.stringify(body)}:{})});
 const data=await r.json().catch(()=>({}));
 if(!r.ok)throw Error(data.error||'Error HTTP '+r.status);
 return data;
}
function date(x){try{return new Date(x).toLocaleString('es-MX');}catch{return '';}}
function update(){
 $('counter-omni').textContent=$('idea-omni').value.length+'/350';
 const duration=$('length-omni').value;
 $('price-omni').textContent=duration==='60'
  ?'Referencia de costo: US$3–10 de video por 10 clips (3–10 s cada uno) a 720p, más guion; no es un límite garantizado.'
  :'Referencia de costo: US$0.30–1 por clip generado (3–10 s) a 720p, más guion. La prueba tiene cobro real.';
}
function link(text,url){
 const a=document.createElement('a');a.textContent=text;a.href=url;
 a.rel='noopener noreferrer';a.target='_blank';return a;
}
function draw(runs){
 const root=$('renders-omni');root.textContent='';
 if(!runs.length){const p=document.createElement('p');p.className='placeholder';p.textContent='Sin producciones Omni todavía.';root.append(p);return;}
 for(const run of runs.slice(0,10)){
  const div=document.createElement('div');div.className='task';
  const top=document.createElement('div');top.className='task-top';
  const title=document.createElement('strong');title.textContent=(run.title||'Video Omni').slice(0,90);
  const stat=document.createElement('span');stat.className='task-status';
  stat.textContent=run.status==='completed'?(run.conclusion==='success'?'Listo':'Falló'):'Procesando';
  if(run.status==='completed')stat.classList.add(run.conclusion==='success'?'ok':'bad');
  top.append(title,stat);
  const bottom=document.createElement('div');bottom.className='task-bottom';
  const actions=document.createElement('div');
  actions.append(link(run.downloadUrl?'Descargar MP4 (ZIP)':'Ver ejecución',run.downloadUrl||run.url));
  bottom.append(document.createTextNode(date(run.created)),actions);
  div.append(top,bottom);root.append(div);
 }
}
async function refresh(){
 if(!signedIn)return;
 try {
  const data=await api('/api/omni');
  draw(data.runs||[]);
  if(waitingFolio){
   const found=(data.runs||[]).find(r=>r.title?.includes(waitingFolio));
   if(found?.status==='completed'){
    waitingFolio=null;
    clearInterval(timer);timer=null;
    feedback(found.conclusion==='success'?'Video terminado. Descarga el ZIP desde esta página.':'La producción falló. Abre la ejecución para revisar el error.',found.conclusion==='success'?'success':'error');
   }
  }
 }catch(err){feedback(err.message,'error');}
}
async function start(){
 if(busy)return;
 const idea=$('idea-omni').value.trim();
 if(idea.length<8||idea.length>350)return feedback('Escribe una idea de 8 a 350 caracteres.','error');
 if(!$('accept-omni').checked)return feedback('Debes aceptar el costo antes de iniciar.','error');
 if(!signedIn)return feedback('Entra con tu cuenta GitHub para iniciar la producción.','error');
 busy=true;$('start-omni').disabled=true;
 try{
  feedback('Enviando la idea a GitHub Actions…');
  const data=await api('/api/omni','POST',{
   idea,duracion:$('length-omni').value,costoAceptado:true
  });
  waitingFolio=data.folio;
  feedback('Producción iniciada. Gemini preparará el guion y generará las escenas. Puedes consultar la ejecución en Resultados.','success');
  await refresh();clearInterval(timer);timer=setInterval(refresh,12000);
 }catch(err){feedback(err.message,'error');}
 finally{busy=false;$('start-omni').disabled=false;}
}
async function setup(){
 $('idea-omni').addEventListener('input',update);
 $('length-omni').addEventListener('change',update);
 $('refresh-omni').addEventListener('click',refresh);
 $('start-omni').addEventListener('click',start);
 update();
 try{
  const s=await api('/api/status');signedIn=Boolean(s.signedIn);
  $('login-state-omni').textContent=signedIn?'GitHub conectado como hecagus':'Debes iniciar sesión con GitHub';
  if(signedIn)await refresh();
 }catch(err){feedback(err.message,'error');}
}
setup();
