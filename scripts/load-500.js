// Solo para la instancia aislada de GitHub Actions creada por este repositorio.
import {performance} from 'node:perf_hooks';
import {writeFile} from 'node:fs/promises';

if (process.env.GITHUB_ACTIONS !== 'true' || process.env.LOAD_TEST_ISOLATED !== '1') {
 throw new Error('Esta prueba solo se ejecuta en la instancia aislada de GitHub Actions.');
}
const base='http://127.0.0.1:3000';
const queryIds=['viajes','promedios','economicas','sin-ofertas','cobros','abiertas'];
const count=500;
const results=[];
const percentile=(sorted,p)=>sorted[Math.ceil(p*sorted.length)-1] ?? null;
const round=n=>Math.round(n*100)/100;
async function health(){
 const r=await fetch(base+'/api/health',{signal:AbortSignal.timeout(15000),redirect:'error'});
 const data=await r.json();
 if(!r.ok || data.connected!==true)throw new Error('Health falló: HTTP '+r.status+' '+JSON.stringify(data));
 return data;
}
async function query(id){
 const started=performance.now();
 try {
  const r=await fetch(base+'/api/queries/'+id,{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify(id==='promedios'?{minimo:1}:{}),signal:AbortSignal.timeout(15000),redirect:'error'});
  let data;
  try {data=await r.json();} catch {data={error:'Respuesta JSON inválida'};}
  const ms=performance.now()-started;
  if(!r.ok)return {ok:false,ms,error:'HTTP '+r.status+': '+String(data.error||'sin detalle').slice(0,240)};
  if(!Array.isArray(data.rows)||typeof data.sql!=='string')return {ok:false,ms,error:'Respuesta de consulta inválida (HTTP '+r.status+')'};
  return {ok:true,ms};
 } catch(e){return {ok:false,ms:performance.now()-started,error:'Red/timeout: '+e.message};}
}
async function scenario(concurrency){
 let next=0; const samples=new Array(count);
 const started=performance.now();
 async function worker(){
  while(true){
   const i=next++;
   if(i>=count)return;
   samples[i]=await query(queryIds[i%queryIds.length]);
  }
 }
 await Promise.all(Array.from({length:concurrency},()=>worker()));
 const duration=(performance.now()-started)/1000;
 const latencies=samples.map(s=>s.ms).sort((a,b)=>a-b);
 const ok=samples.filter(s=>s.ok).length;
 const errors={};for(const item of samples.filter(s=>!s.ok))errors[item.error]=(errors[item.error]||0)+1;
 let db;
 try {db={ok:true,...await health()};}catch(e){db={ok:false,error:e.message};}
 return {concurrency,total:count,successful:ok,failed:count-ok,duration_seconds:round(duration),
  completed_requests_per_second:round(count/duration),successful_requests_per_second:round(ok/duration),
  latency_ms:{average:round(latencies.reduce((a,b)=>a+b,0)/count),p50:round(percentile(latencies,.50)),p95:round(percentile(latencies,.95)),p99:round(percentile(latencies,.99))},
  errors,database_after:db};
}
const metadata={node:process.version,platform:process.platform,arch:process.arch,started_at:new Date().toISOString(),
 host:base,requests_per_scenario:count,query_ids:queryIds,workload:'read-only SQL via POST API',
 dataset:'database/02-seed.sql; small synthetic dataset',percentile_method:'nearest-rank; includes successes and failures'};
let fatal=null;
try{
 metadata.database_before=await health();
 for(const id of queryIds){const r=await query(id);if(!r.ok)throw new Error('Calentamiento '+id+': '+r.error);}
 for(const n of [5,25,50]){
  const result=await scenario(n); results.push(result); console.log('RESULTADO '+JSON.stringify(result));
 }
}catch(e){fatal=e.message;console.error('ERROR: '+fatal);}
const report={metadata,results,fatal};
await writeFile('load-results.json',JSON.stringify(report,null,2)+'\n');
console.log('INFORME '+JSON.stringify(report));
if(fatal || results.length!==3 || results.some(r=>r.failed>0||!r.database_after.ok))process.exitCode=1;
