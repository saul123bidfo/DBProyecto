#!/usr/bin/env python3
"""Construye docs/entrega/Presentacion_inDrive_BD.pptx (16:9, editable).

Solo biblioteca estándar. Los diagramas se insertan como PNG con su SVG editable (PowerPoint: clic derecho,
«Convertir en forma»). Antes ejecutar: python3 scripts/entrega/diagramas.py
Uso: python3 scripts/entrega/construir_pptx.py
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pptx_lib import *  # noqa: E402,F401,F403
import pptx_lib as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SALIDA = ROOT / "docs/entrega/Presentacion_inDrive_BD.pptx"
DIAG = ROOT / "docs/entrega/diagramas"
ASSETS = ROOT / "docs/entrega/assets"

DEIVIS, LUIS, DARLY, SAUL = "Deivis Ancco", "Luis Rodriguez", "Darly Quispe", "Saul Chauca"
MEDIOS = {}


def medio(archivo):
    MEDIOS[archivo.name] = archivo.read_bytes()
    return archivo.name


def dim(nombre):
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', (DIAG / f"{nombre}.svg").read_text(encoding="utf8"))
    return int(m.group(1)), int(m.group(2))


def diagrama(sl, nombre, x, y, alto=None, ancho=None, descr=""):
    w, h = dim(nombre)
    if alto:
        ancho = alto * w / h
    else:
        alto = ancho * h / w
    sl.imagen(medio(DIAG / f"{nombre}.png"), medio(DIAG / f"{nombre}.svg"), x, y, ancho, alto, descr)
    return ancho, alto


def chip(sl, x, y, w, h, n, titulo, sub="", oscuro=False, size=16):
    """Tarjeta con número en círculo, palabra clave y una línea de apoyo."""
    fondo, tit, apoyo = (TINTA, BLANCO, "D1D5DB") if oscuro else (SUAVE, NEGRO, GRIS)
    sl.forma(x, y, w, h, [], fondo, None, nombre="Tarjeta")
    sl.circulo(x + 0.18, y + (h - 0.5) / 2, 0.5, str(n), LIMA, NEGRO, 16)
    ps = [P(titulo, size, True, tit)]
    if sub:
        ps.append(P(sub, 13, False, apoyo, before=2))
    sl.texto(x + 0.85, y + 0.08, w - 1.0, h - 0.16, ps, anchor="ctr", nombre="Texto de tarjeta")


def dato(sl, x, y, w, h, grande, texto, oscuro=False, color_n=None, size_n=30):
    fondo = TINTA if oscuro else SUAVE
    sl.forma(x, y, w, h, [], fondo, None, nombre="Dato")
    sl.texto(x + 0.2, y + 0.08, w - 0.4, h * 0.46, [P(grande, size_n, True, color_n or (LIMA if oscuro else VERDE))], anchor="b", nombre="Cifra")
    sl.texto(x + 0.2, y + h * 0.56, w - 0.4, h * 0.42, [P(texto, 13, False, "D1D5DB" if oscuro else GRIS)], anchor="t", nombre="Descripción de la cifra")


def construir():
    ds = []

    # ------------------------------------------------------------------ 1 portada
    s = Diapositiva(0, notas=(
        f"Responsable: {DEIVIS}.\n"
        "Presentamos el proyecto del curso de Base de Datos: inDrive Lab, una base de datos relacional para el flujo de negociación de viajes. "
        "Es un modelo ilustrativo propio, no la base de datos interna de inDrive.\n"
        "Nos presentamos: Deivis Nicolas Abdias Ancco Gomez, Luis Franchesco Rodriguez Santalaya, Darly Cielo Quispe Mimbela y Saul David Chauca Cruz. "
        "Docente: Julio Alfredo Martín Cordova Forero.\n"
        "Adelantamos el recorrido: problema, objetivos, propuesta, modelos, normalización, SQL, transacciones, pruebas y prototipo."))
    s.imagen(medio(ASSETS / "logo-universidad-norbert-wiener.png"), None, (W_IN - 4.4) / 2, 0.55, 4.4, 4.4 * 379 / 954,
             "Logotipo oficial de la Universidad Norbert Wiener")
    s.texto(0.9, 2.75, 11.53, 0.4, [P("FACULTAD DE INGENIERÍA DE SISTEMAS E INFORMÁTICA", 14, True, GRIS, "ctr")], nombre="Facultad")
    s.texto(1.4, 3.15, 10.53, 1.25, [P("inDrive Lab: base de datos para la negociación de viajes", 32, True, NEGRO, "ctr")], anchor="ctr", nombre="Título del proyecto")
    s.texto(0.9, 4.5, 11.53, 0.4, [P("Presentación del proyecto · Curso: Base de Datos", 18, False, TINTA, "ctr")], nombre="Curso")
    s.texto(0.9, 5.0, 11.53, 0.35, [P([("Docente: ", dict(bold=True)), ("Julio Alfredo Martín Cordova Forero", {})], 16, False, TINTA, "ctr")], nombre="Docente")
    s.texto(0.9, 5.45, 11.53, 0.35, [P("Integrantes", 16, True, TINTA, "ctr")], nombre="Rótulo de integrantes")
    s.texto(1.9, 5.8, 9.53, 0.8, [P("Deivis Nicolas Abdias Ancco Gomez · Luis Franchesco Rodriguez Santalaya", 15, False, TINTA, "ctr"),
                                   P("Darly Cielo Quispe Mimbela · Saul David Chauca Cruz", 15, False, TINTA, "ctr", before=3)],
            nombre="Integrantes")
    s.texto(0.9, 6.8, 11.53, 0.35, [P("Lima, Perú · 2026 – II", 14, False, GRIS, "ctr")], nombre="Lugar y periodo")
    ds.append(s)

    # ------------------------------------------------------------------ 2 índice
    s = Diapositiva(2, "Índice", notas=(
        f"Responsable: {DEIVIS}.\n"
        "Este es el mapa de la exposición, de catorce paradas. Primero el problema y los objetivos; luego la propuesta y la arquitectura; "
        "después los modelos (ER, EER y lógico), la normalización, el álgebra y el SQL; y al final transacciones, pruebas, prototipo y conclusiones.\n"
        "Nos repartimos la exposición entre los cuatro: Deivis hasta los objetivos, Luis de la propuesta al EER, Darly del modelo lógico al SQL y Saul de las transacciones a las conclusiones."))
    items = ["Problemática", "Objetivos", "Propuesta", "Arquitectura", "Modelo ER", "Modelo EER", "Modelo lógico", "Normalización", "Álgebra relacional",
             "Consultas SQL", "Transacciones", "Pruebas y evidencias", "Prototipo", "Conclusiones"]
    for k, t in enumerate(items):
        col, fila = k % 3, k // 3
        x, y = 0.6 + col * 4.1, 1.55 + fila * 1.05
        s.forma(x, y, 3.85, 0.85, [], TINTA, None, nombre="Tarjeta")
        s.circulo(x + 0.17, y + 0.17, 0.5, str(k + 1), LIMA, NEGRO, 16)
        s.texto(x + 0.85, y + 0.1, 2.9, 0.65, [P(t, 18, True, BLANCO)], anchor="ctr", nombre="Tema")
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 3 problemática
    s = Diapositiva(2, "Cada viaje es una negociación", notas=(
        f"Responsable: {DEIVIS}.\n"
        "El modelo de inDrive, descrito en la sección 2.3 del informe, convierte cada viaje en una negociación: el pasajero propone un precio, los conductores ofertan y el pasajero elige.\n"
        "Para que eso funcione, cada paso debe quedar registrado de forma consistente: qué oferta originó el viaje, cuánto se acordó, cuánto se cobró y quién calificó a quién.\n"
        "Si se gestionara sin un modelo relacional, aparecerían cuatro riesgos principales: personas o vehículos duplicados, registros huérfanos, doble aceptación de ofertas y pérdida del historial. "
        "En el informe hay tres más: importes incoherentes, calificaciones de terceros y datos redundantes.\n"
        "Aclaración importante: son riesgos de diseño que identificamos a partir del flujo. No son estadísticas de inDrive; no tenemos mediciones de su base de datos real."))
    for k, (a, b) in enumerate([("Pasajero propone", "origen, destino y precio"), ("Conductores ofertan", "monto y minutos de llegada"), ("Pasajero elige", "una oferta → un viaje")]):
        y = 1.6 + k * 1.55
        s.forma(0.6, y, 4.5, 1.15, [], LIMA, None, nombre="Paso")
        s.texto(0.85, y + 0.1, 4.0, 0.95, [P(a, 22, True, NEGRO), P(b, 14, False, TINTA, before=2)], anchor="ctr", nombre="Texto de paso")
        if k < 2:
            s.linea(2.85, y + 1.18, 2.85, y + 1.52, LIMA, 2.5)
    s.texto(5.7, 1.55, 7.0, 0.5, [P("Sin un modelo relacional aparecen…", 20, True, LIMA)], nombre="Encabezado")
    riesgos = [("Duplicados", "el mismo correo, teléfono o placa dos veces"), ("Registros huérfanos", "una oferta sin solicitud"),
               ("Doble aceptación", "dos viajes para un solo pedido"), ("Historial perdido", "viajes, pagos o calificaciones borrados")]
    for k, (t, d) in enumerate(riesgos):
        x, y = 5.7 + (k % 2) * 3.6, 2.2 + (k // 2) * 2.0
        s.forma(x, y, 3.4, 1.8, [], TINTA, None, nombre="Riesgo")
        s.circulo(x + 0.2, y + 0.2, 0.45, str(k + 1), LIMA, NEGRO, 14)
        s.texto(x + 0.2, y + 0.8, 3.0, 0.9, [P(t, 18, True, BLANCO), P(d, 14, False, "D1D5DB", before=2)], nombre="Texto de riesgo")
    s.texto(5.7, 6.3, 7.0, 0.5, [P("Son riesgos de diseño, no estadísticas de inDrive.", 13, False, "9CA3AF", italic=True)], nombre="Aclaración")
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 4 objetivos
    s = Diapositiva(1, "Objetivos", notas=(
        f"Responsable: {DEIVIS}.\n"
        "El objetivo general es diseñar, implementar y validar una base de datos relacional en MySQL para el flujo de negociación, y demostrarla con un prototipo web académico.\n"
        "Lo desglosamos en siete objetivos específicos: delimitar el alcance y los requisitos; elaborar los modelos ER y EER; derivar el modelo lógico y justificar la tercera forma normal; "
        "implementar el esquema con restricciones y triggers; formular consultas y expresiones de álgebra; garantizar la consistencia con transacciones; y comprobar todo con pruebas.\n"
        "Cada uno de esos objetivos tiene su diapositiva en lo que sigue. En alcance: no hay contraofertas, reembolsos, pasarelas de pago ni autenticación, porque el informe no los especifica como datos."))
    s.forma(0.6, 1.5, 12.13, 1.15, [P([("Objetivo general  ", dict(bold=True, size=16)),
                                       ("Diseñar, implementar y validar una base de datos relacional en MySQL para el flujo de negociación de viajes, y demostrarla con un prototipo web.", {})], 19, False, NEGRO)],
           LIMA, None, anchor="ctr", ins=(0.3, 0.1, 0.3, 0.1), nombre="Objetivo general")
    objs = [("Alcance y requisitos", "flujo urbano, 8 entidades"), ("ER y EER", "cardinalidades y especialización"), ("Lógico y 3FN", "claves y dependencias"),
            ("SQL e integridad", "PK, FK, UNIQUE, CHECK"), ("Consultas y álgebra", "6 consultas del catálogo"), ("Transacciones", "bloqueo y ROLLBACK"), ("Pruebas", "evidencia verificable")]
    for k, (t, d) in enumerate(objs):
        x, y = 0.6 + (k % 4) * 3.07, 3.0 + (k // 4) * 1.55
        chip(s, x, y, 2.9, 1.3, k + 1, t, d, size=15)
    dato(s, 0.6 + 3 * 3.07, 3.0 + 1.55, 2.9, 1.3, "8·9·15·18", "tablas · FK · CHECK · triggers", oscuro=True, size_n=26)
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 5 propuesta
    s = Diapositiva(1, "Propuesta: inDrive Lab", notas=(
        f"Responsable: {LUIS}.\n"
        "Nuestra propuesta es inDrive Lab: una aplicación web académica sobre MySQL 8 con InnoDB. No busca reemplazar el sistema de la empresa, sino demostrar cómo un modelo relacional bien diseñado sostiene la negociación.\n"
        "El flujo tiene seis pasos: solicitud abierta, ofertas, aceptación, viaje en curso, viaje finalizado y cierre con pago y calificaciones. La solicitud puede cancelarse mientras esté abierta.\n"
        "La aceptación es una sola transacción: crea el viaje pendiente y cierra la solicitud como aceptada.\n"
        "Los estados son una decisión de diseño nuestra para hacer ejecutable el ejemplo; no son políticas oficiales de inDrive.\n"
        "En cifras, el esquema tiene 8 tablas, 9 claves foráneas y 18 triggers, comprobados contra el script SQL."))
    pasos = [("Solicitud", "estado «abierta»", "El pasajero propone origen, destino y precio"),
             ("Ofertas", "0..N por solicitud", "Un vehículo ofrece monto y minutos de llegada"),
             ("Aceptación", "una transacción", "Crea el viaje; la solicitud pasa a «aceptada»"),
             ("Viaje en curso", "hora_inicio", "pendiente → en_curso"),
             ("Viaje finalizado", "hora_fin", "en_curso → finalizado"),
             ("Cierre", "tras finalizar", "1 pago por viaje · hasta 2 calificaciones")]
    xs, ys, cw, ch = [0.6, 4.75, 8.9], [1.5, 3.95], 3.83, 1.95
    for k, (t, sub, d) in enumerate(pasos):
        x, y = xs[k % 3], ys[k // 3]
        s.forma(x, y, cw, ch, [], SUAVE, None, nombre="Paso")
        s.circulo(x + 0.22, y + 0.22, 0.5, str(k + 1), LIMA, NEGRO, 16)
        s.texto(x + 0.9, y + 0.2, cw - 1.05, 0.55, [P(t, 20, True, NEGRO)], anchor="ctr", nombre="Título del paso")
        s.texto(x + 0.25, y + 0.9, cw - 0.5, 0.35, [P(sub, 15, True, VERDE)], nombre="Detalle del paso")
        s.texto(x + 0.25, y + 1.25, cw - 0.5, 0.62, [P(d, 14, False, GRIS)], nombre="Descripción del paso")
        if k % 3 < 2:
            s.linea(x + cw + 0.03, y + ch / 2, xs[k % 3 + 1] - 0.03, y + ch / 2, NEGRO, 2.5)
    s.linea(xs[2] + cw / 2, ys[0] + ch, xs[2] + cw / 2, 3.7, NEGRO, 2.5, flecha=False)
    s.linea(xs[2] + cw / 2, 3.7, xs[0] + cw / 2, 3.7, NEGRO, 2.5, flecha=False)
    s.linea(xs[0] + cw / 2, 3.7, xs[0] + cw / 2, ys[1], NEGRO, 2.5)
    s.forma(0.6, 6.1, 7.7, 0.7, [P("Alternativa: la solicitud puede pasar a «cancelada» mientras esté abierta.", 14, False, TINTA)], SUAVE, None, anchor="ctr", ins=(0.25, 0.05, 0.2, 0.05), nombre="Alternativa")
    s.forma(8.5, 6.1, 4.23, 0.7, [P("8 tablas · 9 FK · 18 triggers", 17, True, LIMA, "ctr")], NEGRO, None, anchor="ctr", nombre="Cifras")
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 6 arquitectura
    s = Diapositiva(1, "Arquitectura en tres capas", notas=(
        f"Responsable: {LUIS}.\n"
        "La arquitectura es cliente-servidor en tres capas. El navegador ejecuta una interfaz React 18 con Vite; el servidor Express 4 valida las entradas y es el único que ejecuta SQL contra MySQL 8.0.44 mediante un pool de conexiones de mysql2.\n"
        "Tres decisiones de seguridad: solo el servidor habla con la base de datos; no hay consola SQL libre, solo un catálogo cerrado de seis consultas de lectura con parámetros validados; y las operaciones de escritura son transaccionales.\n"
        "Se levanta con Docker Compose, con los servicios db, setup y app, y los puertos solo en loopback. GitHub Actions prueba el proyecto contra MySQL 8.0.44 en cada push y pull request.\n"
        "Es una demostración local sin autenticación; no debe exponerse como producto público."))
    bloques = [("Navegador", ["React 18.3.1 · Vite 6.4.4", "9 módulos de operación", "Explorador de BD", "Consultas SQL"]),
               ("Servidor", ["Express 4.22.3 · Node ≥ 20.19", "validate() de entradas", "transaction() para escrituras", "Catálogo de 6 consultas"]),
               ("Base de datos", ["MySQL 8.0.44 · InnoDB", "8 tablas · 9 FK RESTRICT", "15 CHECK · 18 triggers", "INFORMATION_SCHEMA"])]
    bx = [0.6, 4.9, 9.2]
    for k, (t, ls) in enumerate(bloques):
        s.forma(bx[k], 1.5, 3.53, 2.95, [], NEGRO, None, nombre="Capa")
        s.texto(bx[k] + 0.3, 1.65, 3.0, 0.5, [P(t.upper(), 18, True, LIMA)], anchor="ctr", nombre="Nombre de la capa")
        s.texto(bx[k] + 0.3, 2.25, 3.0, 2.1, [P(l, 15, False, BLANCO, after=9) for l in ls], nombre="Contenido de la capa")
    for k, (a_, b_) in enumerate([("API", "JSON"), ("mysql2", "pool")]):
        x1, x2 = bx[k] + 3.56, bx[k + 1] - 0.03
        s.linea(x1, 2.75, x2, 2.75, NEGRO, 2.5)
        s.linea(x2, 3.45, x1, 3.45, NEGRO, 2.5)
        s.texto(x1, 2.35, x2 - x1, 0.3, [P(a_, 12, True, GRIS, "ctr")], nombre="Etiqueta")
        s.texto(x1, 3.52, x2 - x1, 0.3, [P(b_, 12, False, GRIS, "ctr")], nombre="Etiqueta")
    s.forma(0.6, 4.75, 5.95, 1.2, [P("Entorno: Docker Compose", 16, True, NEGRO), P("servicios db · setup · app; puertos solo en loopback (app 3000 · MySQL 3307)", 14, False, GRIS, before=3)],
            SUAVE, None, anchor="ctr", ins=(0.25, 0.08, 0.2, 0.08), nombre="Entorno")
    s.forma(6.78, 4.75, 5.95, 1.2, [P("Verificación: GitHub Actions", 16, True, NEGRO), P("jobs verify (MySQL 8.0.44) y container, en cada push y pull request", 14, False, GRIS, before=3)],
            SUAVE, None, anchor="ctr", ins=(0.25, 0.08, 0.2, 0.08), nombre="Verificación")
    s.forma(0.6, 6.15, 12.13, 0.65, [P("Solo el servidor ejecuta SQL · sin consola libre · catálogo cerrado de 6 consultas", 16, True, LIMA, "ctr")], TINTA, None, anchor="ctr", nombre="Principio")
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 7 ER
    s = Diapositiva(1, "Modelo entidad-relación", notas=(
        f"Responsable: {LUIS}.\n"
        "Este es el modelo ER con ocho entidades: Usuario, Conductor, Vehículo, Solicitud, Oferta, Viaje, Pago y Calificación.\n"
        "Cómo leerlo: un usuario puede tener un perfil de conductor; un conductor posee vehículos; un usuario crea solicitudes; cada solicitud recibe ofertas de vehículos; una oferta puede originar un viaje; y el viaje tiene un pago y hasta dos calificaciones.\n"
        "Detalles que conviene remarcar: las dos restricciones UNIQUE compuestas, en Oferta (solicitud, placa) y en Calificación (viaje, autor), valen en conjunto, no por separado. "
        "Y una oferta solo se acepta una vez por solicitud: eso lo garantizan el bloqueo y los triggers, no solo la unicidad.\n"
        "Las nueve claves foráneas son obligatorias y usan RESTRICT."))
    ancho, alto = diagrama(s, "er", 0.6, 1.45, alto=5.35, descr="Diagrama ER con ocho entidades y nueve relaciones con sus cardinalidades")
    x0 = 0.6 + ancho + 0.3
    for k, (g, t) in enumerate([("8", "entidades"), ("9", "relaciones 1 : 0..1 y 1 : 0..N"), ("0..2", "calificaciones por viaje (autor único)")]):
        dato(s, x0, 1.5 + k * 1.8, W_IN - 0.6 - x0, 1.6, g, t)
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 8 EER
    s = Diapositiva(1, "Modelo EER: especialización parcial", notas=(
        f"Responsable: {LUIS}.\n"
        "La extensión que usamos es una especialización parcial: algunos usuarios además son conductores y para ellos se guarda la licencia.\n"
        "Como solo representamos un subtipo, no corresponde declarar disyunción ni inventar una especialización total.\n"
        "Pasajero no es un subtipo: es un rol que adquiere cualquier usuario al crear una solicitud, y un conductor también puede pedir un viaje.\n"
        "En la implementación no creamos una tabla extra para el rol. Conductor conserva su propia clave primaria y usa id_usuario como clave foránea única y no nula: cada conductor es exactamente un usuario y un usuario tiene como máximo un perfil."))
    ancho, alto = diagrama(s, "eer", 0.6, 1.45, alto=5.35, descr="Usuario con subtipo parcial Conductor; el rol de pasajero surge de la clave foránea de Solicitud")
    x0 = 0.6 + ancho + 0.35
    for k, (t, d) in enumerate([("Parcial", "hay usuarios sin perfil de conductor"), ("Pasajero = rol", "surge de Solicitud.id_usuario"), ("FK UNIQUE NOT NULL", "1 usuario → máx. 1 perfil")]):
        chip(s, x0, 1.6 + k * 1.75, W_IN - 0.6 - x0, 1.5, k + 1, t, d, size=16)
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 9 modelo lógico
    s = Diapositiva(1, "Modelo lógico y diccionario", notas=(
        f"Responsable: {DARLY}.\n"
        "El modelo lógico se obtiene del ER: ocho relaciones con sus claves. Aquí se ven las columnas con su tipo de dato, las claves primarias en verde y las claves foráneas con flechas hacia su padre.\n"
        "El diccionario documenta 42 atributos con tipo, nulabilidad, clave o restricción y descripción; está en el informe y, en ejecución, el Explorador de la aplicación lo lee de INFORMATION_SCHEMA.\n"
        "Las nueve claves foráneas aplican ON DELETE RESTRICT y ON UPDATE RESTRICT para proteger el historial. Solo hora_inicio y hora_fin admiten nulos, porque un viaje pendiente todavía no tiene fechas.\n"
        "Las claves candidatas: además de las primarias, teléfono y correo en Usuario, licencia en Conductor, y los pares (solicitud, placa) y (viaje, autor)."))
    ancho, alto = diagrama(s, "logico", 0.6, 1.45, alto=5.35, descr="Ocho tablas con columnas, tipos de datos, claves primarias, foráneas y únicas")
    x0 = 0.6 + ancho + 0.3
    for k, (g, t) in enumerate([("42", "atributos en el diccionario"), ("9/9", "FK con ON DELETE RESTRICT"), ("2", "columnas con NULL: hora_inicio y hora_fin")]):
        dato(s, x0, 1.5 + k * 1.8, W_IN - 0.6 - x0, 1.6, g, t)
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 10 normalización
    s = Diapositiva(1, "Normalización hasta 3FN", notas=(
        f"Responsable: {DARLY}.\n"
        "Primero las dependencias funcionales: cada clave candidata determina todos los atributos de su relación. No suponemos, por ejemplo, que el modelo determine la marca ni que un nombre identifique a una persona.\n"
        "1FN: valores atómicos; las ofertas de una solicitud son filas de Oferta, no una lista dentro de una celda.\n"
        "2FN: las claves primarias son simples, así que no hay dependencias parciales; en las candidatas compuestas asumimos que ni la solicitud ni la placa por sí solas determinan el monto.\n"
        "3FN: ningún atributo no clave determina a otro no clave. El nombre vive solo en Usuario, el conductor se obtiene por Vehículo, el monto pactado vive solo en Oferta y el promedio de calificación se calcula con AVG.\n"
        "Una redundancia controlada: Pago guarda un monto que debe coincidir con el de la oferta. No rompe la 3FN dentro de Pago, pero exige un control, y lo hace el trigger pago_bi. "
        "La conclusión de 3FN depende de los supuestos declarados."))
    cols = [("1FN", ["Valores atómicos", "Cada oferta es una fila", "Sin listas en celdas"]),
            ("2FN", ["Claves primarias simples", "Candidatas compuestas: (solicitud, placa) y (viaje, autor)", "Sin dependencias parciales"]),
            ("3FN", ["Conductor vía Vehículo", "Monto pactado solo en Oferta", "Promedio con AVG, no guardado"])]
    for k, (t, ls) in enumerate(cols):
        x = 0.6 + k * 4.1
        s.forma(x, 1.5, 3.85, 3.7, [], SUAVE, None, nombre="Columna")
        s.circulo(x + 0.25, 1.7, 0.85, t, LIMA, NEGRO, 20)
        s.texto(x + 0.3, 2.75, 3.3, 2.4, [P(l, 17, False, TINTA, after=10) for l in ls], nombre="Puntos clave")
    s.forma(0.6, 5.5, 12.13, 1.2, [P([("Redundancia controlada  ", dict(bold=True, color=LIMA)), ("Pago.monto debe igualar el precio pactado de la oferta → lo verifica el trigger pago_bi", {})], 18, False, BLANCO)],
            NEGRO, None, anchor="ctr", ins=(0.3, 0.1, 0.3, 0.1), nombre="Nota")
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 11 álgebra
    s = Diapositiva(1, "Álgebra relacional y su SQL", notas=(
        f"Responsable: {DARLY}.\n"
        "Mostramos un ejemplo: solicitudes abiertas sin ofertas. A la izquierda, el álgebra: A son las solicitudes abiertas, B las solicitudes que tienen alguna oferta, y la diferencia A menos B deja las abiertas sin ofertas; se reúne con Usuario para traer el nombre.\n"
        "A la derecha, el SQL equivalente del catálogo, consulta 4: un LEFT JOIN con IS NULL. El álgebra básica trabaja con conjuntos, por eso omite ORDER BY y LIMIT, que son de presentación.\n"
        "En el informe hay tres ejemplos: este, viajes y participantes con renombrado de Usuario, y cobros por método con el operador de agrupación gamma.\n"
        "Los operadores que usamos: sigma, pi, reunión, rho, diferencia y gamma."))
    s.forma(0.6, 1.5, 5.9, 3.6, [], NEGRO, None, nombre="Álgebra")
    s.texto(0.85, 1.62, 5.4, 0.4, [P("ÁLGEBRA", 13, True, LIMA)], nombre="Rótulo")
    s.texto(0.85, 2.05, 5.5, 2.9, [P("A = π id_solicitud (", 14, False, BLANCO, mono=True),
                                   P("      σ estado='abierta' (SOLICITUD) )", 14, False, BLANCO, mono=True, after=10),
                                   P("B = π id_solicitud ( OFERTA )", 14, False, BLANCO, mono=True, after=10),
                                   P("R = π id_solicitud, nombres,", 14, False, LIMA, mono=True),
                                   P("      origen, destino,", 14, False, LIMA, mono=True),
                                   P("      precio_ofrecido (", 14, False, LIMA, mono=True),
                                   P("      ( σ estado='abierta'", 14, False, LIMA, mono=True),
                                   P("        (SOLICITUD) ⋈ USUARIO )", 14, False, LIMA, mono=True),
                                   P("      ⋈ ( A − B ) )", 14, False, LIMA, mono=True)],
            nombre="Expresión")
    s.linea(6.6, 3.3, 7.2, 3.3, NEGRO, 3)
    s.forma(7.3, 1.5, 5.43, 3.6, [], SUAVE, None, nombre="SQL")
    s.texto(7.55, 1.62, 5.0, 0.4, [P("SQL · consulta 4", 13, True, VERDE)], nombre="Rótulo")
    sql = ["SELECT s.id_solicitud, u.nombres, s.origen,", "       s.destino, s.precio_ofrecido",
           "FROM solicitud s", "JOIN usuario u ON u.id_usuario = s.id_usuario", "LEFT JOIN oferta o", "  ON o.id_solicitud = s.id_solicitud",
           "WHERE o.id_oferta IS NULL", "  AND s.estado = 'abierta'"]
    s.texto(7.55, 2.05, 5.1, 2.9, [P(l, 12.5, False, NEGRO, mono=True, after=3) for l in sql], nombre="Sentencia")
    for k, (op, d) in enumerate([("σ", "selección"), ("π", "proyección"), ("⋈", "reunión"), ("ρ", "renombrado"), ("−", "diferencia"), ("γ", "agrupación")]):
        x = 0.6 + k * 2.05
        s.forma(x, 5.45, 1.9, 1.15, [], TINTA, None, nombre="Operador")
        s.texto(x, 5.5, 1.9, 0.65, [P(op, 28, True, LIMA, "ctr")], anchor="ctr", nombre="Símbolo")
        s.texto(x, 6.12, 1.9, 0.4, [P(d, 14, False, BLANCO, "ctr")], nombre="Nombre del operador")
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 12 consultas
    s = Diapositiva(1, "Seis consultas SQL del catálogo", notas=(
        f"Responsable: {DARLY}.\n"
        "El catálogo tiene seis consultas de solo lectura, que la aplicación ejecuta con parámetros validados y un máximo de 200 filas. Esta tabla resume la técnica de cada una y el resultado con los datos de demostración.\n"
        "Uno: viajes y participantes, con INNER JOIN. Dos: calificación de conductores con GROUP BY, HAVING y AVG; el mínimo de evaluaciones es un parámetro. Tres: ofertas bajo el promedio, con subconsulta correlacionada. "
        "Cuatro: solicitudes sin ofertas, con LEFT JOIN. Cinco: cobros por método con SUM. Seis: negociaciones abiertas.\n"
        "Los resultados de la última columna los derivamos de los datos del seed y coinciden con los totales verificados en el archivo VALIDACION-SQL.json: una oferta bajo el promedio, una solicitud sin ofertas, total cobrado 20 y promedio de conductor 5.\n"
        "Aclaración: no pudimos volver a ejecutar el SQL en la laptop para esta presentación; la verificación previa fue en MariaDB 11.8.6 y la de integración, en MySQL 8.0.44 en GitHub Actions."))
    filas = [["N.º", "Consulta", "Técnica", "Resultado con el seed"],
             ["1", "Viajes y participantes", "INNER JOIN · ORDER BY", "1 viaje: Ana → Luis, S/ 20.00"],
             ["2", "Calificación de conductores", "GROUP BY · HAVING · AVG", "Luis Quispe: 5.00 (1 evaluación)"],
             ["3", "Ofertas bajo el promedio", "Subconsulta correlacionada", "Oferta 2 (BCD-234): S/ 19.00"],
             ["4", "Solicitudes sin ofertas", "LEFT JOIN · IS NULL", "Solicitud 4: Estación Central → Jesús María"],
             ["5", "Cobros por método", "SUM · GROUP BY", "Efectivo: 1 pago, S/ 20.00, comisión 1.90"],
             ["6", "Negociaciones abiertas", "JOIN · WHERE · ORDER BY", "2 ofertas en solicitudes 2 y 3"]]
    s.tabla(0.6, 1.5, [0.8, 3.5, 3.4, 4.43], filas, alto_fila=0.66, size=15)
    s.texto(0.6, 6.3, 12.13, 0.4, [P("Resultados derivados del seed y coherentes con docs/VALIDACION-SQL.json; fuente: database/03-consultas.sql", 12, False, GRIS, italic=True)], nombre="Fuente")
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 13 transacciones
    s = Diapositiva(1, "Transacciones: una oferta, un viaje", notas=(
        f"Responsable: {SAUL}.\n"
        "Aquí está la operación crítica: aceptar una oferta. El servidor abre una transacción, bloquea la fila de la solicitud con SELECT … FOR UPDATE, verifica que siga abierta e inserta el viaje; el trigger viaje_ai pasa la solicitud a aceptada. Si todo sale bien, COMMIT; si algo falla, ROLLBACK.\n"
        "Si dos clientes aceptan al mismo tiempo dos ofertas de la misma solicitud, el segundo espera el bloqueo; cuando el primero confirma, lee que la solicitud ya está aceptada, recibe un conflicto 409 y su transacción se revierte.\n"
        "Esto lo comprueba la prueba de integración: dos aceptaciones simultáneas devuelven 201 y 409, y existe un solo viaje. Pasó en GitHub Actions con MySQL 8.0.44.\n"
        "Además, 18 triggers protegen el historial: viajes, pagos y calificaciones no se eliminan, y el importe de un pago no se modifica. El proyecto usa el aislamiento por defecto de InnoDB."))
    ancho, alto = diagrama(s, "transaccion", 0.6, 1.45, alto=5.35, descr="Dos clientes aceptan ofertas de la misma solicitud; el segundo espera el bloqueo y recibe un conflicto 409")
    x0 = 0.6 + ancho + 0.35
    for k, (g, t) in enumerate([("FOR UPDATE", "bloquea la solicitud"), ("[201, 409]", "resultado de la prueba concurrente"), ("18", "triggers protegen el historial")]):
        dato(s, x0, 1.5 + k * 1.8, W_IN - 0.6 - x0, 1.6, g, t)
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 14 pruebas
    s = Diapositiva(1, "Pruebas y evidencias", notas=(
        f"Responsable: {SAUL}.\n"
        "Organizamos la evidencia por niveles. Diez pruebas de JavaScript: cinco de validación, dos de errores de arranque y tres de reintentos de conexión. "
        "Una suite SQL de integridad con 23 casos de rechazo, que pasó en MariaDB 11.8.6; usa códigos de error de MariaDB, por eso no la atribuimos a MySQL. "
        "Y una prueba de integración de la API contra MySQL 8.0.44, que cubre altas, claves foráneas, aceptación concurrente, pago, calificación y rollback.\n"
        "A la derecha, una captura real de GitHub Actions: la ejecución 43644564327 del commit 5841e63, con los jobs verify y container en verde. La ejecución 43644591366, del evento pull request, también terminó con éxito.\n"
        "Límites que declaramos: el recorrido manual en navegador y las capturas de la interfaz siguen pendientes, y la integración continua corresponde a la rama del proyecto, no a main."))
    filas = [["Prueba", "Qué comprueba"],
             ["npm test · 10", "entradas, arranque, reintentos"],
             ["Integridad SQL · 23", "UNIQUE, FK, CHECK, triggers (MariaDB)"],
             ["Integración API", "concurrencia, rollback, 8 tablas y 9 FK (MySQL 8.0.44)"],
             ["Build y contenedores", "Vite y docker compose --wait"]]
    s.tabla(0.6, 1.5, [2.6, 4.2], filas, alto_fila=0.78, size=14)
    for k, (g, t) in enumerate([("2", "ejecuciones en verde (5841e63)"), ("23", "casos de rechazo SQL")]):
        dato(s, 0.6 + k * 3.5, 5.5, 3.3, 1.3, g, t)
    s.imagen(medio(ASSETS / "captura-actions-run-43644564327.png"), None, 7.7, 1.5, 5.03, 5.03 * 860 / 2480,
             "Captura real de GitHub Actions: ejecución 43644564327 exitosa, jobs verify y container")
    s.texto(7.7, 1.5 + 5.03 * 860 / 2480 + 0.1, 5.03, 0.6, [P("Captura real: Actions, ejecución 43644564327", 13, True, TINTA),
                                                            P("Falta: recorrido manual en navegador", 13, False, GRIS)], nombre="Pie de captura")
    s.forma(7.7, 4.45, 5.03, 2.35, [P("Límites declarados", 16, True, LIMA, after=6), P("· SQL de integridad: solo MariaDB", 14, False, BLANCO, after=3),
                                    P("· Sin capturas de la interfaz todavía", 14, False, BLANCO, after=3), P("· CI de la rama, no de main", 14, False, BLANCO)],
            NEGRO, None, anchor="ctr", ins=(0.3, 0.1, 0.3, 0.1), nombre="Límites")
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 15 prototipo
    s = Diapositiva(1, "Prototipo de la aplicación", notas=(
        f"Responsable: {SAUL}.\n"
        "Esto es un esquema de la interfaz, no una captura: el repositorio todavía no incluye capturas porque falta el ensayo manual. Los módulos y los textos están tomados del código de la interfaz.\n"
        "A la izquierda, la navegación: Vista general, Usuarios, Conductores, Vehículos, Solicitudes, Ofertas, Viajes, Pagos y Calificaciones; y el laboratorio académico, con el Explorador de Base de Datos y las Consultas SQL.\n"
        "La Vista general muestra usuarios registrados, solicitudes abiertas, viajes acordados y total cobrado; con los datos de demostración serían 5, 3, 1 y 20 soles.\n"
        "En Ofertas, el botón Aceptar ejecuta la transacción que vimos. En Viajes, los botones Iniciar y Finalizar. El Explorador lee tablas, claves, CHECK, índices y triggers de INFORMATION_SCHEMA y dibuja el diagrama.\n"
        "Se inicia con npm run local, en 127.0.0.1:3000. Son datos ficticios y la aplicación no está pensada para exponerse públicamente."))
    s.forma(0.6, 1.5, 12.13, 5.15, [], BLANCO, "D1D5DB", 1.5, adj=3000, nombre="Ventana")
    s.forma(0.6, 1.5, 2.85, 5.15, [], NEGRO, None, adj=3000, nombre="Barra lateral")
    s.texto(0.85, 1.65, 2.3, 0.4, [P([("inDrive ", dict(color=BLANCO)), ("LAB", dict(color=LIMA))], 18, True)], nombre="Marca")
    nav = ["Vista general", "Usuarios", "Conductores", "Vehículos", "Solicitudes", "Ofertas", "Viajes", "Pagos", "Calificaciones"]
    for k, t in enumerate(nav):
        s.texto(0.9, 2.15 + k * 0.32, 2.4, 0.3, [P(t, 13, k == 0, LIMA if k == 0 else "D1D5DB")], nombre="Menú")
    s.texto(0.9, 5.15, 2.4, 0.3, [P("LABORATORIO ACADÉMICO", 11, True, "9CA3AF")], nombre="Rótulo")
    s.texto(0.9, 5.48, 2.5, 0.3, [P("Explorador de Base de Datos", 12, False, "D1D5DB")], nombre="Menú")
    s.texto(0.9, 5.8, 2.4, 0.3, [P("Consultas SQL", 12, False, "D1D5DB")], nombre="Menú")
    s.texto(3.75, 1.65, 8.7, 0.5, [P("Cada viaje comienza con un acuerdo.", 24, True, NEGRO)], nombre="Titular")
    for k, (t, v) in enumerate([("Usuarios registrados", "5"), ("Solicitudes abiertas", "3"), ("Viajes acordados", "1"), ("Total cobrado", "S/ 20.00")]):
        x = 3.75 + k * 2.2
        s.forma(x, 2.3, 2.05, 1.2, [], SUAVE, None, nombre="Indicador")
        s.texto(x + 0.15, 2.38, 1.8, 0.35, [P(t, 12, False, GRIS)], nombre="Rótulo del indicador")
        s.texto(x + 0.15, 2.75, 1.8, 0.6, [P(v, 26, True, VERDE)], nombre="Valor")
    s.forma(3.75, 3.75, 4.2, 2.7, [], BLANCO, "D1D5DB", nombre="Panel")
    s.texto(3.95, 3.85, 3.8, 0.4, [P("Ofertas", 16, True, NEGRO)], nombre="Rótulo del panel")
    s.forma(3.95, 4.3, 3.85, 0.5, [P("ABC-123 · S/ 17.00 · 3 min", 13, False, TINTA)], SUAVE, None, anchor="ctr", nombre="Fila")
    s.forma(6.6, 4.35, 1.1, 0.4, [P("Aceptar", 13, True, NEGRO, "ctr")], LIMA, None, adj=50000, nombre="Botón Aceptar")
    s.forma(3.95, 4.9, 3.85, 0.5, [P("BCD-234 · S/ 22.00 · 5 min", 13, False, TINTA)], SUAVE, None, anchor="ctr", nombre="Fila")
    s.forma(6.6, 4.95, 1.1, 0.4, [P("Aceptar", 13, True, NEGRO, "ctr")], LIMA, None, adj=50000, nombre="Botón Aceptar")
    s.texto(3.95, 5.55, 3.8, 0.8, [P("«Aceptar» cierra la solicitud y crea el viaje en una transacción", 13, False, GRIS)], nombre="Nota del panel")
    s.forma(8.15, 3.75, 4.3, 2.7, [], NEGRO, None, nombre="Panel oscuro")
    s.texto(8.4, 3.88, 3.9, 0.4, [P("Explorador de Base de Datos", 16, True, LIMA)], nombre="Rótulo")
    s.texto(8.4, 4.35, 3.9, 2.0, [P("· Diagrama ER leído del motor", 14, False, BLANCO, after=5), P("· Diccionario por tabla", 14, False, BLANCO, after=5),
                                 P("· Claves, CHECK, índices", 14, False, BLANCO, after=5), P("· Triggers con su código", 14, False, BLANCO, after=5),
                                 P("· 6 consultas con SQL visible", 14, False, BLANCO)], nombre="Funciones")
    s.texto(0.6, 6.7, 12.13, 0.25, [P("Esquema de la interfaz (no es una captura): módulos y textos tomados de client/src/main.jsx; cifras = datos de demostración", 11, False, GRIS, italic=True)], nombre="Aviso")
    s.numero()
    ds.append(s)

    # ------------------------------------------------------------------ 16 conclusiones
    s = Diapositiva(2, "Conclusiones y evidencias", notas=(
        f"Responsable: {SAUL}.\n"
        "Cuatro conclusiones. Uno: el modelo, con ocho entidades, nueve claves foráneas, quince restricciones CHECK y dieciocho triggers, representa el flujo de negociación y protege el historial. "
        "Dos: la normalización hasta 3FN se justifica con las dependencias declaradas, y la única redundancia, el monto del pago, la controla un trigger. "
        "Tres: la aceptación de ofertas es transaccional; en MySQL 8.0.44, dos aceptaciones simultáneas dieron un viaje y un conflicto. "
        "Cuatro: la evidencia es parcial, y lo decimos: falta el recorrido manual con capturas y la suite de integridad se validó en MariaDB.\n"
        "Trabajo futuro, fuera de alcance: contraofertas, cancelación de viajes aceptados, reembolsos, autenticación y geolocalización.\n"
        "Las evidencias verificables están a la derecha: el repositorio, el Pull Request número 1 y las ejecuciones de Actions. El informe completo y esta presentación están en el repositorio, en la carpeta docs/entrega.\n"
        "Gracias. Quedamos atentos a sus preguntas."))
    for k, (t, d) in enumerate([("Modelo íntegro", "8 tablas · 9 FK · 15 CHECK · 18 triggers"), ("3FN justificada", "redundancia controlada: Pago.monto"),
                                ("Aceptación transaccional", "dos aceptaciones simultáneas → un viaje"), ("Evidencia parcial", "falta ensayo en navegador; SQL en MariaDB")]):
        chip(s, 0.6, 1.5 + k * 1.3, 6.5, 1.15, k + 1, t, d, oscuro=True, size=17)
    s.forma(7.5, 1.5, 5.23, 5.1, [], TINTA, None, nombre="Evidencias")
    s.texto(7.8, 1.65, 4.7, 0.4, [P("Evidencias verificables", 17, True, LIMA)], nombre="Rótulo")
    ev = [("Repositorio", "github.com/saul123bidfo/DBProyecto"), ("Pull Request #1", "modelo, documentación y pruebas"), ("Actions 43644564327", "commit 5841e63 · push · éxito"),
          ("Actions 43644591366", "commit 5841e63 · pull request · éxito"), ("Informe y PPT", "docs/entrega/")]
    for k, (a, b) in enumerate(ev):
        s.texto(7.8, 2.2 + k * 0.85, 4.7, 0.8, [P(a, 15, True, BLANCO), P(b, 13, False, "D1D5DB", before=1)], nombre="Evidencia")
    s.numero()
    ds.append(s)
    return ds


def main():
    ds = construir()
    disenos = [L.diseno("Portada", oscuro=False, con_titulo=False, pie=False), L.diseno("Contenido", oscuro=False),
               L.diseno("Oscura", oscuro=True)]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    L.escribir(SALIDA, ds, disenos, "inDrive Lab: base de datos para la negociación de viajes", "Equipo del proyecto de Base de Datos", MEDIOS)
    print("OK", SALIDA.relative_to(ROOT), f"{SALIDA.stat().st_size // 1024} KB, {len(ds)} diapositivas")


if __name__ == "__main__":
    main()
