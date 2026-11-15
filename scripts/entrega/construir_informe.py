#!/usr/bin/env python3
"""Construye docs/entrega/Informe_inDrive_BD_final.docx a partir de docs/Informe_inDrive_corregido.docx.

Conserva la portada, los cuatro integrantes, el docente y la investigación de las secciones 1 a 6, FODA y
referencias; corrige jerarquía de títulos, índice, numeración y encabezados de tablas; y añade la
problemática, los objetivos, la propuesta y el desarrollo de base de datos.
Solo biblioteca estándar. Para paginar el índice usa LibreOffice (soffice) y pdftotext si existen.

Uso: python3 scripts/entrega/construir_informe.py
"""
import os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_lib import *  # noqa: E402,F401,F403

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/Informe_inDrive_corregido.docx"
SALIDA = ROOT / "docs/entrega/Informe_inDrive_BD_final.docx"
DIAG = ROOT / "docs/entrega/diagramas"
ASSETS = ROOT / "docs/entrega/assets"
REPO = "https://github.com/saul123bidfo/DBProyecto"

PAGES = {}          # marcador -> número de página (se rellena en la segunda pasada)
EMU = 914400


# ----------------------------------------------------------------------------- datos reales del repositorio
def leer(ruta):
    return (ROOT / ruta).read_text(encoding="utf8")


def consultas_sql():
    """(título, sentencia) de database/03-consultas.sql, en orden."""
    res, titulo = [], None
    for linea in leer("database/03-consultas.sql").splitlines():
        if linea.startswith("-- "):
            titulo = linea[3:].split(":")[0]
        elif linea.startswith("SELECT") and titulo:
            res.append((titulo, linea.strip()))
            titulo = None
    return res


def formatear_sql(sql, ancho=98):
    sql = re.sub(r"\s+(FROM|LEFT JOIN|JOIN|WHERE|GROUP BY|HAVING|ORDER BY|LIMIT)\s", lambda m: "\n" + m.group(1) + " ", sql)
    sql = re.sub(r"\s+(AND)\s", r" \1 ", sql)
    out = []
    for l in sql.split("\n"):
        out.extend(envolver(l, ancho))
    return out


def envolver(l, ancho, sangria="    "):
    if len(l) <= ancho:
        return [l]
    res = []
    palabras = l.split(" ")
    cur = palabras[0]
    for p in palabras[1:]:
        if len(cur) + 1 + len(p) > ancho:
            res.append(cur)
            cur = sangria + p
        else:
            cur += " " + p
    res.append(cur)
    return res


def extraer(patron):
    m = re.search(patron, leer("database/01-schema.sql"), re.S)
    assert m, patron
    return m.group(0)


# ----------------------------------------------------------------------------- estado de construcción
class Estado:
    def __init__(self):
        self.cuerpo = []          # fragmentos XML (cadenas) o elementos ET
        self.cab = []             # (nivel, texto, marcador)
        self.figs = []            # (n, texto, marcador)
        self.tabs = []
        self.bm = 100
        self.nfig = 0
        self.ntab = 0
        self.rels = []            # (rid, destino, archivo_origen)
        self.imgs = 0
        self.etq = {}

    def marcador(self, prefijo="_Toc"):
        self.bm += 1
        return self.bm, f"{prefijo}{self.bm:06d}"

    def add(self, xml):
        self.cuerpo.append(xml)

    def titulo(self, nivel, t, salto=False):
        i, nombre = self.marcador()
        self.cab.append((nivel, t, nombre))
        self.add(para(f'<w:bookmarkStart w:id="{i}" w:name="{nombre}"/>{run(t)}<w:bookmarkEnd w:id="{i}"/>',
                      style="Ttulo1" if nivel == 1 else "Ttulo2", page_break=salto))

    def leyenda_tabla(self, t, clave=None):
        self.ntab += 1
        if clave:
            self.etq[clave] = f"Tabla {self.ntab}"
        i, nombre = self.marcador()
        self.tabs.append((self.ntab, t, nombre))
        self.add(para(f'<w:bookmarkStart w:id="{i}" w:name="{nombre}"/>{run("Tabla ")}{campo("SEQ Tabla \\* ARABIC", self.ntab)}'
                      f'{run(". " + t)}<w:bookmarkEnd w:id="{i}"/>', style="Leyenda", keep_next=True))

    def figura(self, archivo, t, ancho_emu, ancho_px, alto_px, descr, clave=None):
        self.nfig += 1
        if clave:
            self.etq[clave] = f"Figura {self.nfig}"
        self.imgs += 1
        rid = f"rIdFig{self.imgs}"
        self.rels.append((rid, f"media/{archivo.name}", archivo))
        cy = int(ancho_emu * alto_px / ancho_px)
        self.add(para(imagen(rid, ancho_emu, cy, 200 + self.imgs, archivo.stem, descr), jc="center", keep_next=True, before=120, after=60))
        i, nombre = self.marcador()
        self.figs.append((self.nfig, t, nombre))
        self.add(para(f'<w:bookmarkStart w:id="{i}" w:name="{nombre}"/>{run("Figura ")}{campo("SEQ Figura \\* ARABIC", self.nfig)}'
                      f'{run(". " + t)}<w:bookmarkEnd w:id="{i}"/>', style="Leyenda", jc="center"))

    def figura_existente(self, nodo_parrafo, t):
        """Añade una leyenda numerada tras una figura de los compañeros (organigrama)."""
        self.nfig += 1
        i, nombre = self.marcador()
        self.figs.append((self.nfig, t, nombre))
        self.add(nodo_parrafo)
        self.add(para(f'<w:bookmarkStart w:id="{i}" w:name="{nombre}"/>{run("Figura ")}{campo("SEQ Figura \\* ARABIC", self.nfig)}'
                      f'{run(". " + t)}<w:bookmarkEnd w:id="{i}"/>', style="Leyenda", jc="center"))


def px(nombre):
    cab = (DIAG / f"{nombre}.svg").read_text(encoding="utf8")
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', cab)
    return int(m.group(1)), int(m.group(2))


# ----------------------------------------------------------------------------- contenido nuevo
def intro_extra(s):
    s.add(texto("Además de la investigación sobre la empresa, el informe incorpora el desarrollo de una base de datos relacional "
                "para el flujo de negociación de un viaje, elaborado en el curso de Base de Datos. Ese desarrollo se presenta en "
                "las secciones 8 a 10 e incluye el modelo entidad-relación (ER) y su extensión (EER), el modelo lógico, el "
                "diccionario de datos, la normalización, el álgebra relacional, el código SQL, las transacciones y las pruebas, "
                "junto con un prototipo web académico. El código y las evidencias están en el repositorio del proyecto "
                f"({REPO}). Se trata de un modelo ilustrativo propio: no describe la base de datos interna de inDrive."))


def seccion_8(s):
    s.titulo(1, "8. Problemática y objetivos", salto=True)
    s.titulo(2, "8.1 Problemática")
    s.add(texto("El modelo de precios negociados descrito en la sección 2.3 convierte cada viaje en una pequeña negociación: el "
                "pasajero publica una solicitud con el precio que está dispuesto a pagar, varios conductores responden con sus "
                "ofertas y el pasajero elige una. Para que ese proceso sea confiable, lo que ocurre en cada paso debe quedar "
                "registrado de forma consistente y poder consultarse después: qué oferta originó un viaje, cuánto se acordó, "
                "cuánto se cobró y quién calificó a quién."))
    s.add(texto("Si esa información se gestionara sin un modelo relacional bien definido, por ejemplo en hojas de cálculo o en "
                "archivos independientes, aparecerían problemas previsibles. La [[T:riesgos]] resume los riesgos que se identificaron "
                "a partir del propio flujo de negociación y el mecanismo del diseño que los previene."))
    s.leyenda_tabla("Riesgos del flujo de negociación y mecanismos de prevención", "riesgos")
    s.add(tabla(["Riesgo identificado", "Consecuencia en el flujo", "Mecanismo en la solución"], [
        ["Personas, conductores o vehículos duplicados", "Identidad ambigua del pasajero o del conductor",
         "UNIQUE en teléfono, correo, licencia y placa"],
        ["Registros huérfanos (oferta sin solicitud, viaje sin oferta)", "Datos que ya no se pueden interpretar",
         "Nueve claves foráneas obligatorias con RESTRICT"],
        ["Aceptar dos ofertas de una misma solicitud", "Dos viajes para un solo pedido",
         "Bloqueo de la solicitud dentro de una transacción, UNIQUE(id_oferta) y triggers"],
        ["Importes incoherentes (montos negativos, cobro distinto al pactado)", "Cobros que no se pueden conciliar",
         "CHECK de montos y trigger que exige el precio acordado"],
        ["Pérdida del historial (borrar viajes, pagos o calificaciones)", "Sin trazabilidad de lo ocurrido",
         "FK RESTRICT y triggers de conservación"],
        ["Calificaciones de terceros o repetidas", "Reputación poco confiable",
         "UNIQUE(id_viaje, id_usuario) y trigger de participantes"],
        ["Datos redundantes (promedio almacenado, conductor repetido en la oferta)", "Actualizaciones inconsistentes",
         "Normalización hasta 3FN y promedio calculado con AVG"],
    ], [2900, 2700, 3426], sz=17))
    s.add(texto("Estos riesgos no se presentan como estadísticas de inDrive: son situaciones que el diseño busca evitar y que se "
                "pueden comprobar con las pruebas de la sección 10.10. El informe no dispone de mediciones sobre la base de datos "
                "real de la empresa, por lo que no se formulan cifras sobre su frecuencia.", before=140))

    s.titulo(2, "8.2 Objetivo general")
    s.add(texto("Diseñar, implementar y validar una base de datos relacional en MySQL que soporte el flujo de negociación de viajes "
                "(solicitud, ofertas, viaje, pago y calificación) de manera consistente, íntegra y verificable, y demostrarla "
                "mediante un prototipo web académico."))
    s.titulo(2, "8.3 Objetivos específicos")
    for t in ["Delimitar el alcance y los requisitos del flujo de negociación a partir de la sección 7 del informe.",
              "Elaborar los modelos ER y EER con sus cardinalidades y la especialización parcial de Conductor.",
              "Derivar el modelo lógico, identificar claves y dependencias funcionales y justificar la normalización hasta 3FN.",
              "Implementar el esquema físico en SQL con restricciones declarativas (PK, FK, UNIQUE, CHECK) y triggers.",
              "Formular consultas SQL y expresiones de álgebra relacional que respondan preguntas del negocio.",
              "Garantizar la consistencia de las operaciones críticas mediante transacciones y bloqueos.",
              "Comprobar el diseño con pruebas automatizadas y evidencia verificable en el repositorio."]:
        s.add(viñeta(t, num=3))
    s.titulo(2, "8.4 Alcance y limitaciones")
    s.add(texto("**Alcance.** El proyecto cubre el flujo urbano de viaje con precio negociado: solicitud, ofertas, aceptación, viaje, "
                "pago y calificación, con ocho entidades y datos ficticios de demostración. La aplicación es local y académica."))
    s.add(texto("**Fuera del alcance.** No se modelan contraofertas sucesivas, cancelación de viajes ya aceptados, reembolsos, pagos en "
                "cuotas, mapas, geolocalización, pasarelas de pago ni autenticación, porque el informe no los especifica como datos. "
                "El pago es un registro académico y no realiza cargos reales. La comisión se guarda como un importe: no se adopta el "
                "9,5 % citado en la sección 2.3 como regla del sistema, ya que proviene de una entrevista y no de una tarifa contractual."))
    s.add(texto("**Limitaciones de la evidencia.** El recorrido manual en navegador y las capturas de la interfaz no se realizaron; "
                "la suite SQL de integridad se ejecutó en MariaDB 11.8.6 y la integración continua verifica el flujo completo en "
                "MySQL 8.0.44 (sección 10.10)."))


