#!/usr/bin/env python3
"""Copia y empaqueta solo fuentes autorizadas. No publica ni copia secretos o datos locales."""
from pathlib import Path
import shutil, subprocess, zipfile
root=Path(__file__).resolve().parents[1]
release=root/'release'
target=release/'indrive-lab'
archive=release/'indrive-lab-github.zip'
files=['.env.example','.gitignore','.dockerignore','.nvmrc','Dockerfile','compose.yaml','package.json','package-lock.json','README.md','iniciar.sh','Informe_inDrive.docx']
folders=['client','server','database','scripts','tests','docs','.github']
release.mkdir(exist_ok=True)
# No se elimina el destino: preserva su historial Git, si el usuario ya lo creó.
target.mkdir(exist_ok=True)
selected=[]
for file in files:
    source=root/file
    if not source.is_file():raise SystemExit('Falta archivo necesario: '+file)
    selected.append(source)
for folder in folders:
    for source in (root/folder).rglob('*'):
        if source.is_file() and '__pycache__' not in source.parts:
            selected.append(source)
for source in selected:
    relative=source.relative_to(root)
    if any(part in {'.env','node_modules','.git','.aws','.codex','.agents','dist','.runtime'} for part in relative.parts):
        raise SystemExit('Archivo local no permitido: '+str(relative))
    if source.name.startswith('.env') and source.name!='.env.example':raise SystemExit('Archivo de entorno no permitido')
    destination=target/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for source in selected:
        relative=source.relative_to(root)
        z.write(target/relative,Path('indrive-lab')/relative)
with zipfile.ZipFile(archive) as z:
    assert all(not any(part in {'.env','.git','node_modules','.aws','.codex','.agents','dist','.runtime'} for part in Path(name).parts) for name in z.namelist())
    assert 'indrive-lab/package-lock.json' in z.namelist()
    assert 'indrive-lab/.github/workflows/ci.yml' in z.namelist()
if shutil.which('git'):
    if not (target/'.git').exists():subprocess.run(['git','-C',str(target),'init','--initial-branch=main'],check=True)
    # Solo prepara archivos de esta copia, sin incluir ficheros ajenos que pudieran existir.
    subprocess.run(['git','-C',str(target),'add','--']+[str(p.relative_to(root)) for p in selected],check=True)
print(f'Copia de fuentes y repositorio local: {target}')
print(f'ZIP sin credenciales ni datos locales: {archive}')
print('No se creó ningún repositorio remoto ni se publicó información en GitHub.')
