#!/usr/bin/env python3
"""Prueba real del motor en bootstrap, sin sockets. Instancia temporal independiente."""
from pathlib import Path
import tempfile, subprocess, sys, shutil, json
root=Path(__file__).resolve().parents[1]
server=shutil.which('mariadbd') or '/usr/sbin/mariadbd'
with tempfile.TemporaryDirectory(prefix='indrive-sql-') as folder:
    base=Path(folder);data=base/'data';log=base/'server.log'
    r=subprocess.run(['mariadb-install-db',f'--datadir={data}','--auth-root-authentication-method=normal','--skip-test-db'],capture_output=True,text=True)
    if r.returncode:sys.exit(r.stderr+r.stdout)
    def run(sql):
        log.unlink(missing_ok=True)
        r=subprocess.run([server,'--no-defaults','--bootstrap',f'--datadir={data}',f'--log-error={log}'],input=sql,capture_output=True,text=True)
        errors=log.read_text() if log.exists() else ''
        if r.returncode or '[ERROR]' in errors:sys.exit(r.stdout+r.stderr+errors)
    run((root/'database/01-schema.sql').read_text())
    run((root/'database/02-seed.sql').read_text())
    suite=(root/'tests/integrity.sql').read_text()
    run(suite+f"\nSELECT 'INTEGRIDAD_OK' INTO OUTFILE '{base}/result.txt';\n")
    assert (base/'result.txt').read_text().strip()=='INTEGRIDAD_OK'
    catalog=(root/'database/03-consultas.sql').read_text()
    run(catalog)
    # Prueba de resultados concretos (JOIN, GROUP BY y subconsulta).
    run(f"""USE indrive_academico;
    SELECT JSON_OBJECT('usuarios',(SELECT COUNT(*) FROM usuario),'tablas',(SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='indrive_academico' AND TABLE_TYPE='BASE TABLE'),'viajes',(SELECT COUNT(*) FROM viaje),'cobrado',(SELECT SUM(monto) FROM pago),'ofertas_bajo_promedio',(SELECT COUNT(*) FROM oferta o WHERE o.monto<(SELECT AVG(x.monto) FROM oferta x WHERE x.id_solicitud=o.id_solicitud)),'sin_ofertas',(SELECT COUNT(*) FROM solicitud s LEFT JOIN oferta o ON o.id_solicitud=s.id_solicitud WHERE o.id_oferta IS NULL),'promedio_conductor',(SELECT AVG(c.puntaje) FROM calificacion c JOIN viaje v ON v.id_viaje=c.id_viaje JOIN oferta o ON o.id_oferta=v.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud WHERE c.id_usuario=s.id_usuario)) INTO OUTFILE '{base}/summary.json';
    """)
    summary=json.loads((base/'summary.json').read_text())
    assert summary=={'usuarios':5,'tablas':8,'viajes':1,'cobrado':20.0,'ofertas_bajo_promedio':1,'sin_ofertas':1,'promedio_conductor':5.0},summary
    run(f"""USE indrive_academico;
    SELECT JSON_OBJECT('tables',(SELECT JSON_ARRAYAGG(JSON_OBJECT('name',TABLE_NAME,'description',TABLE_COMMENT,'engine',ENGINE)) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE'),'columns',(SELECT JSON_ARRAYAGG(JSON_OBJECT('table_name',TABLE_NAME,'name',COLUMN_NAME,'type',COLUMN_TYPE,'nullable',IS_NULLABLE,'default_value',COLUMN_DEFAULT,'column_key',COLUMN_KEY,'extra',EXTRA,'description',COLUMN_COMMENT)) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE()),'keys',(SELECT JSON_ARRAYAGG(JSON_OBJECT('table_name',TABLE_NAME,'name',CONSTRAINT_NAME,'column_name',COLUMN_NAME,'referenced_table',REFERENCED_TABLE_NAME,'referenced_column',REFERENCED_COLUMN_NAME)) FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE())) INTO OUTFILE '{base}/schema.json' FIELDS TERMINATED BY '' ESCAPED BY '' LINES TERMINATED BY '';
    """)
    metadata=json.loads((base/'schema.json').read_text())
    assert len(metadata['tables'])==8
    assert len([k for k in metadata['keys'] if k['referenced_table']])==9
    (root/'docs/DICCIONARIO.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    report={'engine':subprocess.run([server,'--version'],capture_output=True,text=True).stdout.strip(),'mode':'bootstrap (motor real, sin sockets)','integrity':'PASS','academic_queries':'PASS','summary':summary}
    (root/'docs/VALIDACION-SQL.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