def seccion_9(s):
    s.titulo(1, "9. Propuesta de solución", salto=True)
    s.titulo(2, "9.1 Descripción de la solución")
    s.add(texto("La propuesta es **inDrive Lab**, una aplicación web académica construida sobre una base de datos MySQL 8.0 con InnoDB. "
                "Su objetivo no es reemplazar el sistema de la empresa, sino demostrar cómo un modelo relacional bien diseñado sostiene "
                "el flujo de negociación. La aplicación permite registrar personas, conductores y vehículos; crear solicitudes con un "
                "precio propuesto; registrar ofertas; aceptar una oferta, lo que genera el viaje; iniciar y finalizar viajes; registrar "
                "el cobro y las calificaciones; y cancelar solicitudes abiertas."))
    s.add(texto("Además incluye dos módulos de apoyo académico: un **Explorador de Base de Datos**, que lee tablas, columnas, claves, "
                "restricciones CHECK, índices, triggers y reglas referenciales directamente de INFORMATION_SCHEMA y dibuja el diagrama "
                "de relaciones, y un catálogo de **seis consultas SQL** de solo lectura, con parámetros validados y un máximo de 200 filas. "
                "Los usuarios de la aplicación no disponen de una consola SQL libre."))
    s.titulo(2, "9.2 Flujo de negociación")
    s.add(texto("La [[F:flujo]] resume el proceso. La solicitud nace en estado «abierta» y puede cancelarse mientras siga abierta. Cuando el "
                "pasajero acepta una oferta, una sola transacción crea el viaje en estado «pendiente» y cierra la solicitud como "
                "«aceptada»; las demás ofertas quedan cerradas. El viaje pasa luego a «en_curso» y «finalizado», y solo entonces se "
                "puede registrar el pago y las calificaciones de los participantes."))
    w, h = px("flujo")
    s.figura(DIAG / "flujo.png", "Flujo de negociación implementado en la base de datos", 5600000, w, h,
             "Seis pasos: solicitud, ofertas, aceptación, viaje en curso, viaje finalizado y cierre con pago y calificaciones", "flujo")
    s.add(texto("Los estados son una decisión de diseño adoptada para hacer ejecutable el ejemplo (solicitud: abierta, aceptada, cancelada; "
                "viaje: pendiente, en_curso, finalizado). No corresponden a políticas oficiales de inDrive.", before=60))
    s.titulo(2, "9.3 Arquitectura")
    s.add(texto("La arquitectura es cliente-servidor en tres capas ([[F:arq]]). El navegador ejecuta una interfaz React que consume una API "
                "JSON; el servidor Express valida las entradas y es el único que ejecuta SQL contra MySQL mediante un pool de "
                "conexiones. La aplicación se levanta con Docker Compose (servicios db, setup y app) y el repositorio incluye un "
                "flujo de GitHub Actions que prueba el proyecto contra MySQL 8.0.44."))
    w, h = px("arquitectura")
    s.figura(DIAG / "arquitectura.png", "Arquitectura de tres capas, entorno de ejecución y verificación automática", 5600000, w, h,
             "Navegador React, servidor Express y MySQL 8.0.44, con Docker Compose y GitHub Actions", "arq")
    s.leyenda_tabla("Tecnologías y versiones declaradas en el proyecto", "tec")
    s.add(tabla(["Componente", "Versión", "Uso"], [
        ["MySQL con InnoDB", "8.0.44 (imagen Docker); esquema compatible con 8.0.16 o superior", "Motor relacional, restricciones y triggers"],
        ["Node.js", "20.19 o superior (.nvmrc)", "Ejecución del servidor"],
        ["Express", "4.22.3", "API REST en JSON"],
        ["mysql2", "3.15.3", "Conexión y transacciones desde el servidor"],
        ["React y Vite", "18.3.1 y 6.4.4", "Interfaz y compilación"],
        ["Docker Compose", "Servicios db, setup y app", "Arranque local reproducible"],
    ], [2300, 3300, 3426], sz=17))
    s.titulo(2, "9.4 Requisitos funcionales")
    s.add(texto("La [[T:rf]] relaciona cada requisito con su origen en el informe y con la parte de la API que lo implementa.", before=120))
    s.leyenda_tabla("Requisitos funcionales y su trazabilidad", "rf")
    s.add(tabla(["Código", "Requisito", "Origen en el informe", "Implementación"], [
        ["RF-01", "Registrar, consultar, buscar y editar usuarios", "Tabla de la sección 7: Usuario", "/api/data/usuario"],
        ["RF-02", "Gestionar conductores y vehículos con licencia y placa únicas", "Sección 7: Conductor y Vehículo", "/api/data/conductor y /api/data/vehiculo"],
        ["RF-03", "Crear solicitudes con precio propuesto y cancelarlas mientras estén abiertas", "Secciones 2.3 y 7", "/api/data/solicitud y /api/requests/:id/cancel"],
        ["RF-04", "Registrar ofertas de un vehículo con monto y tiempo de llegada", "Sección 2.3", "/api/data/oferta"],
        ["RF-05", "Aceptar una oferta y crear el viaje en una sola transacción", "Sección 2.3", "/api/offers/:id/accept"],
        ["RF-06", "Iniciar y finalizar viajes registrando las fechas", "Sección 7: Viaje", "/api/trips/:id/start y /finish"],
        ["RF-07", "Registrar el cobro de un viaje finalizado por el importe pactado", "Sección 7: Pago", "/api/data/pago"],
        ["RF-08", "Registrar la calificación de cada participante", "Sección 7: Calificación", "/api/data/calificacion"],
        ["RF-09", "Explorar la estructura real de la base de datos", "Requerimiento del curso", "/api/explorer"],
        ["RF-10", "Ejecutar consultas académicas de un catálogo cerrado", "Requerimiento del curso", "/api/queries"],
    ], [800, 3300, 2200, 2726], sz=16, mono_cols=(3,)))
    s.titulo(2, "9.5 Reglas de negocio adoptadas")
    s.add(texto("El informe original describe el flujo, pero no define reglas de datos. Para que el ejemplo sea ejecutable se adoptaron las "
                "siguientes decisiones, que son supuestos del proyecto y no políticas de inDrive:", before=60))
    for t in ["Un usuario puede ser pasajero y, opcionalmente, tener un perfil de conductor; no se duplica una entidad Pasajero.",
              "Cada vehículo pertenece a un conductor. La oferta referencia un vehículo y de él se deriva el conductor.",
              "Existe como máximo una oferta por vehículo y solicitud, y un conductor no puede ofertar en su propia solicitud.",
              "Aceptar una oferta equivale a que exista un viaje con ese id_oferta; por eso no se guarda un estado «aceptada» en Oferta.",
              "El monto final del viaje es el de la oferta elegida y no se vuelve a guardar en Viaje.",
              "Se registra un pago por viaje finalizado, con importe igual al pactado y comisión entre 0 y el importe.",
              "Solo los participantes de un viaje finalizado pueden calificar, una vez cada uno, con un puntaje entero de 1 a 5.",
              "Viajes, pagos y calificaciones no se eliminan; las claves foráneas usan RESTRICT."]:
        s.add(viñeta(t))


