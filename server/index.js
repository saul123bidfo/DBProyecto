import {app} from './app.js';
import {pool} from './db.js';
import {startupError} from './startup-errors.js';
import {existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import express from 'express';
const root=fileURLToPath(new URL('../',import.meta.url));
const host=process.env.HOST||'127.0.0.1',port=Number(process.env.PORT||3000);
let vite,server;
try {
 if(!Number.isInteger(port)||port<1||port>65535)throw Object.assign(new Error('Puerto inválido'),{code:'INVALID_PORT'});
 const [[db]]=await pool.query('SELECT VERSION() AS version,DATABASE() AS name');
 await pool.query('SELECT id_usuario FROM usuario LIMIT 1');
 console.log(`Base conectada: ${db.name} · ${db.version}`);
 if(process.argv.includes('--dev')){
  const {createServer}=await import('vite');
  vite=await createServer({configFile:path.join(root,'client/vite.config.js'),server:{middlewareMode:true}});
  app.use(vite.middlewares);
 }else{
  if(!existsSync(path.join(root,'dist/index.html'))){console.error('Falta compilar la interfaz. Ejecuta npm run build o usa npm run dev.');await pool.end();process.exitCode=1;}
  else{app.use(express.static(path.join(root,'dist')));app.get('*',(req,res)=>res.sendFile(path.join(root,'dist/index.html')));}
 }
 if(!process.exitCode){
  server=await new Promise((resolve,reject)=>{const listener=app.listen(port,host,()=>resolve(listener));listener.once('error',reject);});
  console.log(`Aplicación: http://${host==='0.0.0.0'?'127.0.0.1':host}:${port}`);
 }
}catch(error){
 console.error(startupError(error,{port,dbPort:process.env.DB_PORT||3306}));
 if(vite)await vite.close();
 await pool.end();process.exitCode=1;
}
async function shutdown(){if(server)await new Promise(resolve=>server.close(resolve));if(vite)await vite.close();await pool.end();}
for(const signal of ['SIGINT','SIGTERM'])process.once(signal,()=>shutdown().then(()=>process.exit(0)));
