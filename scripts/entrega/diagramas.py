#!/usr/bin/env python3
"""Genera los diagramas del informe y de la presentación (SVG editable + PNG).

Solo usa la biblioteca estándar. Las tablas y columnas se copian del DDL
(database/01-schema.sql); verificar_contra_ddl() comprueba que coincidan.
El PNG se obtiene con un Chromium sin interfaz si existe (variable CHROME o la
caché de Playwright); si no, solo se escriben los SVG.

Uso: python3 scripts/entrega/diagramas.py
"""
import glob, os, re, subprocess, sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/entrega/diagramas"
OUT.mkdir(parents=True, exist_ok=True)

INK, LIME, GREEN, GRAY, SOFT = "#111111", "#C1F11D", "#2F7D00", "#6B7280", "#F3F6EC"
FONT = "Arial, Helvetica, sans-serif"

# ---------------------------------------------------------------- modelo de datos
# (etiqueta de clave, columna, tipo)
TABLAS = {
    "usuario": [("PK", "id_usuario", "INT"), ("", "nombres", "VARCHAR(120)"), ("UK", "telefono", "VARCHAR(20)"),
                ("UK", "correo", "VARCHAR(160)"), ("", "fecha_registro", "DATETIME")],
    "conductor": [("PK", "id_conductor", "INT"), ("FK·UK", "id_usuario", "INT"), ("UK", "licencia", "VARCHAR(20)")],
    "vehiculo": [("PK", "placa", "VARCHAR(10)"), ("FK", "id_conductor", "INT"), ("", "marca", "VARCHAR(50)"),
                 ("", "modelo", "VARCHAR(60)"), ("", "color", "VARCHAR(30)"), ("", "anio", "SMALLINT")],
    "solicitud": [("PK", "id_solicitud", "INT"), ("FK", "id_usuario", "INT"), ("", "origen", "VARCHAR(200)"),
                  ("", "destino", "VARCHAR(200)"), ("", "precio_ofrecido", "DECIMAL(10,2)"),
                  ("", "estado", "VARCHAR(12)"), ("", "fecha_solicitud", "DATETIME")],
    "oferta": [("PK", "id_oferta", "INT"), ("FK", "id_solicitud", "INT"), ("FK", "placa", "VARCHAR(10)"),
               ("", "monto", "DECIMAL(10,2)"), ("", "tiempo_llegada", "SMALLINT")],
    "viaje": [("PK", "id_viaje", "INT"), ("FK·UK", "id_oferta", "INT"), ("", "estado", "VARCHAR(12)"),
              ("", "hora_inicio", "DATETIME NULL"), ("", "hora_fin", "DATETIME NULL")],
    "pago": [("PK", "id_pago", "INT"), ("FK·UK", "id_viaje", "INT"), ("", "metodo", "VARCHAR(15)"),
             ("", "monto", "DECIMAL(10,2)"), ("", "comision", "DECIMAL(10,2)"), ("", "fecha_pago", "DATETIME")],
    "calificacion": [("PK", "id_calificacion", "INT"), ("FK", "id_viaje", "INT"), ("FK", "id_usuario", "INT"),
                     ("", "puntaje", "TINYINT"), ("", "comentario", "VARCHAR(500)")],
}
NOTAS = {"oferta": "UNIQUE (id_solicitud, placa)", "calificacion": "UNIQUE (id_viaje, id_usuario)"}
# (hijo, padre) = las nueve claves foráneas del DDL
FKS = [("conductor", "usuario"), ("vehiculo", "conductor"), ("solicitud", "usuario"), ("oferta", "solicitud"),
       ("oferta", "vehiculo"), ("viaje", "oferta"), ("pago", "viaje"), ("calificacion", "viaje"),
       ("calificacion", "usuario")]


def verificar_contra_ddl():
    ddl = (ROOT / "database/01-schema.sql").read_text(encoding="utf8")
    tablas = re.findall(r"CREATE TABLE (\w+)", ddl)
    assert sorted(tablas) == sorted(TABLAS), (tablas, list(TABLAS))
    fks = re.findall(r"CREATE TABLE (\w+)|FOREIGN KEY \((\w+)\) REFERENCES (\w+)", ddl)
    actual, tabla = [], None
    for t, _col, ref in fks:
        if t:
            tabla = t
        else:
            actual.append((tabla, ref))
    assert sorted(actual) == sorted(FKS), (sorted(actual), sorted(FKS))
    for nombre, cols in TABLAS.items():
        bloque = re.search(r"CREATE TABLE %s \((.*?)\n\) ENGINE" % nombre, ddl, re.S).group(1)
        for _t, col, _tipo in cols:
            assert re.search(r"(^|\n)\s*%s\s" % col, bloque), (nombre, col)
    return len(tablas), len(actual)