def paginas_er(s):
    """ER: texto en vertical y figura en página horizontal."""
    s.titulo(1, "10. Desarrollo de la base de datos", salto=True)
    s.add(texto("Este capítulo documenta el modelo y la implementación. La fuente de verdad es el script `database/01-schema.sql`; los "
                "diagramas, las tablas y las cifras se contrastaron con ese archivo, con el seed, con el código del servidor y con las "
                "pruebas del repositorio."))
    s.titulo(2, "10.1 Modelo entidad-relación (ER)")
    s.add(texto("El modelo conceptual tiene ocho entidades: **Usuario, Conductor, Vehículo, Solicitud, Oferta, Viaje, Pago y Calificación**. "
                "La [[F:er]], en la página siguiente, muestra sus atributos, claves y cardinalidades. Se lee así: un usuario puede tener "
                "un perfil de conductor; un conductor posee vehículos; un usuario crea solicitudes; cada solicitud recibe ofertas de "
                "vehículos; una oferta puede originar un viaje, y el viaje tiene un pago y hasta dos calificaciones emitidas por sus "
                "participantes."))
    s.leyenda_tabla("Relaciones, cardinalidades y su implementación", "card")
    s.add(tabla(["Relación", "Cardinalidad", "Cómo se garantiza"], [
        ["Usuario – Conductor", "1 : 0..1", "id_usuario en Conductor es FK, UNIQUE y NOT NULL"],
        ["Conductor – Vehículo", "1 : 0..N", "FK id_conductor en Vehículo"],
        ["Usuario – Solicitud", "1 : 0..N", "FK id_usuario en Solicitud (el pasajero)"],
        ["Solicitud – Oferta", "1 : 0..N", "FK id_solicitud en Oferta"],
        ["Vehículo – Oferta", "1 : 0..N", "FK placa en Oferta; UNIQUE(id_solicitud, placa)"],
        ["Oferta – Viaje", "1 : 0..1", "UNIQUE(id_oferta) más bloqueo de la solicitud y trigger: una solicitud solo acepta una oferta"],
        ["Viaje – Pago", "1 : 0..1", "UNIQUE(id_viaje) en Pago"],
        ["Viaje – Calificación", "1 : 0..2", "La FK sola expresa 0..N; UNIQUE(id_viaje, id_usuario) y el trigger de participantes limitan a dos"],
        ["Usuario – Calificación", "1 : 0..N", "FK id_usuario en Calificación (el autor)"],
    ], [2300, 1300, 5426], sz=17))
    s.add(texto("Las dos restricciones UNIQUE compuestas valen **en conjunto**: ni la solicitud ni la placa son únicas por separado en "
                "Oferta, y ni el viaje ni el autor lo son por separado en Calificación. Las nueve claves foráneas son obligatorias; los "
                "hijos pueden no existir (por eso las cardinalidades mínimas son 0), pero cada hijo siempre tiene su padre.", before=140))
    # --- página horizontal con la figura
    s.add(para("", sect=sect(False, start=1)))
    w, h = px("er")
    s.figura(DIAG / "er.png", "Modelo entidad-relación de inDrive Lab (ocho entidades y nueve relaciones)", 8300000, w, h,
             "Diagrama ER con Usuario, Conductor, Vehículo, Solicitud, Oferta, Viaje, Pago y Calificación", "er")
    s.add(para("", sect=sect(True)))


