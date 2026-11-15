// Planes estimados, sin cambiar datos ni ejecutar EXPLAIN ANALYZE.
import {pool} from '../server/db.js';
import {queries} from '../server/queries.js';
import {writeFile} from 'node:fs/promises';
if(process.env.GITHUB_ACTIONS!=='true'||process.env.LOAD_TEST_ISOLATED!=='1')throw new Error('Solo en instancia aislada de CI');
try {
 const [[engine]]=await pool.query('SELECT VERSION() AS version');
 const plans=[];
 for(const q of queries){
  const params=q.param?[q.param.default]:[];
  const [rows]=await pool.execute('EXPLAIN '+q.sql,params);
  plans.push({id:q.id,params,plan:rows});
 }
 const report={engine,description:'EXPLAIN estimado sobre el seed; no es una medición de tiempo ni un plan universal.',plans};
 await writeFile('explain-results.json',JSON.stringify(report,null,2)+'\n');
 console.log('EXPLAIN '+JSON.stringify(report));
}finally{await pool.end();}
