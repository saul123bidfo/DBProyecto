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
// Comprueba ROLLBACK después de una escritura real en una transacción.
const {pool,transaction}=await import('../server/db.js');
const rollbackOrigin='Rollback transacción '+token;
try {
 await assert.rejects(transaction(async connection=>{
  await connection.execute('INSERT INTO solicitud(id_usuario,origen,destino,precio_ofrecido) VALUES(?,?,?,?)',[p.id,rollbackOrigin,'Destino prueba',10]);
  throw new Error('Forzar rollback de prueba');
 }),/Forzar rollback de prueba/);
 const [[rolledBack]]=await pool.execute('SELECT COUNT(*) AS total FROM solicitud WHERE origen=?',[rollbackOrigin]);
 assert.equal(rolledBack.total,0);
} finally {await pool.end();}
const explorer=await ok('/explorer');assert.equal(explorer.tables.length,8);assert.equal(explorer.keys.filter(k=>k.referenced_table).length,9);
const catalog=await ok('/queries');for(const q of Object.values(catalog).filter(q=>q&&typeof q==='object'&&q.id))await ok('/queries/'+q.id,'POST',q.param?{[q.param.name]:q.param.default}:{});
assert.equal((await request('/queries/inventada','POST',{})).status,404);
console.log('PASS: alta, FK, rechazo de borrado, aceptación concurrente, viaje, cobro, calificación, metadatos y consultas.');
// ---- Ediciones, operaciones inválidas y restricciones (todas deben ser rechazadas con el estado HTTP correcto) ----
const status=async(path,method,body)=>(await request(path,method,body)).status;
// Edición de registros existentes
await ok('/data/usuario/'+p.id,'PUT',{nombres:'Pasajero editado '+token,telefono:'+51'+token.slice(-10),correo:`p${token}@example.test`});
assert.equal((await ok('/data/usuario?q='+encodeURIComponent('Pasajero editado '+token))).total,1);
await ok('/data/vehiculo/'+placa,'PUT',{id_conductor:c.id,marca:'Toyota',modelo:'Yaris Cross',color:'Gris',anio:2023});
await ok('/data/conductor/'+c.id,'PUT',{licencia:'T'+token+'X'});
// Unicidad (UNIQUE) y formato
assert.equal(await status('/data/usuario','POST',{nombres:'Duplicado',telefono:'+51'+token.slice(-10),correo:`otro${token}@example.test`}),409);
assert.equal(await status('/data/usuario','POST',{nombres:'Duplicado',telefono:'+99'+token.slice(-10),correo:`p${token}@example.test`}),409);
assert.equal(await status('/data/usuario','POST',{nombres:'Sin correo válido',telefono:'+98'+token.slice(-10),correo:'no-es-correo'}),400);
assert.equal(await status('/data/conductor','POST',{id_usuario:d.id,licencia:'OTRA'+token}),409);
assert.equal(await status('/data/vehiculo','POST',{placa,id_conductor:c.id,marca:'X',modelo:'Y',color:'Z',anio:2020}),409);
// Integridad referencial: FK inexistente y borrado restringido
assert.equal(await status('/data/solicitud','POST',{id_usuario:99999999,origen:'A',destino:'B',precio_ofrecido:10}),400);
assert.equal(await status('/data/conductor/'+c.id,'DELETE',{}),409);
assert.equal(await status('/data/vehiculo/'+placa,'DELETE',{}),409);
assert.equal(await status('/data/viaje/'+v.id,'DELETE',{}),400);
assert.equal(await status('/data/pago/1','DELETE',{}),400);
// CHECK y validación: importes, puntajes, origen igual a destino
assert.equal(await status('/data/solicitud','POST',{id_usuario:p.id,origen:'Mismo',destino:'Mismo',precio_ofrecido:10}),400);
assert.equal(await status('/data/solicitud','POST',{id_usuario:p.id,origen:'A',destino:'B',precio_ofrecido:-5}),400);
assert.equal(await status('/data/calificacion','POST',{id_viaje:v.id,id_usuario:p.id,puntaje:6,comentario:''}),400);
assert.equal(await status('/data/pago','POST',{id_viaje:v.id,metodo:'bitcoin',comision:1}),400);
assert.equal(await status('/data/oferta','POST',{id_solicitud:s.id,placa,monto:0,tiempo_llegada:3}),400);
// Reglas de negocio implementadas con triggers
assert.equal(await status('/data/oferta','POST',{id_solicitud:s.id,placa,monto:25,tiempo_llegada:3}),409,'solicitud ya aceptada');
const propia=await ok('/data/solicitud','POST',{id_usuario:d.id,origen:'Solicitud del conductor',destino:'Destino propio',precio_ofrecido:12});
assert.equal(await status('/data/oferta','POST',{id_solicitud:propia.id,placa,monto:13,tiempo_llegada:3}),409,'el conductor no oferta en su propia solicitud');
assert.equal(await status('/data/pago','POST',{id_viaje:v.id,metodo:'tarjeta',comision:9999}),400,'comisión mayor al monto');
// Estados de viaje y de solicitud
assert.equal(await status(`/trips/${v.id}/start`,'POST',{}),409);
assert.equal(await status(`/trips/${v.id}/finish`,'POST',{}),409);
assert.equal(await status(`/trips/999999999/start`,'POST',{}),404);
assert.equal(await status(`/requests/${s.id}/cancel`,'POST',{}),409);
assert.equal(await status('/offers/999999999/accept','POST',{}),404);
// Identificadores y rutas inválidas
assert.equal(await status('/data/inexistente'),404);
assert.equal(await status('/data/usuario/abc','PUT',{}),400);
assert.equal(await status('/queries/promedios','POST',{minimo:0}),400);
assert.equal(await status('/queries/inventada/explain','POST',{}),404);
// Búsqueda por nombre visible y paginación
const porNombre=await ok('/data/solicitud?q='+encodeURIComponent('Pasajero editado '+token));
assert.ok(porNombre.total>=2&&porNombre.rows.every(r=>r.pasajero.includes('Pasajero editado')));
const todas=await ok('/data/solicitud?page=1');assert.equal(todas.rows.length,Math.min(25,todas.total));assert.equal(todas.pages,Math.ceil(todas.total/25));
const ultima=await ok('/data/solicitud?page='+todas.pages);assert.ok(ultima.rows.length>=1&&ultima.rows.length<=25);
// Panel: las agregaciones de MySQL deben coincidir con los totales de las tablas
const dash=await ok('/dashboard');
const totalSolicitudes=(await ok('/data/solicitud')).total;
assert.equal(dash.charts.solicitudes.reduce((a,r)=>a+r.total,0),totalSolicitudes);
assert.ok(Math.abs(dash.charts.pagosPorMetodo.reduce((a,r)=>a+r.monto,0)-dash.stats.cobrado)<0.005);
assert.equal(dash.charts.pagosPorMetodo.reduce((a,r)=>a+r.pagos,0),(await ok('/data/pago')).total);
assert.ok(dash.charts.viajesPorMes.every(r=>/^\d{4}-\d{2}$/.test(r.mes)&&r.total>0));
assert.ok(dash.charts.conductores.every(r=>r.promedio>=1&&r.promedio<=5&&r.evaluaciones>=dash.charts.minimoEvaluaciones));
assert.ok(dash.actividad.length>0&&dash.actividad.length<=5);
// EXPLAIN real de cada consulta del catálogo
for(const q of Object.values(catalog).filter(q=>q&&typeof q==='object'&&q.id)){const plan=await ok(`/queries/${q.id}/explain`,'POST',q.param?{[q.param.name]:q.param.default}:{});assert.ok(plan.rows.length>0&&plan.columns.includes('table'));}
console.log('PASS: ediciones, rechazos (UNIQUE, FK, CHECK, triggers, estados), búsqueda, panel con agregaciones y EXPLAIN.');

