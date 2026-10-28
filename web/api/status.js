import {method,respond,ownerSession,sessionKey} from './_lib.js';
export default async function handler(req,res){
 if(!method(req,['GET'],res))return;
 respond(res,200,{
   github:Boolean(process.env.GITHUB_TOKEN),
   loginConfigured:Boolean(process.env.GITHUB_OAUTH_CLIENT_ID&&process.env.GITHUB_OAUTH_CLIENT_SECRET&&sessionKey()),
   signedIn:Boolean(ownerSession(req)),
   ai:Boolean(process.env.OPENAI_API_KEY),
   repo:'hecagus/Hecagus-Reels'
 });
}
