import {test} from 'node:test';
import assert from 'node:assert/strict';
import {connectWithRetry} from '../scripts/connect-db.js';
test('espera al servidor TCP después de conexiones rechazadas',async()=>{
 let calls=0;const waits=[],retries=[],connection={connected:true},options={host:'db',port:3306};
 const result=await connectWithRetry(async config=>{assert.equal(config,options);calls++;if(calls<3)throw Object.assign(new Error('No disponible'),{code:'ECONNREFUSED'});return connection;},options,{wait:async ms=>waits.push(ms),onRetry:n=>retries.push(n)});
 assert.equal(result,connection);assert.equal(calls,3);assert.deepEqual(waits,[2000,2000]);assert.deepEqual(retries,[1,2]);
});
test('rechaza credenciales o permisos sin reintentar',async()=>{
 for(const code of ['ER_ACCESS_DENIED_ERROR','EPERM']){
  let calls=0;const error=Object.assign(new Error(code),{code});
  await assert.rejects(connectWithRetry(async()=>{calls++;throw error;},{},{wait:async()=>assert.fail('No debe esperar')}),e=>e===error);
  assert.equal(calls,1);
 }
});
test('limita los reintentos y conserva el error original',async()=>{
 let calls=0,waits=0;const error=Object.assign(new Error('Tiempo agotado'),{code:'ETIMEDOUT'});
 await assert.rejects(connectWithRetry(async()=>{calls++;throw error;},{},{attempts:3,wait:async()=>{waits++;}}),e=>e===error);
 assert.equal(calls,3);assert.equal(waits,2);
});
