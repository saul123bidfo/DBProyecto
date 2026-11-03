const text=(label,max=120,extra={})=>({label,type:'text',max,...extra});
const ref=(label,table,key)=>({label,type:'ref',table,key});
const money=label=>({label,type:'number',min:0.01,max:99999999.99,step:0.01});
export const entities={
 usuario:{title:'Usuarios',singular:'usuario',pk:'id_usuario',fields:{nombres:text('Nombres y apellidos'),telefono:text('Teléfono',20,{minLength:7}),correo:text('Correo',160,{type:'email'})},search:['nombres','telefono','correo']},
 conductor:{title:'Conductores',singular:'conductor',pk:'id_conductor',fields:{id_usuario:ref('Usuario','usuario','id_usuario'),licencia:text('Licencia',20,{minLength:5})},immutable:['id_usuario'],search:['licencia']},
 vehiculo:{title:'Vehículos',singular:'vehículo',pk:'placa',fields:{placa:text('Placa',10,{minLength:5}),id_conductor:ref('Conductor','conductor','id_conductor'),marca:text('Marca',50),modelo:text('Modelo',60),color:text('Color',30),anio:{label:'Año',type:'number',min:1980,max:2100,step:1}},immutable:['placa'],search:['placa','marca','modelo']},
 solicitud:{title:'Solicitudes',singular:'solicitud',pk:'id_solicitud',fields:{id_usuario:ref('Pasajero','usuario','id_usuario'),origen:text('Origen',200),destino:text('Destino',200),precio_ofrecido:money('Precio ofrecido (S/)')},immutable:['id_usuario'],search:['origen','destino','estado']},
 oferta:{title:'Ofertas',singular:'oferta',pk:'id_oferta',fields:{id_solicitud:ref('Solicitud abierta','solicitud','id_solicitud'),placa:ref('Vehículo del conductor','vehiculo','placa'),monto:money('Monto propuesto (S/)'),tiempo_llegada:{label:'Llegada estimada (minutos)',type:'number',min:1,max:240,step:1}},immutable:['id_solicitud','placa'],search:['placa']},
 viaje:{title:'Viajes',singular:'viaje',pk:'id_viaje',fields:{},noCreate:true,noDelete:true,search:['estado']},
 pago:{title:'Pagos',singular:'pago',pk:'id_pago',fields:{id_viaje:ref('Viaje finalizado sin cobro','viaje','id_viaje'),metodo:{label:'Método',type:'select',options:['efectivo','tarjeta','transferencia']},comision:{...money('Comisión (S/)'),min:0}},immutable:['id_viaje'],noDelete:true,search:['metodo']},
 calificacion:{title:'Calificaciones',singular:'calificación',pk:'id_calificacion',fields:{id_viaje:ref('Viaje finalizado','viaje','id_viaje'),id_usuario:ref('Autor participante','usuario','id_usuario'),puntaje:{label:'Puntaje',type:'number',min:1,max:5,step:1},comentario:text('Comentario',500,{optional:true})},immutable:['id_viaje','id_usuario'],noDelete:true,search:['comentario']}
};
export function validate(table,body,updating=false){
 const config=Object.hasOwn(entities,table)?entities[table]:null; const values={};
 if(!config) throw Object.assign(new Error('Entidad desconocida'),{status:404});
 if(!body||typeof body!=='object'||Array.isArray(body))throw Object.assign(new Error('Datos inválidos'),{status:400});
 for(const [name,f] of Object.entries(config.fields)){
  if(updating&&config.immutable?.includes(name))continue;
  let v=body[name];
  if(f.optional&&(v===undefined||v===null))v='';
  if(v===undefined||v===null||(!f.optional&&String(v).trim()===''))throw Object.assign(new Error(`Falta ${f.label}`),{status:400});
  if(f.type==='number'||(f.type==='ref'&&f.key!=='placa')){
   if(typeof v!=='string'&&typeof v!=='number')throw Object.assign(new Error(`${f.label}: valor inválido`),{status:400});
   v=Number(v);const min=f.min??1,max=f.max??2147483647;
   if(!Number.isFinite(v)||v<min||v>max||((f.step===1||f.type==='ref')&&!Number.isInteger(v))||(f.step===0.01&&Math.abs(v*100-Math.round(v*100))>0.000001))throw Object.assign(new Error(`${f.label}: valor fuera de rango o precisión inválida`),{status:400});
  }else{
   if(typeof v!=='string')throw Object.assign(new Error(`${f.label}: texto inválido`),{status:400});
   v=v.trim();if(v.length>(f.max??500)||v.length<(f.minLength??0)||(f.type==='email'&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v))||(f.options&&!f.options.includes(v)))throw Object.assign(new Error(`${f.label}: formato inválido`),{status:400});
  }
  values[name]=v;
 }
 return values;
}