def seccion_10_resto(s):
    # ------------------------------------------------------------------ 10.2 EER
    s.titulo(2, "10.2 Modelo entidad-relación extendido (EER)")
    s.add(texto("La extensión relevante es la **especialización parcial** de Usuario: algunos usuarios además son conductores, y para ellos se "
                "guarda la licencia. Como solo se representa un subtipo, no corresponde declarar disyunción ni inventar una "
                "especialización total. Pasajero no es un subtipo: es un rol que adquiere cualquier usuario al crear una solicitud, y un "
                "conductor también puede pedir un viaje."))
    w, h = px("eer")
    s.figura(DIAG / "eer.png", "Especialización parcial de Usuario en Conductor y rol de pasajero", 5600000, w, h,
             "Usuario con subtipo parcial Conductor; el rol de pasajero surge de la FK de Solicitud", "eer")
    s.add(texto("La implementación no crea una tabla adicional para el rol. Conductor conserva `id_conductor` como clave primaria y usa "
                "`id_usuario` como clave foránea única y no nula: cada conductor corresponde a exactamente un usuario, un usuario tiene "
                "como máximo un perfil y pueden existir usuarios sin perfil de conductor.", before=140))

    # ------------------------------------------------------------------ 10.3 lógico
    s.titulo(2, "10.3 Modelo lógico relacional")
    s.add(texto("A partir del modelo ER se obtuvieron ocho relaciones. La [[T:esquema]] muestra su esquema (clave primaria en negrita) y sus claves "
                "candidatas. La [[F:logico]], en la página siguiente, presenta el mismo modelo con tipos de datos y claves foráneas."))
    s.leyenda_tabla("Esquema relacional y claves candidatas", "esquema")
    s.add(tabla(["Relación", "Atributos (PK en negrita; FK en cursiva)", "Claves candidatas"], [
        ["USUARIO", "**id_usuario**, nombres, telefono, correo, fecha_registro", "id_usuario; telefono; correo"],
        ["CONDUCTOR", "**id_conductor**, __id_usuario__, licencia", "id_conductor; id_usuario; licencia"],
        ["VEHICULO", "**placa**, __id_conductor__, marca, modelo, color, anio", "placa"],
        ["SOLICITUD", "**id_solicitud**, __id_usuario__, origen, destino, precio_ofrecido, estado, fecha_solicitud", "id_solicitud"],
        ["OFERTA", "**id_oferta**, __id_solicitud__, __placa__, monto, tiempo_llegada", "id_oferta; (id_solicitud, placa)"],
        ["VIAJE", "**id_viaje**, __id_oferta__, estado, hora_inicio, hora_fin", "id_viaje; id_oferta"],
        ["PAGO", "**id_pago**, __id_viaje__, metodo, monto, comision, fecha_pago", "id_pago; id_viaje"],
        ["CALIFICACION", "**id_calificacion**, __id_viaje__, __id_usuario__, puntaje, comentario", "id_calificacion; (id_viaje, id_usuario)"],
    ], [1500, 4900, 2626], sz=17, bold_first=True))
    s.add(texto("Todas las claves foráneas aplican `ON DELETE RESTRICT` y `ON UPDATE RESTRICT`. Solo `hora_inicio` y `hora_fin` admiten "
                "valores nulos, porque un viaje pendiente todavía no tiene fechas. Las claves primarias son artificiales, salvo la placa "
                "del vehículo, que es un identificador natural.", before=140))
    s.add(para("", sect=sect(False)))
    w, h = px("logico")
    s.figura(DIAG / "logico.png", "Modelo lógico con tipos de datos y claves foráneas", 8300000, w, h,
             "Ocho tablas con sus columnas, tipos, claves primarias, foráneas y únicas", "logico")
    s.add(para("", sect=sect(True)))

    # ------------------------------------------------------------------ 10.4 diccionario
    s.titulo(2, "10.4 Diccionario de datos")
    s.add(texto("La [[T:dicc]] resume el diccionario físico. En ejecución, el Explorador de Base de Datos lo obtiene de INFORMATION_SCHEMA; el "
                "anexo del repositorio `docs/DICCIONARIO.md` conserva una instantánea exportada de MariaDB 11.8.6. Los importes se "
                "expresan en soles."))
    s.leyenda_tabla("Diccionario de datos del esquema indrive_academico", "dicc")
    D = [
        ["usuario", "id_usuario", "INT AUTO_INCREMENT", "NO", "PK", "Identificador de persona"],
        ["", "nombres", "VARCHAR(120)", "NO", "CHECK no vacío", "Nombres y apellidos"],
        ["", "telefono", "VARCHAR(20)", "NO", "UNIQUE; CHECK ≥ 7 caracteres", "Teléfono con código de país"],
        ["", "correo", "VARCHAR(160)", "NO", "UNIQUE; CHECK patrón básico", "Correo de contacto"],
        ["", "fecha_registro", "DATETIME", "NO", "DEFAULT CURRENT_TIMESTAMP", "Fecha de alta"],
        ["conductor", "id_conductor", "INT AUTO_INCREMENT", "NO", "PK", "Identificador del perfil"],
        ["", "id_usuario", "INT", "NO", "FK → usuario; UNIQUE", "Perfil opcional de un usuario"],
        ["", "licencia", "VARCHAR(20)", "NO", "UNIQUE; CHECK ≥ 5 caracteres", "Licencia de conducir"],
        ["vehiculo", "placa", "VARCHAR(10)", "NO", "PK; CHECK 5 a 10 caracteres", "Placa única"],
        ["", "id_conductor", "INT", "NO", "FK → conductor", "Propietario del vehículo"],
        ["", "marca, modelo, color", "VARCHAR(50), (60), (30)", "NO", "CHECK no vacíos", "Descriptores del vehículo"],
        ["", "anio", "SMALLINT", "NO", "CHECK 1980 a 2100", "Año de fabricación"],
        ["solicitud", "id_solicitud", "INT AUTO_INCREMENT", "NO", "PK", "Identificador de la solicitud"],
        ["", "id_usuario", "INT", "NO", "FK → usuario", "Pasajero solicitante"],
        ["", "origen, destino", "VARCHAR(200)", "NO", "CHECK no vacíos y distintos", "Ruta solicitada"],
        ["", "precio_ofrecido", "DECIMAL(10,2)", "NO", "CHECK > 0", "Propuesta inicial en soles"],
        ["", "estado", "VARCHAR(12)", "NO", "DEFAULT 'abierta'; CHECK en (abierta, aceptada, cancelada)", "Estado de la solicitud"],
        ["", "fecha_solicitud", "DATETIME", "NO", "DEFAULT CURRENT_TIMESTAMP", "Fecha de creación"],
        ["oferta", "id_oferta", "INT AUTO_INCREMENT", "NO", "PK", "Identificador de la oferta"],
        ["", "id_solicitud", "INT", "NO", "FK → solicitud; UNIQUE(id_solicitud, placa)", "Solicitud ofertada"],
        ["", "placa", "VARCHAR(10)", "NO", "FK → vehiculo; UNIQUE(id_solicitud, placa)", "Vehículo ofertante"],
        ["", "monto", "DECIMAL(10,2)", "NO", "CHECK > 0", "Precio propuesto, en soles"],
        ["", "tiempo_llegada", "SMALLINT", "NO", "CHECK 1 a 240", "Minutos estimados de llegada"],
        ["viaje", "id_viaje", "INT AUTO_INCREMENT", "NO", "PK", "Identificador del viaje"],
        ["", "id_oferta", "INT", "NO", "FK → oferta; UNIQUE", "Oferta aceptada"],
        ["", "estado", "VARCHAR(12)", "NO", "DEFAULT 'pendiente'; CHECK coherente con las fechas", "pendiente, en_curso o finalizado"],
        ["", "hora_inicio, hora_fin", "DATETIME", "SÍ", "CHECK según el estado", "Fechas reales del viaje"],
        ["pago", "id_pago", "INT AUTO_INCREMENT", "NO", "PK", "Identificador del pago"],
        ["", "id_viaje", "INT", "NO", "FK → viaje; UNIQUE", "Un cobro por viaje"],
        ["", "metodo", "VARCHAR(15)", "NO", "CHECK en (efectivo, tarjeta, transferencia)", "Medio de pago"],
        ["", "monto", "DECIMAL(10,2)", "NO", "CHECK > 0; trigger = precio pactado", "Importe cobrado, en soles"],
        ["", "comision", "DECIMAL(10,2)", "NO", "DEFAULT 0; CHECK entre 0 y monto", "Comisión como importe"],
        ["", "fecha_pago", "DATETIME", "NO", "DEFAULT CURRENT_TIMESTAMP", "Fecha del cobro"],
        ["calificacion", "id_calificacion", "INT AUTO_INCREMENT", "NO", "PK", "Identificador de la calificación"],
        ["", "id_viaje", "INT", "NO", "FK → viaje; UNIQUE(id_viaje, id_usuario)", "Viaje calificado"],
        ["", "id_usuario", "INT", "NO", "FK → usuario; UNIQUE(id_viaje, id_usuario)", "Autor; el destinatario es el otro participante"],
        ["", "puntaje", "TINYINT", "NO", "CHECK 1 a 5", "Puntaje entero"],
        ["", "comentario", "VARCHAR(500)", "NO", "DEFAULT ''", "Comentario libre"],
    ]
    s.add(tabla(["Tabla", "Atributo", "Tipo", "Nulo", "Clave o restricción", "Descripción"], D,
                [1150, 1400, 2000, 650, 2100, 1726], sz=15, bold_first=True, zebra=False))

    # ------------------------------------------------------------------ 10.5 normalización
    s.titulo(2, "10.5 Dependencias funcionales y normalización")
    s.add(texto("Cada clave candidata determina todos los atributos de su relación. La [[T:df]] lista los determinantes; las dependencias "
                "se basan en las restricciones y los supuestos del ejercicio, y no se supone, por ejemplo, que el modelo determine la "
                "marca de un vehículo ni que un nombre identifique a una persona."))
    s.leyenda_tabla("Dependencias funcionales por relación", "df")
    s.add(tabla(["Relación", "Determinante(s)", "Atributos determinados"], [
        ["USUARIO", "id_usuario; telefono; correo", "nombres, telefono, correo, fecha_registro"],
        ["CONDUCTOR", "id_conductor; id_usuario; licencia", "los demás atributos de la relación"],
        ["VEHICULO", "placa", "id_conductor, marca, modelo, color, anio"],
        ["SOLICITUD", "id_solicitud", "id_usuario, origen, destino, precio_ofrecido, estado, fecha_solicitud"],
        ["OFERTA", "id_oferta; (id_solicitud, placa)", "monto, tiempo_llegada y los demás atributos"],
        ["VIAJE", "id_viaje; id_oferta", "estado, hora_inicio, hora_fin"],
        ["PAGO", "id_pago; id_viaje", "metodo, monto, comision, fecha_pago"],
        ["CALIFICACION", "id_calificacion; (id_viaje, id_usuario)", "puntaje, comentario"],
    ], [1500, 3200, 4326], sz=17, bold_first=True))
    s.add(texto("**Primera forma normal (1FN).** Todos los campos contienen valores atómicos. Un diseño ingenuo guardaría en una misma celda "
                "la lista de vehículos que ofertaron a una solicitud; aquí cada oferta es una fila de Oferta, y no hay grupos repetidos.", before=140))
    s.add(texto("**Segunda forma normal (2FN).** Las claves primarias son simples, de modo que no hay dependencias parciales sobre ellas. "
                "En las claves candidatas compuestas, (id_solicitud, placa) en Oferta y (id_viaje, id_usuario) en Calificación, se asume que ni "
                "la solicitud ni la placa por sí solas determinan el monto o el tiempo de llegada, y que ni el viaje ni el autor por sí solos "
                "determinan la evaluación."))
    s.add(texto("**Tercera forma normal (3FN).** Con las dependencias declaradas, ningún atributo no clave determina a otro no clave dentro de "
                "una misma relación. El diseño evita varias redundancias: el nombre de la persona vive solo en Usuario; el conductor se obtiene "
                "a través del Vehículo y no se repite en Oferta; el monto pactado vive solo en Oferta y Viaje no lo copia; y el promedio de "
                "calificación de un conductor no se almacena, sino que se calcula con AVG."))
    s.add(texto("**Una redundancia controlada.** Pago guarda un `monto` que debe coincidir con el de la oferta al crearse. Es una redundancia "
                "entre relaciones destinada a registrar lo efectivamente cobrado; como `id_viaje` es clave candidata de Pago, no infringe "
                "la 3FN dentro de la relación, pero exige un control de consistencia, que implementa el trigger `pago_bi`. La conclusión de "
                "3FN depende de los supuestos declarados y no se deduce solo de que las claves primarias sean simples."))

    # ------------------------------------------------------------------ 10.6 álgebra
    s.titulo(2, "10.6 Álgebra relacional")
    s.add(texto("Se usan σ (selección), π (proyección), ⋈ (reunión), ρ (renombrado), − (diferencia) y γ (agrupación y agregación). El álgebra "
                "básica trabaja con conjuntos, de modo que se omiten ORDER BY y LIMIT, que pertenecen a la presentación SQL. En los ejemplos "
                "1 y 2 la clave primaria proyectada evita filas duplicadas."))
    s.add(texto("**Ejemplo 1: solicitudes abiertas sin ofertas** (consulta 4 de la sección 10.8, que usa LEFT JOIN). Su equivalente con diferencia es:", before=60))
    s.add(codigo(["A = π id_solicitud ( σ estado='abierta' (SOLICITUD) )",
                  "B = π id_solicitud ( OFERTA )",
                  "Resultado = π id_solicitud, nombres, origen, destino, precio_ofrecido (",
                  "              ( σ estado='abierta' (SOLICITUD) ⋈ USUARIO ) ⋈ ( A − B ) )"]))
    s.add(texto("Aquí ⋈ sin condición es la reunión natural, que empareja los atributos de igual nombre (id_usuario e id_solicitud). A y B tienen el "
                "mismo esquema, por lo que pueden restarse. El resultado contiene una fila por cada solicitud abierta que no recibió ofertas.", before=100))
    s.add(texto("**Ejemplo 2: viajes y participantes** (consulta 1). Aquí cada ⋈ lleva su condición. Se renombra Usuario dos veces para distinguir al pasajero (P) del conductor (C):"))
    s.add(codigo(["R = VIAJE ⋈ VIAJE.id_oferta = OFERTA.id_oferta OFERTA",
                  "      ⋈ OFERTA.id_solicitud = SOLICITUD.id_solicitud SOLICITUD",
                  "      ⋈ SOLICITUD.id_usuario = P.id_usuario ρ P (USUARIO)",
                  "      ⋈ OFERTA.placa = VEHICULO.placa VEHICULO",
                  "      ⋈ VEHICULO.id_conductor = CONDUCTOR.id_conductor CONDUCTOR",
                  "      ⋈ CONDUCTOR.id_usuario = C.id_usuario ρ C (USUARIO)",
                  "Resultado = π VIAJE.id_viaje, P.nombres, C.nombres, SOLICITUD.origen, SOLICITUD.destino,",
                  "              OFERTA.placa, OFERTA.monto, VIAJE.estado, VIAJE.hora_inicio, VIAJE.hora_fin ( R )"]))
    s.add(texto("El monto final sale de Oferta: no se guarda de nuevo en Viaje.", before=100))
    s.add(texto("**Ejemplo 3: cobros por método** (consulta 5). Requiere el operador de agrupación γ del álgebra extendida:"))
    s.add(codigo(["γ metodo ; COUNT(*) → pagos, SUM(monto) → total_cobrado, SUM(comision) → total_comisiones ( PAGO )"]))

    # ------------------------------------------------------------------ 10.7 SQL
    s.titulo(2, "10.7 Implementación SQL")
    s.add(texto("El script `database/01-schema.sql` crea la base `indrive_academico` con juego de caracteres utf8mb4 y motor InnoDB, ocho "
                "tablas y 18 triggers, sin sentencias DROP. La [[T:integridad]] cuenta los elementos de integridad que el script declara; las "
                "cifras se comprobaron contra el archivo."))
    s.leyenda_tabla("Elementos de integridad declarados en el DDL", "integridad")
    s.add(tabla(["Elemento", "Cantidad", "Detalle"], [
        ["Tablas", "8", "usuario, conductor, vehiculo, solicitud, oferta, viaje, pago, calificacion"],
        ["Claves foráneas", "9", "Todas con ON DELETE RESTRICT y ON UPDATE RESTRICT"],
        ["Restricciones CHECK", "15", "Rangos, formatos, estados, montos y coherencia de fechas"],
        ["Triggers", "18", "Reglas entre tablas e historial inmutable (Anexo B)"],
        ["Índice adicional", "1", "ix_solicitud_estado_fecha (estado, fecha_solicitud)"],
    ], [2300, 1200, 5526], sz=17, jc_cols={1: "center"}))
    s.add(texto("A modo de muestra, estas son la tabla Oferta y los triggers que gobiernan la creación del viaje. Se copian del script con saltos "
                "de línea adicionales para ajustarlos a la página.", before=140))
    oferta = extraer(r"CREATE TABLE oferta \(.*?\) ENGINE=InnoDB COMMENT='[^']*';")
    s.add(codigo([l for x in oferta.split("\n") for l in envolver(x, 98)]))
    trig = extraer(r"CREATE TRIGGER viaje_bi BEFORE INSERT ON viaje.*?END\$\$\nCREATE TRIGGER viaje_ai AFTER INSERT ON viaje.*?END\$\$")
    s.add(para("", after=60))
    s.add(codigo([l for x in trig.replace("END$$\n", "END$$\n\n").split("\n") for l in envolver(x, 98)]))
    s.add(texto("El script `database/02-seed.sql` inserta, dentro de una transacción, datos ficticios de demostración (correos `@example.test`): "
                "5 usuarios, 2 conductores, 3 vehículos, 4 solicitudes, 4 ofertas, 1 viaje finalizado, 1 pago y 2 calificaciones.", before=140))

    # ------------------------------------------------------------------ 10.8 consultas
    s.titulo(2, "10.8 Consultas SQL")
    s.add(texto("El catálogo contiene seis consultas, definidas en `database/03-consultas.sql` y servidas por la API. Cada una se muestra con su "
                "técnica y el resultado que produce con el seed de demostración. Los resultados se derivaron de los datos del seed y "
                "coinciden con los totales verificados en `docs/VALIDACION-SQL.json` (1 oferta bajo el promedio, 1 solicitud sin ofertas, "
                "total cobrado 20,00 y calificación promedio 5,0)."))
    consultas = consultas_sql()
    assert len(consultas) == 6, consultas
    tecnica = ["INNER JOIN y ORDER BY", "GROUP BY, HAVING y AVG (parámetro: mínimo de evaluaciones, por defecto 1)",
               "Subconsulta correlacionada", "LEFT JOIN con IS NULL", "SUM y GROUP BY", "JOIN, WHERE y ORDER BY"]
    resultados = [
        (["id_viaje", "pasajero", "conductor", "origen", "destino", "placa", "monto_final", "estado"],
         [["1", "Ana Torres", "Luis Quispe", "Universidad Norbert Wiener, Lima", "Parque Kennedy, Miraflores", "ABC-123", "20.00", "finalizado"]],
         [700, 950, 1000, 1700, 1600, 850, 1150, 1076]),
        (["id_conductor", "nombres", "evaluaciones", "calificacion_promedio"], [["1", "Luis Quispe", "1", "5.00"]], [1800, 2800, 2000, 2426]),
        (["id_oferta", "id_solicitud", "placa", "monto"], [["2", "1", "BCD-234", "19.00"]], [2000, 2200, 2400, 2426]),
        (["id_solicitud", "nombres", "origen", "destino", "precio_ofrecido"], [["4", "Ana Torres", "Estación Central", "Jesús María", "12.00"]],
         [1400, 1700, 2200, 2000, 1726]),
        (["metodo", "pagos", "total_cobrado", "total_comisiones", "neto_conductores"], [["efectivo", "1", "20.00", "1.90", "18.10"]],
         [1700, 1100, 2000, 2200, 2026]),
        (["id_solicitud", "origen", "destino", "precio", "id_oferta", "monto", "llegada", "placa", "conductor"],
         [["2", "Plaza San Miguel", "Centro de Lima", "16.00", "3", "17.00", "3", "ABC-123", "Luis Quispe"],
          ["3", "Barranco", "San Isidro", "20.00", "4", "22.00", "5", "BCD-234", "Carla Mendoza"]],
         [600, 1400, 1250, 700, 700, 700, 700, 1000, 1976]),
    ]
    for n, ((titulo, sql), tec, (cab, filas, anchos)) in enumerate(zip(consultas, tecnica, resultados), 1):
        s.add(para(runs(f"**Consulta {n}. {titulo}.** Técnica: {tec}."), keep_next=True, before=160, after=60))
        s.add(codigo(formatear_sql(sql)))
        s.add(para(runs("Resultado con el seed:", sz=18, color="555555", base_i=True), keep_next=True, before=60, after=40))
        s.add(tabla(cab, filas, anchos, sz=15, zebra=False))

    # ------------------------------------------------------------------ 10.9 transacciones
    s.titulo(2, "10.9 Transacciones e integridad")
    s.add(texto("El servidor ejecuta las operaciones que modifican varias filas dentro de una transacción mediante el helper `transaction` de "
                "`server/db.js`: abre una conexión del pool, inicia la transacción, ejecuta la operación y hace COMMIT si termina o "
                "ROLLBACK si falla, liberando siempre la conexión. Usan este helper las altas, las ediciones, la aceptación de ofertas, la "
                "cancelación de solicitudes y el inicio y la finalización de viajes."))
    s.add(texto("**Aceptación de una oferta.** Es la operación crítica. El siguiente pseudocódigo resume `POST /api/offers/:id/accept` de "
                "`server/app.js`:"))
    s.add(codigo(["transaction( conexión => {",
                  "   oferta    <- SELECT id_solicitud FROM oferta WHERE id_oferta = ?",
                  "   solicitud <- SELECT estado FROM solicitud WHERE id_solicitud = ? FOR UPDATE   -- bloquea la fila",
                  "   si solicitud.estado <> 'abierta'  ->  error 409 'La solicitud ya no está abierta'",
                  "   INSERT INTO viaje (id_oferta) VALUES (?)     -- el trigger viaje_ai pasa la solicitud a 'aceptada'",
                  "} )                                            -- COMMIT si termina; ROLLBACK si hay error"]))
    s.add(texto("Si dos clientes aceptan a la vez dos ofertas de la misma solicitud, el segundo espera el bloqueo `FOR UPDATE` hasta que el "
                "primero confirma; entonces lee el estado «aceptada», recibe un conflicto 409 y su transacción se revierte ([[F:trans]]). "
                "El proyecto usa el nivel de aislamiento por defecto de InnoDB y no lo modifica.", before=100))
    w, h = px("transaccion")
    s.figura(DIAG / "transaccion.png", "Aceptación simultánea de dos ofertas de una misma solicitud", 5300000, w, h,
             "Dos clientes ejecutan la aceptación; el segundo espera el bloqueo y recibe un conflicto 409", "trans")
    s.add(texto("**Propiedades ACID.** La atomicidad la aportan COMMIT y ROLLBACK; la consistencia, las restricciones y los triggers; el "
                "aislamiento, los bloqueos de fila de InnoDB sobre solicitud, viaje y pago; y la durabilidad, el motor InnoDB una vez confirmada "
                "la transacción.", before=60))
    s.add(texto("**Traducción de errores.** El servidor convierte los errores del motor en respuestas HTTP comprensibles y no expone mensajes "
                "internos en los errores inesperados ([[T:errores]])."))
    s.leyenda_tabla("Errores del motor y respuesta de la API", "errores")
    s.add(tabla(["Error del motor", "HTTP", "Significado"], [
        ["ER_DUP_ENTRY", "409", "Violación de UNIQUE: placa, teléfono, correo, licencia o relación única"],
        ["ER_ROW_IS_REFERENCED / _2", "409", "Borrado impedido por una FK RESTRICT"],
        ["ER_NO_REFERENCED_ROW / _2", "400", "El registro relacionado no existe"],
        ["SQLSTATE 45000 (SIGNAL de un trigger)", "409", "Regla entre tablas incumplida; se muestra el mensaje del trigger"],
        ["ER_CHECK_CONSTRAINT_VIOLATED, ER_DATA_TOO_LONG y similares", "400", "Dato fuera de rango, formato o longitud"],
        ["ER_LOCK_DEADLOCK / ER_LOCK_WAIT_TIMEOUT", "409", "Otra operación modificó los datos; reintentar"],
        ["Cualquier otro", "500", "Mensaje genérico; el detalle se registra solo en el servidor"],
    ], [3500, 800, 4726], sz=16, mono_cols=(0,), jc_cols={1: "center"}))

    # ------------------------------------------------------------------ 10.10 pruebas
    s.titulo(2, "10.10 Pruebas y evidencias")
    s.add(texto("La evidencia se organiza por nivel. Cada fila indica qué se comprueba, dónde está el código de la prueba y qué resultado se "
                "puede verificar. Los números de ejecución corresponden a GitHub Actions, en el repositorio del proyecto."))
    s.leyenda_tabla("Pruebas del proyecto y evidencia verificable", "pruebas")
    s.add(tabla(["Prueba", "Qué comprueba", "Resultado verificable"], [
        ["`npm test` (10 pruebas)", "Validación de entradas (5), errores de arranque (2) y reintentos de conexión (3); `tests/*.test.js`",
         "Paso «Validación de entradas y errores de arranque» en verde en Actions"],
        ["Integridad SQL (23 casos)", "23 rechazos esperados (UNIQUE, FK, CHECK, triggers, RESTRICT) y un flujo positivo con ROLLBACK; `tests/integrity.sql`",
         "PASS en MariaDB 11.8.6 (`docs/VALIDACION-SQL.json`). Usa códigos de error de MariaDB: no se atribuye a MySQL"],
        ["Integración API", "Alta de datos, FK, rechazo de borrado, aceptación simultánea de la misma oferta y de dos ofertas distintas, aceptación rechazada sin viaje, pago, "
         "calificación, ROLLBACK tras una inserción, 8 tablas y 9 FK en el explorador y las 6 consultas; `tests/api.integration.js`",
         "Paso «Probar API, datos y aceptación concurrente» en verde con MySQL 8.0.44"],
        ["Compilación", "`vite build` de la interfaz React", "Paso «Compilar React» en verde"],
        ["Contenedores", "`docker compose up --build --wait` y `/api/health`", "Job «container» en verde"],
    ], [1900, 4300, 2826], sz=16))
    s.add(texto("Para la versión final de la rama del proyecto (commit `5841e63`), las ejecuciones **43644564327** (evento push) y **43644591366** "
                "(evento pull_request) terminaron con éxito, con los jobs `verify` y `container` aprobados. La ejecución 43644417563 "
                "corresponde al commit `dd6f5cb`, que añadió la prueba de ROLLBACK posterior a una escritura. La [[F:captura]] es una captura real de "
                "la página de resumen de la primera.", before=140))
    w, h = 2480, 860
    s.figura(ASSETS / "captura-actions-run-43644564327.png", "Resumen de la ejecución 43644564327 en GitHub Actions (commit 5841e63)", 5600000, w, h,
             "Captura de GitHub Actions: ejecución exitosa de los jobs verify y container", "captura")
    s.add(texto("Los resultados del seed verificados en MariaDB (`docs/VALIDACION-SQL.json`) fueron: 5 usuarios, 8 tablas, 1 viaje, total cobrado 20,0, "
                "1 oferta bajo el promedio, 1 solicitud sin ofertas y calificación promedio de conductor 5,0. Coinciden con el seed y con los "
                "resultados de la sección 10.8.", before=60))
    s.add(texto("**Límites de la evidencia.** (1) La suite de integridad SQL no se ejecutó sobre MySQL, solo sobre MariaDB. (2) El recorrido manual "
                "en navegador y las capturas de la interfaz siguen pendientes; por eso este informe no incluye capturas de la aplicación. "
                "(3) La integración continua corresponde a la rama del proyecto, no a `main`. (4) La prueba de integración escribe datos de "
                "prueba y debe ejecutarse solo en bases aisladas."))

    # ------------------------------------------------------------------ 10.11 prototipo
    s.titulo(2, "10.11 Prototipo de aplicación")
    s.add(texto("El prototipo se inicia con `npm run local` (Docker con Compose v2) y se abre en `http://127.0.0.1:3000`. Los datos son ficticios y "
                "la aplicación no está pensada para exponerse como producto público. La [[T:modulos]] resume sus módulos, tomados de la "
                "interfaz (`client/src/main.jsx`)."))
    s.leyenda_tabla("Módulos de la interfaz", "modulos")
    s.add(tabla(["Módulo", "Qué ofrece"], [
        ["Vista general", "Usuarios registrados, solicitudes abiertas, viajes acordados, total cobrado y solicitudes recientes"],
        ["Usuarios, Conductores, Vehículos", "Consulta con búsqueda y paginación de 25 registros; alta y edición con selectores de claves existentes"],
        ["Solicitudes", "Alta, edición y cancelación mientras la solicitud está abierta"],
        ["Ofertas", "Alta, edición y botón «Aceptar» que ejecuta la transacción de aceptación"],
        ["Viajes", "Se crean solo al aceptar una oferta; botones «Iniciar» y «Finalizar»"],
        ["Pagos y Calificaciones", "Cobro del viaje finalizado con el importe pactado; calificación por participante"],
        ["Explorador de Base de Datos", "Diagrama ER, diccionario por tabla, claves, CHECK, índices y triggers leídos de INFORMATION_SCHEMA"],
        ["Consultas SQL", "Catálogo de seis consultas con el SQL visible, parámetros validados, tiempo de ejecución y resultados"],
    ], [2700, 6326], sz=17, bold_first=True))
    s.add(texto("Las pruebas de la sección 10.10 recorren por API el mismo flujo que ofrece la interfaz. Las capturas de pantalla se incorporarán "
                "cuando se realice el ensayo manual de la demostración.", before=140))