# ---------------------------------------------------------------- primitivas SVG
class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.p = w, h, []

    def add(self, s):
        self.p.append(s)

    def rect(self, x, y, w, h, fill="white", stroke=INK, sw=1.5, rx=10, dash=None, extra=""):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{extra}/>')

    def text(self, x, y, s, size=13, fill=INK, bold=False, anchor="start", italic=False):
        w = ' font-weight="700"' if bold else ""
        i = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{w}{i}>{escape(s)}</text>')

    def poly(self, pts, stroke=INK, sw=1.6, arrow=False, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#flecha)"' if arrow else ""
        self.add('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s"%s%s/>' % (" ".join(f"{a},{b}" for a, b in pts), stroke, sw, d, m))

    def etiqueta(self, x, y, s, size=12, fill=INK, bold=False):
        ancho = len(s) * size * 0.56 + 10
        self.add(f'<rect x="{x - ancho / 2:.1f}" y="{y - size - 1}" width="{ancho:.1f}" height="{size + 7}" rx="4" fill="white" opacity="0.95"/>')
        self.text(x, y, s, size, fill, bold, "middle")

    def svg(self):
        cab = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
               f'font-family="{FONT}"><defs><marker id="flecha" markerWidth="11" markerHeight="11" refX="9" refY="5.5" orient="auto">'
               f'<path d="M1,1 L10,5.5 L1,10 z" fill="{INK}"/></marker></defs>'
               f'<rect width="{self.w}" height="{self.h}" fill="white"/>')
        return cab + "".join(self.p) + "</svg>"


class Caja:
    def __init__(self, nombre, x, y, w, tipos=False):
        self.n, self.x, self.y, self.w, self.tipos = nombre, x, y, w, tipos
        self.filas = TABLAS[nombre]
        self.nota = NOTAS.get(nombre)
        self.h = 36 + len(self.filas) * 23 + 12 + (20 if self.nota else 0)

    def dibujar(self, c):
        x, y, w, h = self.x, self.y, self.w, self.h
        c.rect(x, y, w, h, "white", INK, 1.8, 10)
        c.add(f'<path d="M{x},{y + 36} V{y + 10} Q{x},{y} {x + 10},{y} H{x + w - 10} Q{x + w},{y} {x + w},{y + 10} V{y + 36} Z" fill="{INK}"/>')
        c.text(x + 14, y + 24, self.n.upper(), 15, "white", True)
        for i, (tag, col, tipo) in enumerate(self.filas):
            yy = y + 36 + 18 + i * 23
            if tag:
                fondo = LIME if tag.startswith("PK") else "#E5E7EB"
                c.rect(x + 10, yy - 13, 44, 17, fondo, "none", 0, 8)
                c.text(x + 32, yy, tag, 10.5, INK, True, "middle")
            c.text(x + 62, yy, col, 13, INK, tag.startswith("PK"))
            if self.tipos:
                c.text(x + w - 12, yy, tipo, 11.5, GRAY, False, "end")
        if self.nota:
            c.text(x + 14, y + h - 9, self.nota, 11, GREEN, False, "start", True)

    def der(self, dy): return (self.x + self.w, self.y + dy)
    def izq(self, dy): return (self.x, self.y + dy)
    def sup(self, dx): return (self.x + dx, self.y)
    def inf(self, dx): return (self.x + dx, self.y + self.h)


def marca(c, p, d, texto):
    """Texto de cardinalidad junto al extremo p; d = dirección (dx, dy) alejándose del extremo."""
    x, y = p[0] + d[0] * 20 + (-d[1]) * 13, p[1] + d[1] * 20 + d[0] * 13
    if d[1] != 0:
        x, y = p[0] + 17, p[1] + d[1] * 17 + 4
    else:
        y = p[1] - 8
        x = p[0] + d[0] * 24
    c.text(x, y, texto, 12.5, GREEN, True, "middle")


