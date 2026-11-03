import 'dotenv/config';
import {existsSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import mysql from 'mysql2/promise';
console.log('Node:',process.version);
console.log('Archivo .env:',existsSync('.env')?'presente':'falta (copiar .env.example)');
console.log('Interfaz compilada:',existsSync('dist/index.html')?'sí':'no (npm run build)');
console.log('Configuración:',JSON.stringify({host:process.env.DB_HOST||'127.0.0.1',port:process.env.DB_PORT||3306,database:process.env.DB_NAME||'indrive_academico',appPort:process.env.PORT||3000}));
console.log('Contraseñas: se omiten del diagnóstico.');
const docker=spawnSync('docker',['version','--format','{{.Server.Version}}'],{encoding:'utf8',timeout:5000});
console.log('Docker:',docker.status===0&&docker.stdout.trim()?'disponible ('+docker.stdout.trim()+')':'no accesible desde esta sesión');
let c;
try {
 c=await mysql.createConnection({host:process.env.DB_HOST||'127.0.0.1',port:Number(process.env.DB_PORT||3306),user:process.env.DB_USER||'indrive_app',password:process.env.DB_PASSWORD||'',database:process.env.DB_NAME||'indrive_academico',...(process.env.DB_SOCKET?{socketPath:process.env.DB_SOCKET}:{}),connectTimeout:4000});
 const [[r]]=await c.query('SELECT VERSION() AS version');
 const [[{tables}]]=await c.query("SELECT COUNT(*) AS tables FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE'");
 console.log('MySQL/MariaDB:',r.version,'·',tables,'tablas');
 if(tables!==8)process.exitCode=1;
}catch(e){console.log('Conexión SQL:',e.code||'falló');process.exitCode=1;}finally{if(c)await c.end();}
try {const response=await fetch(`http://127.0.0.1:${process.env.PORT||3000}/api/health`,{signal:AbortSignal.timeout(4000)});console.log('API:',response.ok?'conectada':`HTTP ${response.status}`);if(!response.ok)process.exitCode=1;}
catch(e){console.log('API:',e.cause?.code||'no responde');process.exitCode=1;}
