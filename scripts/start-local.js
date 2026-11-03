// Usa únicamente módulos de Node; funciona antes de instalar las dependencias del host.
import {spawnSync} from 'node:child_process';
import {existsSync,copyFileSync,readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
process.chdir(root);
if(!existsSync('.env')){copyFileSync('.env.example','.env');console.log('Creado .env local a partir del ejemplo.');}
const check=spawnSync('docker',['version','--format','{{.Server.Version}}'],{encoding:'utf8'});
if(check.error||check.status!==0||!check.stdout.trim()){
 console.error('No se puede acceder a Docker. Abre Docker Desktop o inicia el servicio Docker y usa una terminal con acceso al daemon.');
 console.error('Si este comando se ejecuta dentro del sandbox de Codex, ejecútalo en tu terminal del sistema: npm run local');
 process.exit(1);
}
const compose=spawnSync('docker',['compose','version'],{stdio:'inherit'});
if(compose.status!==0){console.error('Instala Docker Compose v2 para continuar.');process.exit(1);}
const result=spawnSync('docker',['compose','up','--build','-d','--wait','--wait-timeout','240'],{stdio:'inherit'});
if(result.status!==0){console.error('El arranque no terminó. Revisa: docker compose logs --tail=80 db setup app');process.exit(1);}
const env=readFileSync('.env','utf8');
const port=process.env.PORT||env.match(/^PORT\s*=\s*["']?(\d+)/m)?.[1]||3000;
console.log(`\nAplicación y MySQL iniciados: http://127.0.0.1:${port}\nLos datos existentes se conservan. Para detener: npm run local:stop`);
