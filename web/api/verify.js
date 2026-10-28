import {method,respond} from './_lib.js';
// Legacy endpoint intentionally disabled: passwords are no longer accepted from browsers.
export default async function handler(req,res){
 if(!method(req,['POST'],res))return;
 respond(res,410,{error:'Se eliminó la comprobación de clave. Usa el inicio de sesión con GitHub.'});
}
