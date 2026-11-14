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

// Dos ofertas distintas de una misma solicitud compiten en paralelo.
const placa2='U'+token.slice(-7);
await ok('/data/vehiculo','POST',{placa:placa2,id_conductor:c.id,marca:'Kia',modelo:'Rio',color:'Azul',anio:2021});
const s2=await ok('/data/solicitud','POST',{id_usuario:p.id,origen:'Origen concurrencia '+token,destino:'Destino concurrencia',precio_ofrecido:18});
const b1=await ok('/data/oferta','POST',{id_solicitud:s2.id,placa,monto:21,tiempo_llegada:5});
const b2=await ok('/data/oferta','POST',{id_solicitud:s2.id,placa:placa2,monto:22,tiempo_llegada:6});
const race=await Promise.all([request(`/offers/${b1.id}/accept`,'POST',{}),request(`/offers/${b2.id}/accept`,'POST',{})]);
assert.deepEqual(race.map(r=>r.status).sort(),[201,409]);
const winnerId=race.find(r=>r.status===201).id;
const trips=await ok('/data/viaje');
const matching=trips.rows.filter(row=>[b1.id,b2.id].includes(row.id_oferta));
assert.equal(matching.length,1);
assert.equal(matching[0].id_viaje,winnerId);
const requests=await ok('/data/solicitud?q='+encodeURIComponent('Origen concurrencia '+token));
assert.equal(requests.rows.find(row=>row.id_solicitud===s2.id)?.estado,'aceptada');

// Una aceptación rechazada no debe crear un viaje ni cambiar la solicitud cancelada.
const s3=await ok('/data/solicitud','POST',{id_usuario:p.id,origen:'Origen rollback '+token,destino:'Destino rollback',precio_ofrecido:15});
const rejectedOffer=await ok('/data/oferta','POST',{id_solicitud:s3.id,placa,monto:16,tiempo_llegada:5});
await ok(`/requests/${s3.id}/cancel`,'POST',{});
assert.equal((await request(`/offers/${rejectedOffer.id}/accept`,'POST',{})).status,409);
const afterFailure=await ok('/data/viaje');
assert.equal(afterFailure.rows.some(row=>row.id_oferta===rejectedOffer.id),false);
const cancelled=await ok('/data/solicitud?q='+encodeURIComponent('Origen rollback '+token));
assert.equal(cancelled.rows.find(row=>row.id_solicitud===s3.id)?.estado,'cancelada');
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
