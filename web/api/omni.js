import {
  method, guard, readBody, respond, errorOut, gh, signedDownload
} from './_lib.js';

const WORKFLOW = 'generar-omni.yml';

export function validateOmniRequest(body) {
  const idea = typeof body?.idea === 'string' ? body.idea.trim().replace(/\s+/g, ' ') : '';
  if (idea.length < 8 || idea.length > 350) {
    throw Object.assign(new Error('Escribe una idea de 8 a 350 caracteres.'), {http: 400});
  }
  const duration = String(body?.duracion || '');
  if (!['6', '60'].includes(duration)) {
    throw Object.assign(new Error('La duración debe ser 6 o 60 segundos.'), {http: 400});
  }
  if (body?.costoAceptado !== true) {
    throw Object.assign(new Error('Debes aceptar expresamente el consumo de la API de pago.'), {http: 400});
  }
  return {idea, duracion: duration};
}

function readable(run) {
  const done = run.status === 'completed' && run.conclusion === 'success';
  return {
    id: run.id, title: run.display_title, created: run.created_at,
    status: run.status, conclusion: run.conclusion, url: run.html_url,
    downloadUrl: done ? signedDownload(run.id) : null
  };
}

export default async function handler(req, res) {
  if (!method(req, ['POST','GET'], res) || !guard(req, res)) return;
  try {
    const path = '/actions/workflows/' + WORKFLOW;
    if (req.method === 'POST') {
      const {idea, duracion} = validateOmniRequest(await readBody(req, 1500));
      // Evita ejecuciones simultáneas desde el estudio. GitHub también serializa los trabajos.
      const current = await (await gh(path + '/runs?event=workflow_dispatch&per_page=10')).json();
      if ((current.workflow_runs || []).some(run => ['queued','in_progress','waiting','pending'].includes(run.status))) {
        respond(res, 409, {error:'Ya existe una producción Omni en curso. Espera a que termine.'});
        return;
      }
      const folio = 'omni' + Date.now().toString(36);
      await gh(path + '/dispatches', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          ref:'main',
          inputs:{idea, duracion, costo_aceptado:'SI', folio}
        })
      });
      respond(res, 202, {accepted:true, folio});
      return;
    }
    const response = await gh(path + '/runs?event=workflow_dispatch&per_page=15');
    const data = await response.json();
    respond(res, 200, {runs: (data.workflow_runs || []).map(readable)});
  } catch(err) {
    errorOut(res, err);
  }
}