def posiciones(w, tipos):
    cx = [50, 460, 870] if w == 310 else [50, 470, 890]
    cajas = {}
    for n, (col, fila) in {"usuario": (0, 0), "conductor": (1, 0), "vehiculo": (2, 0), "solicitud": (0, 1), "oferta": (1, 1),
                           "viaje": (2, 1), "calificacion": (1, 2), "pago": (2, 2)}.items():
        cajas[n] = Caja(n, cx[col], [30, 270, 530][fila], w, tipos)
    return cajas


# ---------------------------------------------------------------- figuras
def er():
    c = Lienzo(1230, 760)
    b = posiciones(310, False)
    u, d, v, s, o, vi, pa, ca = (b[k] for k in ["usuario", "conductor", "vehiculo", "solicitud", "oferta", "viaje", "pago", "calificacion"])
    # líneas (padre -> hijo) con nombre y cardinalidades
    lineas = [
        ([u.der(60), d.izq(60)], "puede ser", "1", "0..1", (1, 0), (-1, 0)),
        ([d.der(60), v.izq(60)], "posee", "1", "0..N", (1, 0), (-1, 0)),
        ([u.inf(155), s.sup(155)], "solicita", "1", "0..N", (0, 1), (0, -1)),
        ([s.der(60), o.izq(60)], "recibe", "1", "0..N", (1, 0), (-1, 0)),
        ([v.inf(60), (v.x + 60, 240), (o.x + 250, 240), o.sup(250)], "presenta", "1", "0..N", (0, 1), (0, -1)),
        ([o.der(60), vi.izq(60)], "origina", "1", "0..1", (1, 0), (-1, 0)),
        ([vi.inf(235), pa.sup(235)], "registra", "1", "0..1", (0, 1), (0, -1)),
        ([vi.inf(60), (vi.x + 60, 500), (ca.x + 250, 500), ca.sup(250)], "recibe", "1", "0..N", (0, 1), (0, -1)),
        ([u.izq(100), (20, u.y + 100), (20, ca.y + 80), ca.izq(80)], "emite", "1", "0..N", (-1, 0), (1, 0)),
    ]
    for pts, nombre, a, bb, da, db in lineas:
        c.poly(pts, INK, 1.7)
        # nombre de la relación en el punto medio del segmento más largo
        seg = max(range(len(pts) - 1), key=lambda i: abs(pts[i][0] - pts[i + 1][0]) + abs(pts[i][1] - pts[i + 1][1]))
        mx, my = (pts[seg][0] + pts[seg + 1][0]) / 2, (pts[seg][1] + pts[seg + 1][1]) / 2
        if nombre == "emite":
            mx, my = 235, ca.y + 80
        c.etiqueta(mx, my + 4, nombre, 12, GRAY)
        pa_, pb_ = pts[0], pts[-1]
        # dirección de salida de cada extremo
        d0 = (pts[1][0] - pa_[0], pts[1][1] - pa_[1]); n0 = max(abs(d0[0]), abs(d0[1])) or 1
        d1 = (pts[-2][0] - pb_[0], pts[-2][1] - pb_[1]); n1 = max(abs(d1[0]), abs(d1[1])) or 1
        marca(c, pa_, (d0[0] / n0, d0[1] / n0), a)
        marca(c, pb_, (d1[0] / n1, d1[1] / n1), bb)
    for x in b.values():
        x.dibujar(c)
    c.text(50, 745, "PK = clave primaria · FK = clave foránea · UK = clave única. Cardinalidades: 1, 0..1 y 0..N en cada extremo; toda FK es obligatoria (NOT NULL).", 12, GRAY)
    return c


