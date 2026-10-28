import { method, respond } from './_lib.js';
export default async function handler(req,res){
  if(!method(req,['GET'],res))return;
  respond(res,200,{github:Boolean(process.env.GITHUB_TOKEN),accessMode:'vercel-login',ready:Boolean(process.env.HEC_AUTH_MODE==='vercel'&&process.env.HEC_ACCESS_KEY&&process.env.GITHUB_TOKEN),ai:Boolean(process.env.OPENAI_API_KEY),repo:'hecagus/Hecagus-Reels'});
}
