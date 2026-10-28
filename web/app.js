const $ = (id) => document.getElementById(id);
const state = { mode: 'idea', busy: false, interval: null, current: null, aiAvailable: false, draftIdea: '', draftText: '' };
const MAX_SCENES = 6;

const els = {
  idea: $('idea'), script: $('script'), access: $('key'), rate: $('rate'),
  feedback: $('feedback'), preview: $('preview-text'), start: $('start-btn'),
  draft: $('draft-btn'), list: $('task-list')
};

function message(value, type='') {
  els.feedback.textContent = value;
  els.feedback.className = 'feedback '+type;
}
function draftMessage(value, type='') {
  const target = $('draft-feedback');
  target.textContent = value;
  target.className = 'draft-feedback '+type;
}
function setBusy(value) {
  state.busy = value;
  els.start.disabled = value;
  els.draft.disabled = value;
}
function setMode(mode) {
  state.mode=mode;
  els.start.innerHTML=mode==='idea'?'Crear reel desde idea <span aria-hidden="true">➜</span>':'Generar mi reel <span aria-hidden="true">➜</span>';
  $('mode-idea').classList.toggle('is-active',mode==='idea');
  $('mode-script').classList.toggle('is-active',mode==='script');
  $('mode-idea').setAttribute('aria-pressed',mode==='idea');
  $('mode-script').setAttribute('aria-pressed',mode==='script');
  $('idea-zone').hidden=mode!=='idea';
  $('script-zone').hidden=false; // El guion se puede revisar siempre.
  $('draft-btn').hidden=mode!=='idea';
  message('');
  draftMessage('');
}
function scenes(text) {
  return text.split('||').map(x=>x.replace(/\s+/g,' ').trim());
}
function validate(text) {
  const parts=scenes(text);
  if(parts.length<1||parts.length>MAX_SCENES) throw Error('Máximo 6 escenas.');
  for(let i=0;i<parts.length;i++){
    const part=parts[i];
    if(part.length<2||part.length>105)throw Error('Escena '+(i+1)+': usa entre 2 y 105 caracteres.');
    if(part.split(/\s+/).some(x=>x.length>30))throw Error('Escena '+(i+1)+': evita palabras de más de 30 caracteres.');
  }
  return parts.join(' || ');
}
function updatePreview() {
  $('idea-count').textContent=els.idea.value.length+' / 350';
  const list=scenes(els.script.value).filter(Boolean);
  $('scene-count').textContent=list.length+' escena'+(list.length===1?'':'s');
  els.preview.textContent=list[0]||els.idea.value.trim().slice(0,110)||'Tu próxima idea empieza aquí.';
}
async function api(path,{method='GET',body,auth=true}={}) {
  const key=els.access.value.trim();
  if(auth && key.length<16) throw Error('Introduce la clave privada del estudio (mínimo 16 caracteres).');
  const response=await fetch(path,{
    method,cache:'no-store',
    headers:{ ...(body?{'Content-Type':'application/json'}:{}),...(auth?{'x-hec-key':key}:{}) },
    ...(body?{body:JSON.stringify(body)}:{})
  });
  const content=await response.json().catch(()=>({}));
  if(!response.ok)throw Error(content.error||'Error HTTP '+response.status);
  return content;
}
async function status() {
  try {
    const x=await api('/api/status',{auth:false});
    $('github-state').textContent=x.github&&x.access?'● Motor configurado':'● Falta configuración';
    $('github-state').style.color=x.github&&x.access?'#8ee9ba':'#ffd18c';
    state.aiAvailable=Boolean(x.ai);
    $('ai-state').textContent=x.ai?'● Guiones con IA disponibles':'● Borradores gratuitos disponibles';
    $('ai-state').style.color='#8ee9ba';
    els.draft.textContent=x.ai?'✦ Crear guion con IA':'Crear guion gratis (plantilla)';
    $('idea-help').textContent=x.ai?'Un modelo de IA creará escenas editables.':'Borrador automático por plantillas, sin IA ni pagos. Puedes editarlo.';
    if(!x.github||!x.access)message('La web está publicada, pero faltan GITHUB_TOKEN o HEC_ACCESS_KEY en Vercel.');
  }catch{
    $('github-state').textContent='● No se pudo consultar la configuración';
  }
}
function formatDate(raw) {
  if(!raw)return '';
  try{return new Date(raw).toLocaleString('es-MX',{dateStyle:'short',timeStyle:'short'});}catch{return '';}
}
function niceStatus(run) {
  if(run.status==='completed')return run.conclusion==='success'?'Listo':run.conclusion==='cancelled'?'Cancelado':'Falló';
  if(run.status==='in_progress')return 'Generando';
  if(run.status==='queued'||run.status==='waiting'||run.status==='pending')return 'En cola';
  return run.status||'Pendiente';
}
function addLink(element,text,url,download=false) {
  const a=document.createElement('a');
  a.textContent=text;a.href=url;
  if(!download){a.target='_blank';a.rel='noopener noreferrer';}
  element.append(a);return a;
}
function renderJobs(runs) {
  els.list.textContent='';
  if(!runs.length){const p=document.createElement('p');p.className='placeholder';p.textContent='No hay videos anteriores todavía.';els.list.append(p);return;}
  for(const run of runs.slice(0,12)){
    const item=document.createElement('div');item.className='task';
    const top=document.createElement('div');top.className='task-top';
    const title=document.createElement('strong');
    title.textContent=(run.title||'Video #'+run.id).slice(0,100);
    const status=document.createElement('span');
    status.className='task-status '+(run.conclusion==='success'?'ok':run.conclusion&&run.conclusion!=='success'?'bad':'');
    status.textContent=niceStatus(run);
    top.append(title,status);
    const bottom=document.createElement('div');bottom.className='task-bottom';
    const date=document.createElement('span');date.textContent=formatDate(run.created);
    const actions=document.createElement('div');actions.style.display='flex';actions.style.gap='13px';
    if(run.downloadUrl) addLink(actions,'Descargar ZIP',run.downloadUrl,true);
    else if(run.url?.startsWith('https://github.com/'))addLink(actions,'Ver detalle',run.url);
    bottom.append(date,actions);item.append(top,bottom);els.list.append(item);
  }
}
async function fetchRuns() {
  try {
    const result=await api('/api/jobs');
    renderJobs(result.runs||[]);
    if(state.current?.folio&&!state.current.id){
      const match=(result.runs||[]).find(r=>(r.title||'').includes(state.current.folio));
      if(match)state.current.id=match.id;
    }
    if(state.current?.id){
      const found=(result.runs||[]).find(r=>r.id===state.current.id);
      if(found?.status==='completed'){
        clearInterval(state.interval);state.interval=null;
        state.current=null;
        message(found.conclusion==='success'?'Video terminado. Descárgalo desde Tus renders.':'La ejecución terminó con error. Revisa su detalle en GitHub.',found.conclusion==='success'?'success':'error');
      }
    }
  }catch(err){message(err.message,'error');}
}
async function generateDraft(idea) {
  const ai=state.aiAvailable;
  const result=await api(ai?'/api/script':'/api/draft',{
    method:'POST',body:{idea},auth:ai
  });
  const text=validate(result.texto);
  els.script.value=text;
  state.draftIdea=idea;
  state.draftText=text;
  updatePreview();
  draftMessage(ai
    ?'Guion creado con IA. Revísalo antes de generar el video.'
    :'Borrador gratuito listo. Utiliza plantillas, no IA. Revísalo y edítalo antes del video.','success');
  return text;
}
async function makeDraft(){
  if(state.busy)return;
  const idea=els.idea.value.trim();
  if(idea.length<3){draftMessage('Escribe un tema (mínimo 3 caracteres).','error');return;}
  setBusy(true);
  draftMessage(state.aiAvailable?'Generando guion con IA...':'Preparando borrador gratuito...');
  try{
    await generateDraft(idea);
    $('script-zone').scrollIntoView({behavior:'smooth',block:'nearest'});
  }catch(err){draftMessage(err.message,'error');}
  finally{setBusy(false);}
}
async function start() {
 if(state.busy)return;
 setBusy(true);
 try{
   if(state.mode==='idea' && !els.script.value.trim()){
     if(els.idea.value.trim().length<3)throw Error('Escribe un tema de al menos 3 caracteres.');
     message(state.aiAvailable?'Convirtiendo tu idea en guion con IA...':'Generando borrador gratuito...');
     await generateDraft(els.idea.value.trim());
   }
   const text=validate(els.script.value);
   message('Enviando el trabajo a GitHub...');
   const id='w'+Date.now().toString(36)+Math.random().toString(36).slice(2,8);
   const run=await api('/api/jobs',{method:'POST',body:{texto:text,velocidad:els.rate.value,folio:id}});
   state.current={folio:run.folio,id:run.runId};
   message('Solicitud aceptada. GitHub está preparando tu video. Consulta el estado en Tus renders.','success');
   await fetchRuns();
   if(state.interval)clearInterval(state.interval);
   state.interval=setInterval(fetchRuns,12000);
   document.querySelector('.tasks').scrollIntoView({behavior:'smooth',block:'nearest'});
 }catch(err){message(err.message,'error');}
 finally{setBusy(false);}
}
function setup(){
  $('mode-idea').addEventListener('click',()=>setMode('idea'));
  $('mode-script').addEventListener('click',()=>setMode('script'));
  els.idea.addEventListener('input',()=>{
    if(state.draftIdea && els.idea.value.trim()!==state.draftIdea) {
      if(els.script.value===state.draftText){
        els.script.value='';
      }
      state.draftIdea='';
      state.draftText='';
      draftMessage('Cambiaste la idea. Genera un borrador nuevo antes de continuar.');
    }
    updatePreview();
  });
  els.script.addEventListener('input',updatePreview);
  els.access.addEventListener('change',()=>{if(els.access.value.trim().length>=16)fetchRuns();});
  $('refresh-btn').addEventListener('click',fetchRuns);
  els.draft.addEventListener('click',makeDraft);
  els.start.addEventListener('click',start);
  setMode('idea');updatePreview();status();
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&els.access.value.trim().length>=16)fetchRuns();});
}
setup();
