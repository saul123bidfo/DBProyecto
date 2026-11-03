// Ejecutar sobre una instancia de exposición o prueba: añade un viaje histórico, nunca borra historial.
import assert from 'node:assert/strict';
if(process.env.ALLOW_INTEGRATION_WRITES!=='1')throw new Error('Ejecute ALLOW_INTEGRATION_WRITES=1 npm run test:integration sobre una base de prueba. El flujo agrega registros históricos.');
const base=process.env.TEST_URL||'http://127.0.0.1:3000';
async function request(path,method='GET',body){const r=await fetch(base+'/api'+path,{method,headers:{'Content-Type':'application/json'},...(body===undefined?{}:{body:JSON.stringify(body)})});const data=await r.json();return {status:r.status,...data};}
async function ok(path,method='GET',body){const r=await request(path,method,body);assert.ok(r.status<300,JSON.stringify(r));return r;}
const token=String(Date.now());
assert.equal((await ok('/health')).connected,true);
const p=await ok('/data/usuario','POST',{nombres:'Pasajero integración '+token,telefono:'+51'+token.slice(-10),correo:`p${token}@example.test`});
const d=await ok('/data/usuario','POST',{nombres:'Conductor integración '+token,telefono:'+52'+token.slice(-10),correo:`d${token}@example.test`});
const stranger=await ok('/data/usuario','POST',{nombres:'Ajeno integración '+token,telefono:'+53'+token.slice(-10),correo:`a${token}@example.test`});
const c=await ok('/data/conductor','POST',{id_usuario:d.id,licencia:'T'+token});
const placa='T'+token.slice(-7);
await ok('/data/vehiculo','POST',{placa,id_conductor:c.id,marca:'Toyota',modelo:'Yaris',color:'Blanco',anio:2022});
const s=await ok('/data/solicitud','POST',{id_usuario:p.id,origen:'Prueba origen',destino:'Prueba destino',precio_ofrecido:18});
const a=await ok('/data/oferta','POST',{id_solicitud:s.id,placa,monto:20,tiempo_llegada:4});
assert.equal((await request('/data/usuario/'+p.id,'DELETE',{})).status,409);
const accepted=await Promise.all([request(`/offers/${a.id}/accept`,'POST',{}),request(`/offers/${a.id}/accept`,'POST',{})]);
assert.deepEqual(accepted.map(r=>r.status).sort(),[201,409]);
const v=accepted.find(r=>r.status===201);
assert.equal((await request('/data/pago','POST',{id_viaje:v.id,metodo:'efectivo',comision:1})).status,400);
await ok(`/trips/${v.id}/start`,'POST',{});
await ok(`/trips/${v.id}/finish`,'POST',{});
await ok('/data/pago','POST',{id_viaje:v.id,metodo:'efectivo',comision:1.90});
assert.equal((await request('/data/pago','POST',{id_viaje:v.id,metodo:'efectivo',comision:1.90})).status,409);
assert.equal((await request('/data/calificacion','POST',{id_viaje:v.id,id_usuario:stranger.id,puntaje:5,comentario:''})).status,409);
await ok('/data/calificacion','POST',{id_viaje:v.id,id_usuario:p.id,puntaje:5,comentario:'Flujo validado'});
await ok('/data/calificacion','POST',{id_viaje:v.id,id_usuario:d.id,puntaje:4,comentario:'Pasajero puntual'});
const explorer=await ok('/explorer');assert.equal(explorer.tables.length,8);assert.equal(explorer.keys.filter(k=>k.referenced_table).length,9);
const catalog=await ok('/queries');for(const q of Object.values(catalog).filter(q=>q&&typeof q==='object'&&q.id))await ok('/queries/'+q.id,'POST',q.param?{[q.param.name]:q.param.default}:{});
assert.equal((await request('/queries/inventada','POST',{})).status,404);
console.log('PASS: alta, FK, rechazo de borrado, aceptación concurrente, viaje, cobro, calificación, metadatos y consultas.');
