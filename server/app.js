import express from 'express';
import {pool,transaction} from './db.js';
import {entities,validate} from './entities.js';
import {queries} from './queries.js';
export const app=express();
app.disable('x-powered-by');
app.use(express.json({limit:'32kb'}));
app.use((req,res,next)=>{
 res.set('X-Content-Type-Options','nosniff');
 // Same-origin writes only; no permissive CORS and no form-encoded mutations.
 if(!['GET','HEAD','OPTIONS'].includes(req.method)){
  if(!req.is('application/json'))return res.status(415).json({error:'Use application/json'});
  const origin=req.get('origin');
  if(origin){try{if(new URL(origin).host!==req.get('host'))return res.status(403).json({error:'Origen no permitido'});}catch{return res.status(403).json({error:'Origen inválido'});}}
 }
 next();
});
const route=fn=>(req,res,next)=>Promise.resolve(fn(req,res)).catch(next);
const fail=(message,status=400)=>{throw Object.assign(new Error(message),{status});};
const config=table=>Object.hasOwn(entities,table)?entities[table]:fail('Tabla desconocida',404);
const identifier=id=>{if(!/^\d+$/.test(String(id))||!Number.isSafeInteger(Number(id))||Number(id)<1)fail('Identificador inválido');return Number(id);};
const views={
 usuario:`SELECT u.* FROM usuario u`,
 conductor:`SELECT d.*,u.nombres,(SELECT ROUND(AVG(c.puntaje),2) FROM calificacion c JOIN viaje j ON j.id_viaje=c.id_viaje JOIN oferta o ON o.id_oferta=j.id_oferta JOIN vehiculo a ON a.placa=o.placa JOIN solicitud s ON s.id_solicitud=o.id_solicitud WHERE a.id_conductor=d.id_conductor AND c.id_usuario=s.id_usuario) AS calificacion_promedio FROM conductor d JOIN usuario u ON u.id_usuario=d.id_usuario`,
 vehiculo:`SELECT a.*,u.nombres AS conductor FROM vehiculo a JOIN conductor d ON d.id_conductor=a.id_conductor JOIN usuario u ON u.id_usuario=d.id_usuario`,
 solicitud:`SELECT s.*,u.nombres AS pasajero,(SELECT COUNT(*) FROM oferta o WHERE o.id_solicitud=s.id_solicitud) AS ofertas FROM solicitud s JOIN usuario u ON u.id_usuario=s.id_usuario`,
 oferta:`SELECT o.*,s.origen,s.destino,u.nombres AS conductor,CASE WHEN j.id_viaje IS NOT NULL THEN 'aceptada' WHEN s.estado='abierta' THEN 'pendiente' ELSE 'cerrada' END AS estado FROM oferta o JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN vehiculo a ON a.placa=o.placa JOIN conductor d ON d.id_conductor=a.id_conductor JOIN usuario u ON u.id_usuario=d.id_usuario LEFT JOIN viaje j ON j.id_oferta=o.id_oferta`,
 viaje:`SELECT j.*,o.monto AS monto_final,o.placa,s.origen,s.destino,s.id_usuario AS id_pasajero,d.id_usuario AS id_conductor_usuario,p.nombres AS pasajero,u.nombres AS conductor FROM viaje j JOIN oferta o ON o.id_oferta=j.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN usuario p ON p.id_usuario=s.id_usuario JOIN vehiculo a ON a.placa=o.placa JOIN conductor d ON d.id_conductor=a.id_conductor JOIN usuario u ON u.id_usuario=d.id_usuario`,
 pago:`SELECT p.*,s.origen,s.destino FROM pago p JOIN viaje j ON j.id_viaje=p.id_viaje JOIN oferta o ON o.id_oferta=j.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud`,
 calificacion:`SELECT c.*,u.nombres AS autor FROM calificacion c JOIN usuario u ON u.id_usuario=c.id_usuario`
};
app.get('/api/health',route(async(req,res)=>{const [[row]]=await pool.query('SELECT VERSION() AS version,DATABASE() AS base');res.json({connected:true,...row});}));
app.get('/api/config',(req,res)=>res.json(entities));
app.get('/api/dashboard',route(async(req,res)=>{
 const [[row]]=await pool.query(`SELECT (SELECT COUNT(*) FROM usuario) AS usuarios,(SELECT COUNT(*) FROM conductor) AS conductores,(SELECT COUNT(*) FROM solicitud WHERE estado='abierta') AS abiertas,(SELECT COUNT(*) FROM viaje) AS viajes,(SELECT COALESCE(SUM(monto),0) FROM pago) AS cobrado,(SELECT COALESCE(SUM(comision),0) FROM pago) AS comisiones`);
 const [recent]=await pool.query(`${views.solicitud} ORDER BY s.id_solicitud DESC LIMIT 5`);res.json({stats:row,recent});
}));
app.get('/api/options/:table',route(async(req,res)=>{
 const table=req.params.table;config(table);let sql;
 if(table==='usuario')sql=`SELECT id_usuario AS value,CONCAT('#',id_usuario,' · ',nombres) AS label FROM usuario ORDER BY nombres`;
 if(table==='conductor')sql=`SELECT d.id_conductor AS value,CONCAT(u.nombres,' · ',d.licencia) AS label FROM conductor d JOIN usuario u ON u.id_usuario=d.id_usuario ORDER BY u.nombres`;
 if(table==='vehiculo')sql=`SELECT a.placa AS value,CONCAT(a.placa,' · ',u.nombres,' · ',a.marca,' ',a.modelo) AS label FROM vehiculo a JOIN conductor d ON d.id_conductor=a.id_conductor JOIN usuario u ON u.id_usuario=d.id_usuario ORDER BY a.placa`;
 if(table==='solicitud')sql=`SELECT id_solicitud AS value,CONCAT('#',id_solicitud,' · ',origen,' → ',destino) AS label FROM solicitud WHERE estado='abierta' ORDER BY id_solicitud DESC`;
 if(table==='viaje'){
  sql=`SELECT j.id_viaje AS value,CONCAT('#',j.id_viaje,' · ',s.origen,' → ',s.destino,' · S/ ',o.monto) AS label,s.id_usuario AS pasajero,d.id_usuario AS conductor,o.monto FROM viaje j JOIN oferta o ON o.id_oferta=j.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN vehiculo a ON a.placa=o.placa JOIN conductor d ON d.id_conductor=a.id_conductor WHERE j.estado='finalizado'`;
  if(req.query.for==='pago')sql+=' AND NOT EXISTS(SELECT 1 FROM pago p WHERE p.id_viaje=j.id_viaje)';
  sql+=' ORDER BY j.id_viaje DESC';
 }
 if(!sql)fail('No existe selector para esta tabla');const [rows]=await pool.query(sql);res.json(rows);
}));
app.get('/api/explorer',route(async(req,res)=>{
 const [tables]=await pool.query(`SELECT TABLE_NAME AS name,TABLE_COMMENT AS description,ENGINE AS engine FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME`);
 const [columns]=await pool.query(`SELECT TABLE_NAME AS table_name,COLUMN_NAME AS name,COLUMN_TYPE AS type,IS_NULLABLE AS nullable,COLUMN_DEFAULT AS default_value,COLUMN_KEY AS column_key,EXTRA AS extra,COLUMN_COMMENT AS description FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,ORDINAL_POSITION`);
 const [keys]=await pool.query(`SELECT TABLE_NAME AS table_name,CONSTRAINT_NAME AS name,COLUMN_NAME AS column_name,REFERENCED_TABLE_NAME AS referenced_table,REFERENCED_COLUMN_NAME AS referenced_column FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,CONSTRAINT_NAME,ORDINAL_POSITION`);
 const [checks]=await pool.query(`SELECT CONSTRAINT_NAME AS name,CHECK_CLAUSE AS clause FROM information_schema.CHECK_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=DATABASE()`);
 const [relations]=await pool.query(`SELECT TABLE_NAME AS table_name,CONSTRAINT_NAME AS name,REFERENCED_TABLE_NAME AS referenced_table,UPDATE_RULE AS update_rule,DELETE_RULE AS delete_rule FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=DATABASE()`);
 const [triggers]=await pool.query(`SELECT TRIGGER_NAME AS name,EVENT_OBJECT_TABLE AS table_name,ACTION_TIMING AS timing,EVENT_MANIPULATION AS event,ACTION_STATEMENT AS statement FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()`);
 const [indexes]=await pool.query(`SELECT TABLE_NAME AS table_name,INDEX_NAME AS name,COLUMN_NAME AS column_name,NON_UNIQUE AS non_unique,SEQ_IN_INDEX AS position FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX`);
 res.json({tables,columns,keys,checks,relations,triggers,indexes});
}));
app.get('/api/queries',(req,res)=>res.json(queries));
app.post('/api/queries/:id',route(async(req,res)=>{
 const q=queries.find(q=>q.id===req.params.id);if(!q)fail('Consulta desconocida',404);
 const params=[];if(q.param){const v=Number(req.body[q.param.name]??q.param.default);if(!Number.isInteger(v)||v<q.param.min||v>q.param.max)fail('Parámetro fuera de rango');params.push(v);}
 const start=performance.now();const [rows,fields]=await pool.execute(q.sql,params);res.json({rows,columns:fields.map(f=>f.name),ms:Math.round((performance.now()-start)*100)/100,sql:q.sql,params,limit:200});
}));
app.get('/api/data/:table',route(async(req,res)=>{
 const table=req.params.table,cfg=config(table);const term=String(req.query.q||'').slice(0,200),page=Math.max(1,Math.min(100000,parseInt(req.query.page)||1)),size=25;
 const where=term?` WHERE ${cfg.search.map(k=>`CAST(t.\`${k}\` AS CHAR) LIKE ?`).join(' OR ')}`:'';
 const values=cfg.search.map(()=>`%${term}%`);const args=term?values:[];
 const [[{total}]]=await pool.execute(`SELECT COUNT(*) AS total FROM (${views[table]}) t${where}`,args);
 const [rows,fields]=await pool.execute(`SELECT * FROM (${views[table]}) t${where} ORDER BY t.\`${cfg.pk}\` DESC LIMIT ${size} OFFSET ${(page-1)*size}`,args);
 res.json({rows,columns:fields.map(f=>f.name),total,page,pages:Math.max(1,Math.ceil(total/size))});
}));
app.post('/api/data/:table',route(async(req,res)=>{
 const table=req.params.table,cfg=config(table);if(cfg.noCreate)fail('El viaje se crea al aceptar una oferta');const values=validate(table,req.body);
 const id=await transaction(async c=>{
  if(table==='pago'){
   const [rows]=await c.execute(`SELECT v.estado,o.monto FROM viaje v JOIN oferta o ON o.id_oferta=v.id_oferta WHERE v.id_viaje=? FOR UPDATE`,[values.id_viaje]);if(!rows.length)fail('Viaje inexistente');if(rows[0].estado!=='finalizado')fail('El viaje todavía no ha finalizado');values.monto=rows[0].monto;
  }
  const fields=Object.keys(values);const [result]=await c.execute(`INSERT INTO \`${table}\` (${fields.map(k=>'`'+k+'`').join(',')}) VALUES (${fields.map(()=>'?').join(',')})`,Object.values(values));return values[cfg.pk]??result.insertId;
 });res.status(201).json({id,message:'Registro creado en la base de datos'});
}));
app.put('/api/data/:table/:id',route(async(req,res)=>{
 const table=req.params.table,cfg=config(table);if(table==='viaje')fail('Use las transiciones de viaje');const values=validate(table,req.body,true);const id=cfg.pk==='placa'?req.params.id:identifier(req.params.id);
 await transaction(async c=>{const [rows]=await c.execute(`SELECT * FROM \`${table}\` WHERE \`${cfg.pk}\`=? FOR UPDATE`,[id]);if(!rows.length)fail('Registro inexistente',404);const fields=Object.keys(values);await c.execute(`UPDATE \`${table}\` SET ${fields.map(k=>'`'+k+'`=?').join(',')} WHERE \`${cfg.pk}\`=?`,[...Object.values(values),id]);});
 res.json({message:'Registro actualizado'});
}));
app.delete('/api/data/:table/:id',route(async(req,res)=>{
 const table=req.params.table,cfg=config(table);if(cfg.noDelete)fail('La información histórica se conserva');const id=cfg.pk==='placa'?req.params.id:identifier(req.params.id);
 const [result]=await pool.execute(`DELETE FROM \`${table}\` WHERE \`${cfg.pk}\`=?`,[id]);if(!result.affectedRows)fail('Registro inexistente',404);res.json({message:'Registro eliminado'});
}));
app.post('/api/offers/:id/accept',route(async(req,res)=>{
 const id=identifier(req.params.id);
 const result=await transaction(async c=>{
  const [[offer]]=await c.execute('SELECT id_solicitud FROM oferta WHERE id_oferta=?',[id]);if(!offer)fail('Oferta inexistente',404);
  const [[s]]=await c.execute('SELECT estado FROM solicitud WHERE id_solicitud=? FOR UPDATE',[offer.id_solicitud]);if(s.estado!=='abierta')fail('La solicitud ya no está abierta',409);
  const [r]=await c.execute('INSERT INTO viaje (id_oferta) VALUES (?)',[id]);return r.insertId;
 });res.status(201).json({id:result,message:'Oferta aceptada y viaje creado en una sola transacción'});
}));
app.post('/api/requests/:id/cancel',route(async(req,res)=>{
 await transaction(async c=>{const [[s]]=await c.execute('SELECT estado FROM solicitud WHERE id_solicitud=? FOR UPDATE',[identifier(req.params.id)]);if(!s)fail('Solicitud inexistente',404);if(s.estado!=='abierta')fail('Solo puede cancelar solicitudes abiertas',409);await c.execute("UPDATE solicitud SET estado='cancelada' WHERE id_solicitud=?",[req.params.id]);});res.json({message:'Solicitud cancelada; se conservan sus ofertas'});
}));
app.post('/api/trips/:id/:action',route(async(req,res)=>{
 const action=req.params.action;if(!['start','finish'].includes(action))fail('Acción desconocida',404);
 await transaction(async c=>{const id=identifier(req.params.id);const [[v]]=await c.execute('SELECT estado FROM viaje WHERE id_viaje=? FOR UPDATE',[id]);if(!v)fail('Viaje inexistente',404);if(v.estado!==(action==='start'?'pendiente':'en_curso'))fail('El estado del viaje no permite esta acción',409);await c.execute(action==='start'?"UPDATE viaje SET estado='en_curso',hora_inicio=CURRENT_TIMESTAMP WHERE id_viaje=?":"UPDATE viaje SET estado='finalizado',hora_fin=CURRENT_TIMESTAMP WHERE id_viaje=?",[id]);});res.json({message:action==='start'?'Viaje iniciado':'Viaje finalizado'});
}));
app.use('/api',(req,res)=>res.status(404).json({error:'Ruta inexistente'}));
app.use((err,req,res,next)=>{
 let status=err.status||500,message=err.message;
 if(err.code==='ER_DUP_ENTRY'){status=409;message='Ya existe un registro con esa placa, teléfono, correo, licencia o relación única.';}
 if(['ER_ROW_IS_REFERENCED_2','ER_ROW_IS_REFERENCED'].includes(err.code)){status=409;message='El registro tiene relaciones. No puede eliminarse porque se perdería historial.';}
 if(['ER_NO_REFERENCED_ROW_2','ER_NO_REFERENCED_ROW'].includes(err.code)){status=400;message='El registro relacionado no existe. Actualice los selectores.';}
 if(err.sqlState==='45000'){status=409;message=err.sqlMessage;}
 if(['ER_CHECK_CONSTRAINT_VIOLATED','ER_CONSTRAINT_FAILED','WARN_DATA_TRUNCATED','ER_DATA_TOO_LONG'].includes(err.code)){status=400;message='Los datos incumplen una restricción de integridad. Revise rangos, formatos y campos.';}
 if(['ER_LOCK_DEADLOCK','ER_LOCK_WAIT_TIMEOUT'].includes(err.code)){status=409;message='Otra operación modificó estos datos. Actualice e intente otra vez.';}
 if(status>=500){console.error(err.code||err.message);message='No se pudo completar la operación. Compruebe la conexión y la inicialización de la base de datos.';}
 res.status(status).json({error:message});
});
