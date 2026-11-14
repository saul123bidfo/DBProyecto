#!/usr/bin/env python3
"""Cruza las cifras y funciones que citan el informe y la presentación con el código y el SQL reales del repositorio.

No ejecuta SQL (no requiere motor): cuenta objetos del DDL, comprueba rutas y módulos y reproduce en Python la lógica
de las seis consultas sobre los datos de database/02-seed.sql para validar los resultados mostrados.
Uso: python3 scripts/entrega/verificar_entrega.py
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
fallos = []


def ok(cond, msg):
    print(("OK   " if cond else "FALLA"), msg)
    if not cond:
        fallos.append(msg)


def leer(r):
    return (ROOT / r).read_text(encoding="utf8")


ddl, seed, app, jsx, ci = leer("database/01-schema.sql"), leer("database/02-seed.sql"), leer("server/app.js"), leer("client/src/main.jsx"), leer(".github/workflows/ci.yml")

# ---- DDL
ok(len(re.findall(r"CREATE TABLE", ddl)) == 8, "8 tablas")
ok(len(re.findall(r"FOREIGN KEY", ddl)) == 9, "9 claves foráneas")
ok(len(re.findall(r"ON DELETE RESTRICT ON UPDATE RESTRICT", ddl)) == 9, "las 9 FK usan RESTRICT en borrado y actualización")
ok(len(re.findall(r"CONSTRAINT ck_", ddl)) == 15, "15 restricciones CHECK")
ok(len(re.findall(r"CREATE TRIGGER", ddl)) == 18, "18 triggers")
cols = 0
for t in re.findall(r"CREATE TABLE \w+ \((.*?)\n\) ENGINE", ddl, re.S):
    cols += len([l for l in t.split("\n") if re.match(r"^\s*\w+ (INT|VARCHAR|DECIMAL|DATETIME|SMALLINT|TINYINT)", l)])
ok(cols == 42, f"42 atributos en el diccionario (DDL: {cols})")
nulos = re.findall(r"^\s*(\w+) DATETIME NULL", ddl, re.M)
ok(nulos == ["hora_inicio", "hora_fin"], "solo hora_inicio y hora_fin admiten NULL")
ok("ENGINE=InnoDB" in ddl and "utf8mb4" in ddl, "InnoDB y utf8mb4")
ok("mysql:8.0.44" in leer("compose.yaml") and "mysql:8.0.44" in ci, "MySQL 8.0.44 en Compose y CI")

# ---- pruebas
ok(len(re.findall(r"CALL esperar_error", leer("tests/integrity.sql"))) == 23, "23 casos en tests/integrity.sql")
n_js = sum(len(re.findall(r"^test\(", leer(f"tests/{f}"), re.M)) for f in ["validation.test.js", "startup.test.js", "connection.test.js"])
ok(n_js == 10, f"10 pruebas JS (encontradas {n_js})")
ok(len(re.findall(r"\{id:'", leer("server/queries.js"))) == 6, "6 consultas en el catálogo de la API")
integ = leer("tests/api.integration.js")
ok("[201,409]" in integ and "assert.equal(explorer.tables.length,8)" in integ and "referenced_table).length,9)" in integ, "la prueba de integración comprueba [201,409], 8 tablas y 9 FK")
ok("Forzar rollback" in integ, "la prueba de integración incluye ROLLBACK tras escritura")
ok("FOR UPDATE" in app and "transaction(" in app, "app.js usa FOR UPDATE y transaction()")
for ruta in ["/api/offers/:id/accept", "/api/requests/:id/cancel", "/api/trips/:id/:action", "/api/explorer", "/api/queries", "/api/data/:table", "/api/health"]:
    ok(ruta in app, f"ruta {ruta} existe")
ok("ER_DUP_ENTRY" in app and "45000" in app and "ER_LOCK_DEADLOCK" in app, "traducción de errores del motor")
ok("ISOLATION" not in app and "ISOLATION" not in leer("server/db.js"), "no se modifica el nivel de aislamiento")

# ---- interfaz
nav = re.search(r"const nav=\[(.*?)\];", jsx, re.S).group(1)
ok(len(re.findall(r"\['\w+','[^']+','\w+'\]", nav)) == 9, "9 módulos de operación en la navegación")
for t in ["Explorador de Base de Datos", "Consultas SQL", "Diagrama ER", "Tablas y diccionario", "Integridad e índices", "Cada viaje comienza con un acuerdo.", "Aceptar", "Iniciar", "Finalizar"]:
    ok(t in jsx, f"interfaz contiene «{t}»")
ok("size=25" in jsx or "pages" in app and "size=25" in app, "paginación de 25 registros")

# ---- seed y consultas (simulación en Python de la lógica SQL)
def tuplas(bloque):
    return [tuple(x.strip().strip("'") for x in re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", t)) for t in re.findall(r"\(([^()]*)\)", bloque)]


def insert(tabla, cols=None):
    m = re.search(r"INSERT INTO %s[^;]*?VALUES\s*(.*?);" % tabla, seed, re.S)
    return tuplas(m.group(1))


usuarios = insert("usuario"); conductores = insert("conductor"); vehiculos = insert("vehiculo")
solicitudes = insert("solicitud"); ofertas = insert("oferta")
ok((len(usuarios), len(conductores), len(vehiculos), len(solicitudes), len(ofertas)) == (5, 2, 3, 4, 4), "seed: 5 usuarios, 2 conductores, 3 vehículos, 4 solicitudes, 4 ofertas")
nombre = {i + 1: u[0] for i, u in enumerate(usuarios)}
cond_usuario = {i + 1: int(c[0]) for i, c in enumerate(conductores)}
veh = {v[0]: int(v[1]) for v in vehiculos}
sol = {i + 1: dict(usuario=int(s_[0]), origen=s_[1], destino=s_[2], precio=float(s_[3])) for i, s_ in enumerate(solicitudes)}
ofe = {i + 1: dict(sol=int(o[0]), placa=o[1], monto=float(o[2]), min=int(o[3])) for i, o in enumerate(ofertas)}
viaje_oferta = 1       # INSERT INTO viaje (id_oferta) VALUES (1)
aceptadas = {ofe[viaje_oferta]["sol"]}
estado = {i: ("aceptada" if i in aceptadas else "abierta") for i in sol}
conductor_de = lambda o: nombre[cond_usuario[veh[ofe[o]["placa"]]]]

ok(f"{nombre[sol[ofe[1]['sol']]['usuario']]}→{conductor_de(1)}" == "Ana Torres→Luis Quispe" and ofe[1]["monto"] == 20.0, "consulta 1: viaje 1 de Ana Torres con Luis Quispe, S/ 20.00")
promedio = {}
for o, d in ofe.items():
    promedio.setdefault(d["sol"], []).append(d["monto"])
bajo = [o for o, d in ofe.items() if d["monto"] < sum(promedio[d["sol"]]) / len(promedio[d["sol"]])]
ok(bajo == [2] and ofe[2]["placa"] == "BCD-234" and ofe[2]["monto"] == 19.0, "consulta 3: solo la oferta 2 (BCD-234, 19.00) está bajo el promedio")
sin = [i for i in sol if estado[i] == "abierta" and not any(d["sol"] == i for d in ofe.values())]
ok(sin == [4] and sol[4]["origen"] == "Estación Central", "consulta 4: solo la solicitud 4 (Estación Central → Jesús María)")
abiertas = [(i, o) for o, d in ofe.items() for i in [d["sol"]] if estado[i] == "abierta"]
ok(sorted(abiertas) == [(2, 3), (3, 4)] and conductor_de(4) == "Carla Mendoza", "consulta 6: ofertas 3 y 4 de las solicitudes 2 y 3 (Luis Quispe y Carla Mendoza)")
pago = re.search(r"INSERT INTO pago[^;]*VALUES \(1,'efectivo',20,1\.90\)", seed)
ok(bool(pago), "consulta 5: un pago en efectivo de 20 con comisión 1.90 → neto 18.10")
calif = re.search(r"INSERT INTO calificacion[^;]*VALUES (.*?);", seed, re.S).group(1)
ok("(1,1,5," in calif and "(1,2,5," in calif, "consulta 2: el pasajero (usuario 1) calificó 5 al conductor Luis Quispe")
dash = (len(usuarios), sum(1 for e_ in estado.values() if e_ == "abierta"), 1, 20.0)
ok(dash == (5, 3, 1, 20.0), f"vista general con el seed: usuarios, abiertas, viajes, cobrado = {dash}")
val = json.loads(leer("docs/VALIDACION-SQL.json"))["summary"]
ok(val["ofertas_bajo_promedio"] == len(bajo) and val["sin_ofertas"] == len(sin) and val["cobrado"] == 20.0 and val["promedio_conductor"] == 5.0,
   "coincide con docs/VALIDACION-SQL.json")

# ---- documentos entregados
try:
    from zipfile import ZipFile
    doc = ZipFile(ROOT / "docs/entrega/Informe_inDrive_BD_final.docx").read("word/document.xml").decode("utf8")
    plano = re.sub(r"<[^>]+>", "", doc)
    for t in ["Deivis Nicolas Abdias Ancco Gomez", "Luis Franchesco Rodriguez Santalaya", "Darly Cielo Quispe Mimbela", "Saul David Chauca Cruz",
              "Julio Alfredo Martín Cordova Forero", "FACULTAD DE INGENIERÍA DE SISTEMAS E INFORMÁTICA", "Asignatura: Base de Datos"]:
        ok(t in plano, f"portada del informe conserva «{t}»")
    for t in ["Arsen Tomsky", "Yakutsk", "SUOL Innovations", "ASPEC", "One team"]:
        ok(t in plano, f"se conserva la investigación de los compañeros («{t}»)")
    ppt = ZipFile(ROOT / "docs/entrega/Presentacion_inDrive_BD.pptx")
    p1 = ppt.read("ppt/slides/slide1.xml").decode("utf8")
    for t in ["Julio Alfredo Martín Cordova Forero", "Base de Datos", "Deivis Nicolas Abdias Ancco Gomez", "Saul David Chauca Cruz", "Darly Cielo Quispe Mimbela", "Luis Franchesco Rodriguez Santalaya"]:
        ok(t in p1, f"portada del PPT contiene «{t}»")
    notas = [ppt.read(f"ppt/notesSlides/notesSlide{i}.xml").decode("utf8") for i in range(1, 17)]
    resp = [re.search(r"Responsable: ([^.<]+)\.", n).group(1) for n in notas]
    ok(all(resp.count(x) == 4 for x in set(resp)) and len(set(resp)) == 4, f"notas repartidas 4 + 4 + 4 + 4 entre {sorted(set(resp))}")
except FileNotFoundError:
    print("(aún no existen los documentos entregables)")

print("\nRESULTADO:", "todo coincide" if not fallos else f"{len(fallos)} discrepancias")
sys.exit(1 if fallos else 0)
