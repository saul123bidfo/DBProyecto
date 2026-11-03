#!/usr/bin/env python3
"""Genera anexos a partir del catálogo real exportado por verify-sql.py."""
from pathlib import Path
from html import escape as esc
import json
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'docs/DICCIONARIO.json').read_text())
text=['# Diccionario del modelo físico','', 'Exportado de INFORMATION_SCHEMA en MariaDB 11.8.6. La aplicación muestra el catálogo de su conexión activa; este anexo es una instantánea del esquema validado.','']
fks=[k for k in data['keys'] if k['referenced_table']]
for table in sorted(data['tables'],key=lambda t:t['name']):
    name=table['name'];text+=['## '+name,'',table['description'],'','| Atributo | Tipo | Nulo | Predeterminado | Claves | Descripción |','|---|---|---|---|---|---|']
    for c in [c for c in data['columns'] if c['table_name']==name]:
        keys=[('FK → '+k['referenced_table']+'.'+k['referenced_column']) if k['referenced_table'] else ('PK' if k['name']=='PRIMARY' else 'UNIQUE: '+k['name']) for k in data['keys'] if k['table_name']==name and k['column_name']==c['name']]
        text.append('| '+' | '.join(str(v or '—').replace('|','\\|') for v in [c['name'],c['type'],c['nullable'],c['default_value'],', '.join(keys),c['description'] or c['extra']])+' |')
    text.append('')
text+=['## Relaciones','', '| FK | Referencia | Borrado / actualización |','|---|---|---|']
for k in fks:text.append(f"| {k['table_name']}.{k['column_name']} | {k['referenced_table']}.{k['referenced_column']} | RESTRICT / RESTRICT |")
(root/'docs/DICCIONARIO.md').write_text('\n'.join(text)+'\n')
pos={'usuario':(30,40),'conductor':(360,40),'vehiculo':(690,40),'solicitud':(30,340),'oferta':(360,340),'viaje':(690,340),'calificacion':(360,640),'pago':(690,640)}
w,h=270,238
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="990" viewBox="0 0 1000 990"><title>Modelo entidad-relación académico de inDrive</title><rect width="1000" height="990" fill="#f6f9f2"/><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="none" stroke="#618073"/></marker></defs><g font-family="sans-serif">']
for k in fks:
    a,b=pos[k['table_name']],pos[k['referenced_table']];vertical=a[1]!=b[1]
    x1=a[0]+(w/2 if vertical else w if a[0]<b[0] else 0);y1=a[1]+((0 if a[1]>b[1] else h) if vertical else h/2)
    x2=b[0]+(w/2 if vertical else 0 if a[0]<b[0] else w);y2=b[1]+((h if a[1]>b[1] else 0) if vertical else h/2)
    d=f'M{x1} {y1} V{(y1+y2)/2} H{x2} V{y2}' if vertical else f'M{x1} {y1} H{(x1+x2)/2} V{y2} H{x2}'
    svg.append(f'<path d="{d}" fill="none" stroke="#618073" stroke-width="1.5" marker-end="url(#arrow)"/>')
    unique=any(x['table_name']==k['table_name'] and x['column_name']==k['column_name'] and x['name']!='PRIMARY' and not x['referenced_table'] and sum(1 for z in data['keys'] if z['name']==x['name'] and z['table_name']==x['table_name'])==1 for x in data['keys'])
    svg.append(f'<text x="{x1+6}" y="{y1+(-8 if a[1]>b[1] else 15)}" font-size="10" fill="#52713d">{"0..1" if unique else "0..N"}</text><text x="{x2+6}" y="{y2+(-8 if a[1]>b[1] else 15)}" font-size="10" fill="#52713d">1</text>')
for table in data['tables']:
    name=table['name'];x,y=pos[name]
    svg.append(f'<g transform="translate({x} {y})"><rect width="{w}" height="{h}" rx="9" fill="white" stroke="#d6e2da"/><path d="M9 0H261Q270 0 270 9V40H0V9Q0 0 9 0" fill="#173b2d"/><text x="15" y="26" font-size="15" fill="white">{name}</text>')
    for i,c in enumerate([c for c in data['columns'] if c['table_name']==name]):
        key='PK' if c['column_key']=='PRI' else 'FK' if any(k['table_name']==name and k['column_name']==c['name'] for k in fks) else ''
        svg.append(f'<text x="12" y="{61+i*21}" font-size="10" fill="#71924a">{key}</text><text x="40" y="{61+i*21}" font-size="12" fill="#243d30">{esc(c["name"])}</text><text x="255" y="{61+i*21}" text-anchor="end" font-size="10" fill="#8b978e">{esc(c["type"])}</text>')
    svg.append('</g>')
svg.append('<text x="30" y="925" font-size="12" fill="#4c6b3d">PK: clave primaria · FK: clave foránea · flecha: hijo → padre · todas las FK son obligatorias.</text><text x="30" y="949" font-size="12" fill="#4c6b3d">Calificación: máximo 2 autores participantes por viaje, validado mediante trigger y UNIQUE(viaje, autor).</text><text x="30" y="973" font-size="12" fill="#4c6b3d">Oferta: máximo un viaje por solicitud, protegido por estado, trigger y transacción.</text></g></svg>')
(root/'docs/MER.svg').write_text(''.join(svg))
print('Generados docs/DICCIONARIO.md y docs/MER.svg con metadatos reales.')