def conclusiones_extra(s):
    for t in ["El modelo implementado, con ocho entidades, nueve claves foráneas, 15 restricciones CHECK y 18 triggers, representa el flujo "
              "de negociación de un viaje y protege el historial de viajes, pagos y calificaciones.",
              "La normalización hasta la tercera forma normal se justifica con las dependencias declaradas; la única redundancia entre "
              "relaciones, el monto del pago, se controla con un trigger.",
              "La aceptación de una oferta se ejecuta en una transacción que bloquea la solicitud. En la integración continua con MySQL 8.0.44, "
              "dos aceptaciones simultáneas de ofertas de una misma solicitud produjeron un solo viaje y un conflicto.",
              "La evidencia es parcial: la suite de integridad se validó en MariaDB y el recorrido manual en navegador sigue pendiente.",
              "Como trabajo futuro, y fuera del alcance actual, quedan las contraofertas, la cancelación de viajes aceptados, los reembolsos, la "
              "autenticación y la geolocalización."]:
        s.add(para(runs(t), style="Prrafodelista", num=2, after=80, line=320, jc="both"))


def referencias_extra(s):
    s.add(para(run("Referencias del desarrollo de base de datos", b=True), keep_next=True, before=200, after=100))
    refs = [
        "Chen, P. P.-S. (1976). The entity-relationship model: Toward a unified view of data. ACM Transactions on Database Systems, 1(1), 9-36. https://doi.org/10.1145/320434.320440",
        "Codd, E. F. (1970). A relational model of data for large shared data banks. Communications of the ACM, 13(6), 377-387. https://doi.org/10.1145/362384.362685",
        "Elmasri, R., y Navathe, S. B. (2016). Fundamentals of database systems (7.ª ed.). Pearson.",
        "Silberschatz, A., Korth, H. F., y Sudarshan, S. (2019). Database system concepts (7.ª ed.). McGraw-Hill.",
        "Oracle. (s. f.). MySQL 8.0 reference manual: FOREIGN KEY constraints. https://dev.mysql.com/doc/refman/8.0/en/create-table-foreign-keys.html",
        "Oracle. (s. f.). MySQL 8.0 reference manual: CHECK constraints. https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html",
        "Oracle. (s. f.). MySQL 8.0 reference manual: Locking reads. https://dev.mysql.com/doc/refman/8.0/en/innodb-locking-reads.html",
        f"Equipo del proyecto. (2026). DBProyecto: inDrive Lab [Repositorio de código]. GitHub. {REPO}",
    ]
    for r_ in refs:
        s.add(para(run(r_, sz=20), after=100, line=276, left=540, hanging=540))


