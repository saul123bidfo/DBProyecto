#!/usr/bin/env python3
"""Conserva el paquete DOCX original y modifica solo bloques técnicos identificados."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import re
import xml.etree.ElementTree as E
root=Path(__file__).resolve().parents[1]
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
ns={'w':W}
E.register_namespace('w',W)
def text(n):return ''.join(t.text or '' for t in n.findall('.//w:t',ns))
def paragraph(content,style=None):
    p=E.Element('{'+W+'}p')
    if style:
        props=E.SubElement(p,'{'+W+'}pPr');E.SubElement(props,'{'+W+'}pStyle',{'{'+W+'}val':style})
    r=E.SubElement(p,'{'+W+'}r');t=E.SubElement(r,'{'+W+'}t');t.text=content
    return p
with ZipFile(root/'Informe_inDrive.docx') as source:
    original_xml=source.read('word/document.xml')
    declarations=re.findall(r'xmlns:([\w]+)="([^"]+)"',original_xml.decode())
    for prefix,uri in declarations:E.register_namespace(prefix,uri)
    doc=E.fromstring(original_xml);body=doc.find('w:body',ns)
    nodes=list(body)
    # Reordena los bloques del cuerpo; no altera el índice ni la historia.
    start23=next(i for i,n in enumerate(nodes) if text(n)=='2.3 Modelo de negocio')
    start22=next(i for i,n in enumerate(nodes) if text(n)=='2.2 Origen e historia')
    end22=next(i for i,n in enumerate(nodes) if text(n)=='3. Misión, visión y valores')
    reordered=nodes[:start23]+nodes[start22:end22]+nodes[start23:start22]+nodes[end22:]
    for n in list(body):body.remove(n)
    for n in reordered:body.append(n)
    table=next(t for t in body.findall('w:tbl',ns) if text(t).startswith('EntidadAtributos de ejemplo'))
    rows=table.findall('w:tr',ns)
    revised=[
      ['Entidad','Atributos del modelo implementado','Relaciones principales'],
      ['Usuario','id_usuario (PK), nombres, telefono (UQ), correo (UQ), fecha_registro','Puede ser pasajero y/o tener un perfil Conductor (0..1).'],
      ['Conductor','id_conductor (PK), id_usuario (FK, UQ), licencia (UQ)','Pertenece a un Usuario; posee 0..N vehículos. Calificación promedio calculada.'],
      ['Vehículo','placa (PK), id_conductor (FK), marca, modelo, color, anio','Pertenece a un conductor; participa en 0..N ofertas.'],
      ['Solicitud de viaje','id_solicitud (PK), id_usuario (FK), origen, destino, precio_ofrecido, estado, fecha_solicitud','La crea un pasajero; recibe 0..N ofertas.'],
      ['Oferta','id_oferta (PK), id_solicitud (FK), placa (FK), monto, tiempo_llegada; UQ(id_solicitud, placa)','Vincula solicitud y vehículo. El conductor se deriva del vehículo. Aceptación mediante Viaje.'],
      ['Viaje','id_viaje (PK), id_oferta (FK, UQ), estado, hora_inicio, hora_fin','Surge de una oferta seleccionada. El monto_final se obtiene de Oferta.monto.'],
      ['Pago','id_pago (PK), id_viaje (FK, UQ), metodo, monto, comision, fecha_pago','Como máximo un cobro por viaje finalizado; importe igual al acordado.'],
      ['Calificación','id_calificacion (PK), id_viaje (FK), id_usuario (FK), puntaje, comentario; UQ(id_viaje, id_usuario)','Evaluación del otro participante por viaje finalizado y autor; puntaje 1..5.']]
    assert len(rows)==len(revised),(len(rows),len(revised))
    for row,contents in zip(rows,revised):
        cells=row.findall('w:tc',ns)
        for cell,content in zip(cells,contents):
            for child in list(cell):
                if child.tag!='{'+W+'}tcPr':cell.remove(child)
            cell.append(paragraph(content))
    idx=list(body).index(table)+1
    corrections=[
      'Precisiones técnicas de implementación: este modelo sigue siendo un ejercicio académico propio y no describe la base de datos interna de inDrive. El informe inicial no especificaba motor ni consultas SQL. Se seleccionó MySQL 8.0.16 o superior con InnoDB; se verificó el esquema mediante MariaDB 11.8.6 en modo bootstrap. La ejecución HTTP completa y la verificación directa en MySQL quedan pendientes en un entorno que permita conexiones y la instalación de dependencias.',
      'La normalización evita almacenar el conductor dos veces en Oferta, duplicar el precio de la oferta en Viaje o mantener manualmente el promedio de calificación. Se añaden únicamente las claves necesarias para materializar las relaciones del modelo inicial. Los importes se expresan en soles (PEN).',
      'Reglas adoptadas para hacer ejecutable el ejemplo: una solicitud nace abierta y puede cancelarse antes de aceptar una oferta. La aceptación crea un viaje pendiente y cierra la solicitud en una transacción; luego el viaje pasa a en_curso y finalizado. Las claves foráneas usan RESTRICT para conservar información relacionada. Solo los participantes pueden evaluar un viaje finalizado; los pagos y evaluaciones no se eliminan desde la aplicación.',
      'Los scripts ejecutables, el análisis de 1FN–3FN, las reglas completas y el registro de correcciones se entregan con el proyecto en database/ y docs/. El Explorador de Base de Datos consulta INFORMATION_SCHEMA para presentar el diccionario, PK, FK, CHECK, índices, triggers y el diagrama de las relaciones realmente implementadas. Las seis consultas académicas agregadas se encuentran en database/03-consultas.sql; no pertenecían al documento inicial.'
    ]
    for content in corrections:body.insert(idx,paragraph(content));idx+=1
    # No se añaden bloques de código al cuerpo empresarial: anexos separados y trazables.
    output=root/'docs/Informe_inDrive_corregido.docx'
    corrected=E.tostring(doc,encoding='utf-8',xml_declaration=True).decode()
    missing=' '.join(f'xmlns:{prefix}="{uri}"' for prefix,uri in declarations if f'xmlns:{prefix}=' not in corrected)
    corrected=corrected.replace('<w:document ',f'<w:document {missing} ',1)
    E.fromstring(corrected)
    with ZipFile(output,'w',ZIP_DEFLATED) as dest:
        for item in source.infolist():dest.writestr(item,corrected.encode() if item.filename=='word/document.xml' else source.read(item.filename))
print(output)