def logico():
    c = Lienzo(1260, 760)
    b = posiciones(330, True)
    u, d, v, s, o, vi, pa, ca = (b[k] for k in ["usuario", "conductor", "vehiculo", "solicitud", "oferta", "viaje", "pago", "calificacion"])
    flechas = [
        [d.izq(60), u.der(60)], [v.izq(60), d.der(60)], [s.sup(155), u.inf(155)], [o.izq(60), s.der(60)],
        [o.sup(270), (o.x + 270, 240), (v.x + 60, 240), v.inf(60)], [vi.izq(60), o.der(60)], [pa.sup(255), vi.inf(255)],
        [ca.sup(270), (ca.x + 270, 500), (vi.x + 60, 500), vi.inf(60)],
        [ca.izq(80), (20, ca.y + 80), (20, u.y + 100), u.izq(100)],
    ]
    for pts in flechas:
        c.poly(pts, INK, 1.7, arrow=True)
    for x in b.values():
        x.dibujar(c)
    c.text(50, 745, "Las flechas van de la FK (hija) hacia la PK (padre). Las nueve FK usan ON DELETE RESTRICT y ON UPDATE RESTRICT. Solo hora_inicio y hora_fin admiten NULL.", 12, GRAY)
    return c


def eer():
    c = Lienzo(860, 610)
    u = Caja("usuario", 20, 40, 270, False)
    d = Caja("conductor", 570, 40, 270, False)
    u.dibujar(c); d.dibujar(c)
    cx, cy = 430, 100
    c.poly([(u.x + u.w, cy), (cx - 30, cy)], INK, 1.8)          # línea simple = participación parcial
    c.add(f'<circle cx="{cx}" cy="{cy}" r="30" fill="{LIME}" stroke="{INK}" stroke-width="1.8"/>')
    c.text(cx, cy + 4, "parcial", 11, INK, True, "middle")
    c.poly([(cx + 30, cy), (d.x, cy)], INK, 1.8)
    c.text(515, cy - 8, "⊂", 22, INK, True, "middle")            # el subtipo es subconjunto de la superclase
    c.text(cx, cy - 46, "ESPECIALIZACIÓN PARCIAL", 12.5, GREEN, True, "middle")
    c.text(cx, cy + 52, "un solo subtipo representado", 12, GRAY, False, "middle")
    c.text(cx, cy + 69, "(sin disyunción que declarar)", 12, GRAY, False, "middle")
    s_ = Caja("solicitud", 20, 300, 270, False)
    s_.dibujar(c)
    c.rect(330, 330, 200, 60, "white", GREEN, 1.8, 30, "7 5")
    c.text(430, 356, "ROL: pasajero", 14, GREEN, True, "middle")
    c.text(430, 375, "quien crea una solicitud", 11.5, GRAY, False, "middle")
    c.poly([(s_.x + s_.w, 360), (330, 360)], GREEN, 1.6, dash="6 5")
    c.poly([(430, 330), (430, u.y + u.h + 34), (u.x + 135, u.y + u.h + 34), (u.x + 135, u.y + u.h)], GREEN, 1.6, dash="6 5")
    c.text(430, 414, "No es un subtipo: el rol surge", 12, GRAY, False, "middle")
    c.text(430, 431, "de la FK Solicitud.id_usuario", 12, GRAY, False, "middle")
    c.rect(560, 300, 280, 175, SOFT, "none", 0, 12)
    c.text(578, 328, "Cómo se implementa", 13.5, INK, True)
    for i, linea in enumerate(["Conductor.id_usuario:", "· FK, UNIQUE y NOT NULL", "· cada conductor = un usuario",
                               "· un usuario: máximo un perfil", "· hay usuarios sin perfil de conductor",
                               "id_conductor se conserva como PK."]):
        c.text(578, 354 + i * 20, linea, 12, INK if i == 0 else GRAY, i == 0)
    c.text(20, 568, "Notación: línea simple = especialización parcial; ⊂ = el subtipo es un subconjunto de la", 12, GRAY)
    c.text(20, 586, "superclase; línea punteada = rol, no una tabla nueva.", 12, GRAY)
    return c