def anexos(s):
    s.titulo(1, "Anexos", salto=True)
    s.titulo(2, "Anexo A. Casos de rechazo de la suite de integridad")
    s.add(texto("La [[T:anexoA]] enumera los 23 casos de `tests/integrity.sql`, en el orden del script. Cada caso debe fallar con el código "
                "indicado; los códigos son los de MariaDB (por ejemplo, 4025 es su error de CHECK, que en MySQL tiene otro número).", after=100))
    s.leyenda_tabla("Casos de rechazo de tests/integrity.sql", "anexoA")
    casos = [
        ("Usuario con teléfono repetido", "1062 UNIQUE"), ("Conductor con un usuario inexistente", "1452 FK"),
        ("Oferta con monto negativo", "4025 CHECK"), ("Oferta sobre una solicitud ya aceptada", "1644 trigger"),
        ("Segundo viaje para la misma solicitud (oferta 2)", "1644 trigger"), ("Modificar el monto de una oferta cerrada", "1644 trigger"),
        ("Cambiar el origen de una solicitud con ofertas", "1644 trigger"), ("Eliminar un usuario con historial", "1451 RESTRICT"),
        ("Eliminar un viaje", "1644 trigger"), ("Eliminar un pago", "1644 trigger"),
        ("Reasignar un vehículo con ofertas", "1644 trigger"), ("Calificación de un usuario ajeno al viaje", "1644 trigger"),
        ("Segunda calificación del mismo autor", "1062 UNIQUE"), ("Pago distinto al precio pactado", "1644 trigger"),
        ("Segundo pago para el mismo viaje", "1062 UNIQUE"), ("Modificar el importe de un pago", "1644 trigger"),
        ("Cambiar el autor de una calificación", "1644 trigger"), ("Puntaje igual a 6", "4025 CHECK"),
        ("Devolver un viaje finalizado a pendiente", "1644 trigger"), ("Ofertar en una solicitud propia", "1644 trigger"),
        ("Pago antes de finalizar el viaje", "1644 trigger"), ("Finalizar un viaje sin iniciarlo", "1644 trigger"),
        ("Aceptar una oferta de una solicitud cancelada", "1644 trigger"),
    ]
    assert len(casos) == 23 and len(re.findall(r"CALL esperar_error", leer("tests/integrity.sql"))) == 23
    s.add(tabla(["N.º", "Caso", "Error esperado"], [[str(i), c, e] for i, (c, e) in enumerate(casos, 1)], [700, 5800, 2526],
                sz=16, jc_cols={0: "center"}))

    s.titulo(2, "Anexo B. Triggers del esquema", salto=True)
    s.add(texto("La [[T:anexoB]] lista los 18 triggers de `database/01-schema.sql` y la regla que cada uno protege.", after=100))
    s.leyenda_tabla("Triggers y reglas que protegen", "anexoB")
    trs = [
        ("solicitud_bi", "BEFORE INSERT", "Una solicitud se crea abierta"),
        ("solicitud_bu", "BEFORE UPDATE", "Una solicitud cerrada no cambia; identidad inmutable; con ofertas no cambia ruta ni precio; solo pasa a «aceptada» si existe el viaje"),
        ("solicitud_bd", "BEFORE DELETE", "No se elimina una solicitud que no esté abierta"),
        ("conductor_bu", "BEFORE UPDATE", "Identidad del conductor inmutable"),
        ("vehiculo_bu", "BEFORE UPDATE", "La placa no cambia y no se reasigna un vehículo con ofertas"),
        ("oferta_bi", "BEFORE INSERT", "La solicitud debe estar abierta (la bloquea) y el conductor no puede ofertar en su propia solicitud"),
        ("oferta_bu", "BEFORE UPDATE", "Una oferta de solicitud cerrada conserva su precio; identidad inmutable"),
        ("oferta_bd", "BEFORE DELETE", "No se elimina una oferta cerrada"),
        ("viaje_bi", "BEFORE INSERT", "La solicitud debe estar abierta; el viaje nace pendiente y sin fechas"),
        ("viaje_ai", "AFTER INSERT", "Pasa la solicitud a «aceptada»"),
        ("viaje_bu", "BEFORE UPDATE", "Identidad inmutable; solo pendiente → en_curso → finalizado; fechas no futuras"),
        ("viaje_bd", "BEFORE DELETE", "Los viajes se conservan"),
        ("pago_bi", "BEFORE INSERT", "Solo se cobra un viaje finalizado y por el precio acordado"),
        ("pago_bu", "BEFORE UPDATE", "Importe, fecha e identidad del pago son históricos"),
        ("pago_bd", "BEFORE DELETE", "No se elimina un cobro"),
        ("calificacion_bi", "BEFORE INSERT", "Solo participantes de un viaje finalizado pueden calificar"),
        ("calificacion_bu", "BEFORE UPDATE", "Autor y viaje inmutables"),
        ("calificacion_bd", "BEFORE DELETE", "Las calificaciones se conservan"),
    ]
    nombres = re.findall(r"CREATE TRIGGER (\w+)", leer("database/01-schema.sql"))
    assert [t[0] for t in trs] == nombres and len(trs) == 18, nombres
    s.add(tabla(["Trigger", "Momento", "Regla"], [[a, b, c] for a, b, c in trs], [1800, 1500, 5726], sz=16, mono_cols=(0,)))

    s.titulo(2, "Anexo C. Enlaces de evidencia")
    s.leyenda_tabla("Enlaces del repositorio y de la verificación")
    s.add(tabla(["Elemento", "Enlace o ubicación"], [
        ["Repositorio", REPO],
        ["Pull Request con el modelo y las pruebas", f"{REPO}/pull/1 (rama feature/entrega-bd-indrive)"],
        ["Actions, commit 5841e63 (push)", f"{REPO}/actions/runs/43644564327"],
        ["Actions, commit 5841e63 (pull_request)", f"{REPO}/actions/runs/43644591366"],
        ["Actions, commit dd6f5cb (ROLLBACK)", f"{REPO}/actions/runs/43644417563"],
        ["Esquema, datos y consultas", "database/01-schema.sql, 02-seed.sql y 03-consultas.sql"],
        ["Pruebas", "tests/api.integration.js, tests/integrity.sql y tests/*.test.js"],
        ["Documentos de apoyo", "docs/MODELOS-ER-EER.md, MODELO-LOGICO-NORMALIZACION.md, ALGEBRA-RELACIONAL.md, DICCIONARIO.md y VALIDACION-SQL.json"],
        ["Diagramas editables de este informe", "docs/entrega/diagramas/*.svg"],
    ], [3000, 6026], sz=16, bold_first=True))


