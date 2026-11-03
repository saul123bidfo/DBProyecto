import {setTimeout as delay} from 'node:timers/promises';
const transient=new Set(['ECONNREFUSED','ECONNRESET','ETIMEDOUT','EAI_AGAIN','PROTOCOL_CONNECTION_LOST']);
// Reintenta solo la conexión, nunca una sentencia SQL que podría haberse aplicado.
export async function connectWithRetry(connect,options,{attempts=30,interval=2000,wait=delay,onRetry=()=>{}}={}){
 if(!Number.isInteger(attempts)||attempts<1)throw new Error('Número de intentos inválido');
 for(let attempt=1;attempt<=attempts;attempt++){
  try{return await connect(options);}
  catch(error){
   if(!transient.has(error.code)||attempt===attempts)throw error;
   onRetry(attempt,attempts);
   await wait(interval);
  }
 }
}