def arquitectura():
    c = Lienzo(860, 600)
    bloques = [
        (20, "NAVEGADOR", ["React 18.3.1", "Vite 6.4.4", "9 módulos de operación", "+ Explorador BD", "+ Consultas SQL"]),
        (320, "SERVIDOR", ["Express 4.22.3", "Node.js ≥ 20.19", "validate() de entradas", "helper transaction()", "catálogo de 6 consultas"]),
        (620, "BASE DE DATOS", ["MySQL 8.0.44 · InnoDB", "8 tablas · 9 FK RESTRICT", "15 CHECK · 18 triggers", "utf8mb4", "INFORMATION_SCHEMA"]),
    ]
    for x, t, filas in bloques:
        c.rect(x, 30, 220, 205, "white", INK, 1.8, 14)
        c.add(f'<path d="M{x},{30 + 40} V{44} Q{x},30 {x + 14},30 H{x + 206} Q{x + 220},30 {x + 220},44 V{70} Z" fill="{INK}"/>')
        c.text(x + 110, 57, t, 14.5, LIME, True, "middle")
        for i, f in enumerate(filas):
            c.text(x + 16, 96 + i * 29, f, 13.5, INK, i == 0)
    for x1, x2, a, b_ in [(240, 320, "HTTP·JSON", "/api/…"), (540, 620, "mysql2", "pool de 8")]:
        c.poly([(x1 + 4, 110), (x2 - 4, 110)], INK, 2, arrow=True)
        c.poly([(x2 - 4, 150), (x1 + 4, 150)], INK, 2, arrow=True)
        c.text((x1 + x2) / 2, 98, a, 10.5, GRAY, True, "middle")
        c.text((x1 + x2) / 2, 172, b_, 10.5, GRAY, False, "middle")
    c.rect(20, 262, 820, 92, SOFT, "none", 0, 14)
    c.text(40, 292, "ENTORNO DE EJECUCIÓN", 13.5, GREEN, True)
    c.text(40, 318, "Docker Compose: servicios db · setup · app", 13, INK)
    c.text(40, 340, "Puertos solo en loopback (app 3000 · MySQL 3307). Sin autenticación: demostración local.", 13, GRAY)
    c.rect(20, 380, 820, 124, "white", GREEN, 1.8, 14, "7 5")
    c.text(40, 410, "GitHub Actions (ci.yml, en push y pull_request)", 13.5, GREEN, True)
    c.text(40, 438, "verify: npm ci → npm test → build → db:init (2 veces) → API e integración (MySQL 8.0.44)", 12.5, INK)
    c.text(40, 462, "container: docker compose up --build --wait → /api/health", 12.5, INK)
    c.text(40, 486, "Ambos jobs se ejecutan en cada push y en cada pull request.", 12.5, GRAY)
    c.text(20, 534, "El navegador nunca habla con MySQL: solo el servidor ejecuta SQL.", 12, GRAY)
    c.text(20, 552, "Los usuarios no tienen consola libre, únicamente las consultas del catálogo.", 12, GRAY)
    return c