# ============================================================================= ensamblado
WQ = "{%s}" % W_NS


def q(t):
    return WQ + t


def ntexto(n):
    return "".join(t.text or "" for t in n.iter(q("t")))


def nestilo(n):
    e = n.find(f"{q('pPr')}/{q('pStyle')}")
    return e.get(q("val")) if e is not None else None


def fragmento(xml):
    raiz = ET.fromstring(f"<raiz {FRAG_NS}>{xml}</raiz>")
    return list(raiz)


def sombrear_encabezado(tbl):
    """Los encabezados de tabla del documento base tienen texto blanco sin relleno: se les añade el fondo."""
    fila = tbl.find(q("tr"))
    if fila is None or fila.find(f"{q('trPr')}/{q('tblHeader')}") is None:
        return
    for tc in fila.findall(q("tc")):
        pr = tc.find(q("tcPr"))
        if pr.find(q("shd")) is not None:
            continue
        shd = ET.Element(q("shd"), {q("val"): "clear", q("color"): "auto", q("fill"): TEAL})
        pos = list(pr).index(pr.find(q("tcBorders"))) + 1
        pr.insert(pos, shd)


def portada(nodos, s):
    """Reformatea la portada según la referencia de Hidro-Mejora, conservando facultad, curso, docente e integrantes."""
    logo = nodos[0]
    cx = 3960000
    cy = int(cx * 379 / 954)
    for e in logo.iter():
        if e.tag.endswith("}extent") or e.tag.endswith("}ext") and e.get("cx"):
            e.set("cx", str(cx)); e.set("cy", str(cy))
        if e.tag.endswith("}blip"):
            e.set("{%s}embed" % R_NS, "rIdLogo")
        if e.tag.endswith("}docPr"):
            e.set("descr", "Logotipo oficial de la Universidad Norbert Wiener"); e.set("name", "Logo Universidad Norbert Wiener")
    ppr_logo = logo.find(q("pPr")); sp = ppr_logo.find(q("spacing")); sp.set(q("before"), "0"); sp.set(q("after"), "360")
    titulo = fragmento(
        para(run("INDRIVE LAB: BASE DE DATOS PARA LA NEGOCIACIÓN DE VIAJES", b=True, sz=26), jc="center", before=360, after=80, line=276) +
        para(run("Informe del proyecto", b=True, sz=22), jc="center", after=240))
    # nodos: 0 logo, 1 facultad, 2 vacío, 3 asignatura, ... 24 LIMA, 25 2026-II, 26 sección
    antes, despues = nodos[:2], nodos[2:]
    # se retiran cuatro párrafos vacíos entre los integrantes y la ciudad para conservar una sola página
    vacios = [i for i, n in enumerate(despues) if nestilo(n) is None and not ntexto(n).strip() and n.find(f".//{q('sectPr')}") is None]
    quitar = set(vacios[-6:-2])
    despues = [n for i, n in enumerate(despues) if i not in quitar]
    sectpr = despues[-1].find(f".//{q('sectPr')}")
    ref = ET.Element(q("footerReference"), {q("type"): "default", "{%s}id" % R_NS: "rIdPortada"})
    sectpr.insert(0, ref)
    return antes + titulo + despues


def indices(s):
    """Índice general y listas de figuras y tablas con la paginación calculada."""
    x = para(run("ÍNDICE", b=True, sz=26), jc="center", after=240)
    pie = [("right", "dot", 9026)]

    def bloque(entradas, instr, estilo_fn, texto_fn):
        out = ""
        for k, ent in enumerate(entradas):
            bm = ent[-1]
            pag = PAGES.get(bm, "")
            ini = ""
            if k == 0:
                ini = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
                       f'<w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
                       '<w:r><w:fldChar w:fldCharType="separate"/></w:r>')
            fin = '<w:r><w:fldChar w:fldCharType="end"/></w:r>' if k == len(entradas) - 1 else ""
            cont = (ini + f'<w:hyperlink w:anchor="{bm}" w:history="1">{run(texto_fn(ent))}<w:r><w:tab/></w:r>{run(str(pag))}</w:hyperlink>' + fin)
            out += para(cont, style=estilo_fn(ent), tabs=pie)
        return out

    x += bloque(s.cab, 'TOC \\o "1-2" \\h \\z \\u', lambda e: "TDC1" if e[0] == 1 else "TDC2", lambda e: e[1])
    x += para(run("ÍNDICE DE FIGURAS", b=True, sz=26), jc="center", after=240, page_break=True)
    x += bloque(s.figs, 'TOC \\h \\z \\c "Figura"', lambda e: "Tabladeilustraciones", lambda e: f"Figura {e[0]}. {e[1]}")
    x += para(run("ÍNDICE DE TABLAS", b=True, sz=26), jc="center", before=360, after=240)
    x += bloque(s.tabs, 'TOC \\h \\z \\c "Tabla"', lambda e: "Tabladeilustraciones", lambda e: f"Tabla {e[0]}. {e[1]}")
    return x


NUEVOS_ESTILOS = (
    '<w:style w:type="paragraph" w:styleId="Leyenda"><w:name w:val="caption"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>'
    '<w:uiPriority w:val="35"/><w:unhideWhenUsed/><w:qFormat/><w:pPr><w:spacing w:before="160" w:after="80"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:color w:val="1B1B1B"/><w:sz w:val="19"/><w:szCs w:val="19"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Cdigo"><w:name w:val="Código"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    f'<w:pPr><w:shd w:val="clear" w:color="auto" w:fill="{SOFT}"/><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
    '<w:ind w:left="60" w:right="60"/></w:pPr><w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>'
    '<w:sz w:val="15"/><w:szCs w:val="15"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Tabladeilustraciones"><w:name w:val="table of figures"/><w:basedOn w:val="Normal"/>'
    '<w:next w:val="Normal"/><w:uiPriority w:val="99"/><w:unhideWhenUsed/><w:pPr><w:spacing w:after="80"/></w:pPr></w:style>')

NUEVA_NUMERACION = ('<w:abstractNum w:abstractNumId="2"><w:multiLevelType w:val="hybridMultilevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/>'
                    '<w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="540" w:hanging="360"/></w:pPr>'
                    '</w:lvl></w:abstractNum>')
NUEVA_NUM = '<w:num w:numId="3"><w:abstractNumId w:val="2"/></w:num>'

PIE_PORTADA = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               f'<w:ftr xmlns:w="{W_NS}" xmlns:r="{R_NS}"><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:color w:val="555555"/>'
               '<w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:t>inDrive Lab – Base de Datos</w:t></w:r></w:p></w:ftr>')


