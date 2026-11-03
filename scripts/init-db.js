import 'dotenv/config';
import mysql from 'mysql2/promise';
import fs from 'node:fs/promises';
import {splitSQL} from './sql-parser.js';
import {connectWithRetry} from './connect-db.js';

const database=process.env.DB_NAME||'indrive_academico';
const expectedTables=['calificacion','conductor','oferta','pago','solicitud','usuario','vehiculo','viaje'];
let connection;
try {
 if(database!=='indrive_academico')throw new Error('Los scripts usan DB_NAME=indrive_academico.');
 const user=process.env.DB_USER||'indrive_app';
 if(!/^[a-zA-Z_][a-zA-Z0-9_]{0,31}$/.test(user)||user==='root')throw new Error('DB_USER debe ser una cuenta de aplicación válida, distinta de root.');
 if(process.env.DB_ADMIN_USER&&!process.env.DB_PASSWORD)throw new Error('Defina DB_PASSWORD antes de crear la cuenta de ejecución.');
 connection=await connectWithRetry(options=>mysql.createConnection(options),{host:process.env.DB_HOST||'127.0.0.1',port:Number(process.env.DB_PORT||3306),user:process.env.DB_ADMIN_USER||process.env.DB_USER||'root',password:process.env.DB_ADMIN_PASSWORD??process.env.DB_PASSWORD??'',...(process.env.DB_SOCKET?{socketPath:process.env.DB_SOCKET}:{}),multipleStatements:false,connectTimeout:2000},{onRetry:(attempt,total)=>console.log(`Esperando a MySQL por TCP… intento ${attempt}/${total}`)});
 const [[{version}]]=await connection.query('SELECT VERSION() AS version');
 console.log('Motor:',version);
 const maria=version.includes('MariaDB');
 const [major,minor,patch]=version.match(/^\d+\.\d+\.\d+/)[0].split('.').map(Number);
 if((!maria&&(major<8||(major===8&&minor===0&&patch<16)))||(maria&&(major<10||(major===10&&minor<6))))throw new Error('Se requiere MySQL >=8.0.16 o MariaDB >=10.6.');
 const [tables]=await connection.execute("SELECT TABLE_NAME AS name FROM information_schema.TABLES WHERE TABLE_SCHEMA=? AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME",[database]);
 const exists=tables.length>0;
 if(exists){
  if(!process.argv.includes('--if-empty'))throw new Error('La base ya contiene tablas. Para reutilizarla sin borrar registros, use --if-empty.');
  if(JSON.stringify(tables.map(t=>t.name))!==JSON.stringify(expectedTables))throw new Error('El esquema existente está incompleto o tiene tablas ajenas. No se borró ni sobrescribió información; revise la base.');
  const schema=splitSQL(await fs.readFile('database/01-schema.sql','utf8'));
  const expectedTriggers=schema.filter(s=>s.startsWith('CREATE TRIGGER')).map(s=>s.match(/^CREATE TRIGGER (\w+)/)[1]).sort();
  const [triggers]=await connection.execute('SELECT TRIGGER_NAME AS name FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=? ORDER BY TRIGGER_NAME',[database]);
  if(JSON.stringify(triggers.map(t=>t.name))!==JSON.stringify(expectedTriggers))throw new Error('Las reglas del esquema existente no coinciden. Revise sus triggers; no se alteraron tablas.');
  console.log('Esquema existente: se conserva todo el historial y no se repite el seed.');
 }else{
  for(const file of ['database/01-schema.sql',...(process.argv.includes('--seed')?['database/02-seed.sql']:[])]){
   try {for(const sql of splitSQL(await fs.readFile(file,'utf8')))await connection.query(sql);}
   catch(error){if(file.includes('seed'))await connection.rollback();throw error;}
   console.log('Ejecutado:',file);
  }
 }
 if(process.env.DB_ADMIN_USER){
  for(const host of ['localhost','%']){
   await connection.query('CREATE USER IF NOT EXISTS ?@? IDENTIFIED BY ?',[user,host,process.env.DB_PASSWORD]);
   await connection.query('GRANT SELECT,INSERT,UPDATE,DELETE,SHOW VIEW,TRIGGER ON `indrive_academico`.* TO ?@?',[user,host]);
  }
  console.log('Permisos de la cuenta de ejecución preparados. No se alteran claves de cuentas existentes.');
 }
 console.log('Base de datos lista.');
}catch(error){
 const hints={ECONNREFUSED:'MySQL no está iniciado o el puerto es incorrecto.',EPERM:'Esta sesión no tiene permiso para conectarse a MySQL.',EACCES:'Esta sesión no tiene permiso para conectarse a MySQL.',ER_ACCESS_DENIED_ERROR:'Revise DB_ADMIN_USER y DB_ADMIN_PASSWORD. Un volumen existente conserva su contraseña original.',ENOTFOUND:'El host de MySQL no se pudo resolver.'};
 console.error('No se pudo preparar la base:',hints[error.code]||error.message);
 process.exitCode=1;
}finally{if(connection)await connection.end();}