def flujo():
    c = Lienzo(940, 540)
    pasos = [("1", "Solicitud", "estado «abierta»", "el pasajero propone origen, destino y precio"),
             ("2", "Ofertas", "0..N por solicitud", "un vehículo ofrece monto y minutos de llegada"),
             ("3", "Aceptación", "una transacción", "INSERT en viaje; la solicitud pasa a «aceptada»"),
             ("4", "Viaje en curso", "hora_inicio", "estado: pendiente → en_curso"),
             ("5", "Viaje finalizado", "hora_fin", "estado: en_curso → finalizado"),
             ("6", "Cierre", "tras finalizar", "1 pago por viaje; hasta 2 calificaciones")]
    w, h, g = 260, 150, 50
    pos = []
    for i, (n, t, sub, desc) in enumerate(pasos):
        x, y = 30 + (i % 3) * (w + g), 30 + (i // 3) * 220
        pos.append((x, y))
        c.rect(x, y, w, h, "white", INK, 1.8, 14)
        c.add(f'<circle cx="{x + 30}" cy="{y + 32}" r="16" fill="{LIME}" stroke="{INK}" stroke-width="1.5"/>')
        c.text(x + 30, y + 38, n, 15, INK, True, "middle")
        c.text(x + 56, y + 38, t, 16.5, INK, True)
        c.text(x + 16, y + 76, sub, 13, GREEN, True)
        palabras, lineas, cur = desc.split(), [], ""
        for pl in palabras:
            if len(cur) + len(pl) + 1 > 31:
                lineas.append(cur); cur = pl
            else:
                cur = (cur + " " + pl).strip()
        lineas.append(cur)
        for j, l in enumerate(lineas):
            c.text(x + 16, y + 102 + j * 19, l, 13, GRAY)
    for i in (0, 1, 3, 4):
        x, y = pos[i]
        c.poly([(x + w + 4, y + 75), (x + w + g - 4, y + 75)], INK, 2, arrow=True)
    x3, y3 = pos[2]; x4, y4 = pos[3]
    c.poly([(x3 + w / 2, y3 + h), (x3 + w / 2, y3 + h + 35), (x4 + w / 2, y3 + h + 35), (x4 + w / 2, y4)], INK, 2, arrow=True)
    c.rect(30, 432, 880, 56, SOFT, "none", 0, 12)
    c.text(46, 456, "Alternativa en el paso 1: la solicitud puede pasar a «cancelada» mientras esté abierta;", 13, INK, True)
    c.text(46, 476, "sus ofertas se conservan.", 13, GRAY)
    c.text(30, 520, "Todo el historial (viajes, pagos, calificaciones) se conserva: FK RESTRICT y triggers.", 12, GRAY)
    return c


def transaccion():
    c = Lienzo(820, 640)
    A, B = 20, 460
    for x, t, s_ in [(A, "Cliente A", "POST /api/offers/7/accept"), (B, "Cliente B", "POST /api/offers/8/accept (misma solicitud)")]:
        c.rect(x, 20, 340, 56, INK, INK, 1, 12)
        c.text(x + 16, 45, t, 15, LIME, True)
        c.text(x + 16, 65, s_, 12, "white")
        c.poly([(x + 170, 76), (x + 170, 610)], "#9CA3AF", 1.5, dash="5 5")
    filas = [
        (100, "BEGIN", True, "BEGIN", False),
        (160, "SELECT estado FROM solicitud\nWHERE id_solicitud=? FOR UPDATE", False, "SELECT … FOR UPDATE", False),
        (250, "estado = 'abierta'  ✓", False, "espera el bloqueo de la fila…", True),
        (330, "INSERT INTO viaje (id_oferta)\ntrigger viaje_ai → solicitud 'aceptada'", False, "", False),
        (420, "COMMIT  →  201 Created", True, "lee estado = 'aceptada'", False),
        (500, "", False, "409 «La solicitud ya no está abierta»", True),
        (560, "", False, "ROLLBACK", False),
    ]
    for y, a, ab, b_, bb in filas:
        if a:
            lineas = a.split("\n")
            c.rect(A + 10, y, 320, 20 + 18 * len(lineas), SOFT, "none", 0, 8)
            for j, l in enumerate(lineas):
                c.text(A + 24, y + 22 + j * 18, l, 12.5, INK, ab and j == 0)
        if b_:
            fondo = "#FDE68A" if y == 250 else SOFT
            c.rect(B + 10, y, 320, 40, fondo, "none", 0, 8)
            c.text(B + 24, y + 25, b_, 12.5, INK, bb)
    c.poly([(A + 330, 182), (B + 10, 182)], GREEN, 1.8, arrow=True, dash="6 4")
    c.text(410, 172, "mismo instante", 10.5, GREEN, True, "middle")
    c.poly([(A + 330, 440), (B + 10, 440)], GREEN, 1.8, arrow=True)
    c.text(410, 430, "libera el bloqueo", 10.5, GREEN, True, "middle")
    c.text(20, 632, "Comprobado por tests/api.integration.js: dos aceptaciones simultáneas devuelven [201, 409].", 11.5, GRAY)
    return c


FIGURAS = {"er": er, "logico": logico, "eer": eer, "arquitectura": arquitectura, "flujo": flujo, "transaccion": transaccion}


def chrome():
    ruta = os.environ.get("CHROME")
    if ruta and os.path.exists(ruta):
        return ruta
    c = glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell"))
    return c[0] if c else None


def main():
    t, f = verificar_contra_ddl()
    print(f"DDL coincide con el modelo del diagrama: {t} tablas, {f} claves foráneas")
    ch = chrome()
    for nombre, fn in FIGURAS.items():
        lienzo = fn()
        svg = OUT / f"{nombre}.svg"
        svg.write_text(lienzo.svg(), encoding="utf8")
        if ch:
            png = OUT / f"{nombre}.png"
            subprocess.run([ch, "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                            f"--window-size={lienzo.w},{lienzo.h}", f"--screenshot={png}", svg.as_uri()],
                           check=True, capture_output=True)
        print("OK", nombre, f"{lienzo.w}x{lienzo.h}")
    if not ch:
        print("Sin Chromium: solo se generaron los SVG", file=sys.stderr)


if __name__ == "__main__":
    main()