def construir(paginas):
    PAGES.clear(); PAGES.update(paginas)
    zin = ZipFile(BASE)
    doc_xml = zin.read("word/document.xml").decode("utf8")
    raiz_tag = re.search(r"<w:document [^>]*>", doc_xml).group(0)
    for pfx, uri in re.findall(r'xmlns:(\w+)="([^"]+)"', raiz_tag):
        ET.register_namespace(pfx, uri)
    raiz = ET.fromstring(doc_xml.encode("utf8"))
    cuerpo = raiz.find(q("body"))
    nodos = list(cuerpo)
    sect_final = nodos.pop()
    assert sect_final.tag == q("sectPr")

    i_intro = next(i for i, n in enumerate(nodos) if nestilo(n) == "Ttulo2" and ntexto(n) == "1. Introducción")
    portada_nodos = nodos[:i_intro]
    portada_nodos = [n for n in portada_nodos if n.find(f".//{q('sectPr')}") is not None or True]
    # la portada termina en el párrafo con sectPr; lo posterior (índice antiguo) se descarta
    i_sect = next(i for i, n in enumerate(portada_nodos) if n.find(f".//{q('sectPr')}") is not None)
    portada_nodos = portada_nodos[:i_sect + 1]
    resto = nodos[i_intro:]

    s = Estado()
    leyendas = iter(["Ficha de datos de inDrive", "Hitos de la historia de inDrive", "Valores corporativos de inDrive",
                     "Equipo directivo global de inDrive", "Servicios de la plataforma inDrive",
                     "Entidades del modelo implementado", "Análisis FODA de inDrive"])
    nuevos_listos = False
    primero = True
    for n in resto:
        tag = n.tag
        txt = ntexto(n) if tag == q("p") else ""
        est = nestilo(n) if tag == q("p") else None
        if est == "Ttulo2":
            if txt.startswith("8. Análisis FODA") and not nuevos_listos:
                seccion_8(s); seccion_9(s); paginas_er(s); seccion_10_resto(s); nuevos_listos = True
            txt = txt.replace("8. Análisis FODA", "11. Análisis FODA").replace("9. Conclusiones", "12. Conclusiones")
            if re.match(r"^\d+\.\d+ ", txt):
                s.titulo(2, txt)
            else:
                s.titulo(1, txt, salto=primero)
            primero = False
            continue
        if tag == q("tbl"):
            sombrear_encabezado(n)
            s.leyenda_tabla(next(leyendas), "t_comp" if False else None)
            s.add(n)
            s.add(para("", after=60))
            continue
        if tag == q("p") and n.find(f".//{q('drawing')}") is not None:
            s.figura_existente(n, "Organigrama simplificado del equipo directivo de inDrive")
            continue
        if tag == q("p") and txt.startswith("Precisiones técnicas de implementación"):
            s.add(texto("Precisiones técnicas de implementación: este modelo sigue siendo un ejercicio académico propio y no describe la base de "
                        "datos interna de inDrive. El informe inicial no especificaba motor ni consultas SQL. Se seleccionó MySQL 8.0.16 o superior "
                        "con InnoDB. El esquema se validó en MariaDB 11.8.6 en modo bootstrap y, además, la integración continua del repositorio "
                        "ejecuta el flujo completo sobre MySQL 8.0.44 (sección 10.10). El recorrido manual en navegador no forma parte de la "
                        "evidencia presentada."))
            continue
        if tag == q("p") and est is None and txt.startswith(("La normalización evita almacenar", "Reglas adoptadas para hacer", "Los scripts ejecutables, el análisis")):
            s.add(texto(txt)); continue
        if tag == q("p") and txt.startswith("La información proviene del sitio corporativo"):
            s.add(n); intro_extra(s); continue
        if tag == q("p") and est == "Prrafodelista" and txt.startswith("Para una empresa de este tipo"):
            s.add(n); conclusiones_extra(s); continue
        s.add(n)
    # la última leyenda de tabla (FODA) quedó antes de los anexos; las referencias nuevas y los anexos van al final
    referencias_extra(s)
    anexos(s)

    # ---- portada
    cabeza = portada(portada_nodos, s)
    # ---- cuerpo final
    nuevo = ET.Element(q("body"))
    for n in cabeza:
        nuevo.append(n)
    for xml in fragmento(indices(s)):
        nuevo.append(xml)
    etiquetas = s.etq
    for it in s.cuerpo:
        if isinstance(it, str):
            it = re.sub(r"\[\[([TF]):(\w+)\]\]", lambda m: etiquetas[m.group(2)], it)
            for e in fragmento(it):
                nuevo.append(e)
        else:
            nuevo.append(it)
    # sección final: vertical, sin reinicio de numeración (el reinicio está en la primera sección tras la portada)
    for e in list(sect_final):
        if e.tag == q("pgNumType"):
            sect_final.remove(e)
    nuevo.append(sect_final)
    raiz.remove(cuerpo); raiz.append(nuevo)
    xml_doc = ET.tostring(raiz, encoding="utf-8", xml_declaration=True).decode("utf8")
    # el elemento raíz original declara todos los espacios de nombres que mc:Ignorable exige
    xml_doc = re.sub(r"<w:document [^>]*>", raiz_tag, xml_doc, count=1)

    # ---- partes del paquete
    rels = zin.read("word/_rels/document.xml.rels").decode("utf8")
    rels = re.sub(r'<Relationship Id="rId8"[^>]*/>', "", rels)
    extra = ['<Relationship Id="rIdLogo" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/logo-universidad-norbert-wiener.png"/>',
             '<Relationship Id="rIdPortada" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer2.xml"/>']
    medios = {"word/media/logo-universidad-norbert-wiener.png": ASSETS / "logo-universidad-norbert-wiener.png"}
    for rid, destino, archivo in s.rels:
        extra.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{destino}"/>')
        medios["word/" + destino] = archivo
    rels = rels.replace("</Relationships>", "".join(extra) + "</Relationships>")
    tipos = zin.read("[Content_Types].xml").decode("utf8").replace(
        "</Types>", '<Override PartName="/word/footer2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>')
    estilos = zin.read("word/styles.xml").decode("utf8").replace("</w:styles>", NUEVOS_ESTILOS + "</w:styles>")
    num = zin.read("word/numbering.xml").decode("utf8")
    num = num.replace("<w:num ", NUEVA_NUMERACION + "<w:num ", 1).replace("</w:numbering>", NUEVA_NUM + "</w:numbering>")
    core = zin.read("docProps/core.xml").decode("utf8").replace("Informe de la empresa inDrive", "Informe de Base de Datos: inDrive Lab")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    reemplazos = {"word/document.xml": xml_doc, "word/_rels/document.xml.rels": rels, "[Content_Types].xml": tipos,
                  "word/styles.xml": estilos, "word/numbering.xml": num, "docProps/core.xml": core}
    with ZipFile(SALIDA, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", reemplazos["[Content_Types].xml"])
        for info in zin.infolist():
            if info.is_dir() or info.filename == "[Content_Types].xml" or info.filename == "word/media/image1.png":
                continue
            data = reemplazos[info.filename].encode("utf8") if info.filename in reemplazos else zin.read(info.filename)
            z.writestr(info.filename, data)
        z.writestr("word/footer2.xml", PIE_PORTADA)
        for destino, archivo in medios.items():
            z.writestr(destino, archivo.read_bytes())
    return s


# ----------------------------------------------------------------------------- paginación del índice
def paginar(s):
    """Convierte con LibreOffice y devuelve {marcador: página mostrada} (la portada no cuenta)."""
    if not shutil.which("soffice") or not shutil.which("pdftotext"):
        print("Sin soffice/pdftotext: el índice queda sin números de página (Word los calcula con «Actualizar campos»)", file=sys.stderr)
        return {}
    with tempfile.TemporaryDirectory(prefix="informe-") as tmp:
        subprocess.run(["soffice", f"-env:UserInstallation=file://{tmp}/perfil", "--headless", "--convert-to", "pdf", "--outdir", tmp, str(SALIDA)],
                       check=True, capture_output=True, timeout=240)
        pdf = Path(tmp) / (SALIDA.stem + ".pdf")
        paginas = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True, text=True).stdout.split("\f")
        if os.environ.get("INFORME_PDF"):
            shutil.copy(pdf, os.environ["INFORME_PDF"])      # copia opcional para revisar el diseño
    inicio = next(i for i, p in enumerate(paginas) if "El presente informe describe a inDrive" in p)
    res = {}
    for nivel, t, bm in s.cab:
        rx = re.compile(r"^\s*" + re.escape(t) + r"\s*$", re.M)
        for i in range(inicio, len(paginas)):
            if rx.search(paginas[i]):
                res[bm] = i      # índice base 0 = página del PDF − 1 = número mostrado (la portada no se numera)
                break
        else:
            print("No se encontró el título:", t, file=sys.stderr)
    for lista, etiqueta in ((s.figs, "Figura"), (s.tabs, "Tabla")):
        for n, t, bm in lista:
            rx = re.compile(r"^\s*" + etiqueta + " " + str(n) + r"\. ", re.M)
            for i in range(inicio, len(paginas)):
                if rx.search(paginas[i]):
                    res[bm] = i
                    break
            else:
                print("No se encontró la leyenda:", etiqueta, n, file=sys.stderr)
    print(f"{len(paginas) - 1} páginas en el PDF de prueba")
    return res


def main():
    s = construir({})
    pag = paginar(s)
    s = construir(pag)
    pag2 = paginar(s)
    if pag2 != pag:
        s = construir(pag2)
        pag3 = paginar(s)
        print("Paginación estable:", pag3 == pag2)
    print("OK", SALIDA.relative_to(ROOT), f"{SALIDA.stat().st_size // 1024} KB;", f"{s.nfig} figuras, {s.ntab} tablas, {len(s.cab)} títulos")


if __name__ == "__main__":
    main()
