#!/usr/bin/env python3
"""Genera (por la salida estándar) el SQL del conjunto de demostración de inDrive Lab.

* Datos 100 % ficticios: correos @demo.indrive-lab.test, teléfonos secuenciales, placas inventadas.
* Rutas entre puntos conocidos de Lima; precios en soles (S/).
* Determinista (semilla fija): siempre produce el mismo conjunto de 500 solicitudes.
* No altera el esquema ni borra nada: solo INSERT y los UPDATE que exigen los triggers
  (viaje pendiente -> en_curso -> finalizado, solicitud abierta -> cancelada).
* Todo ocurre en UNA transacción: o se cargan las 500 solicitudes o no se carga nada.

La idempotencia la garantiza cargar-demo.sh (no ejecuta este SQL si el conjunto ya existe).
"""
import math
import random

SEED = 20261114
N_SOLICITUDES = 500
DOMINIO = 'demo.indrive-lab.test'
N_PASAJEROS, N_CONDUCTORES, N_VEHICULOS = 150, 40, 60

# (categoria, cantidad) -> suman 500
CATEGORIAS = [
    ('sin_ofertas', 110), ('abierta_con_ofertas', 130), ('cancelada', 40),
    ('viaje_pendiente', 40), ('viaje_en_curso', 30), ('viaje_finalizado', 150),
]

LUGARES = [  # (nombre, lat, lon)
    ('Aeropuerto Internacional Jorge Chávez, Callao', -12.0219, -77.1143),
    ('Plaza San Miguel, San Miguel', -12.0773, -77.0833),
    ('Parque Kennedy, Miraflores', -12.1219, -77.0297),
    ('Larcomar, Miraflores', -12.1317, -77.0300),
    ('Plaza Mayor de Lima, Cercado de Lima', -12.0464, -77.0300),
    ('Estación Central, Cercado de Lima', -12.0553, -77.0373),
    ('Jockey Plaza, Santiago de Surco', -12.0846, -76.9753),
    ('Real Plaza Salaverry, Jesús María', -12.0897, -77.0509),
    ('Campo de Marte, Jesús María', -12.0700, -77.0430),
    ('Plaza Norte, Independencia', -11.9944, -77.0613),
    ('Parque de Barranco, Barranco', -12.1403, -77.0206),
    ('Óvalo Gutiérrez, Miraflores', -12.1130, -77.0360),
    ('Centro Empresarial, San Isidro', -12.0950, -77.0360),
    ('Parque El Olivar, San Isidro', -12.1000, -77.0360),
    ('Plaza Matriz, Chorrillos', -12.1680, -77.0140),
    ('Estadio Nacional, Cercado de Lima', -12.0674, -77.0334),
    ('Plaza Bolognesi, Breña', -12.0560, -77.0430),
    ('Plaza Dos de Mayo, Cercado de Lima', -12.0527, -77.0430),
    ('Mall del Sur, San Juan de Miraflores', -12.1530, -76.9700),
    ('Galería comercial Gamarra, La Victoria', -12.0680, -77.0113),
    ('Plaza de Armas de Pueblo Libre, Pueblo Libre', -12.0720, -77.0630),
    ('Plaza San Martín, Cercado de Lima', -12.0517, -77.0338),
    ('Real Plaza Primavera, Santiago de Surco', -12.1100, -76.9920),
    ('Plaza de Armas de Magdalena, Magdalena del Mar', -12.0900, -77.0720),
    ('Hospital Rebagliati, Jesús María', -12.0770, -77.0450),
    ('Parque Zonal Huiracocha, San Juan de Lurigancho', -12.0000, -76.9990),
    ('Playa Makaha, Miraflores', -12.1260, -77.0390),
    ('Universidad Norbert Wiener, Cercado de Lima', -12.0578, -77.0399),
]
NOMBRES = ['Valeria', 'Mateo', 'Camila', 'Joaquín', 'Lucía', 'Renzo', 'Ximena', 'Matías', 'Daniela', 'Gael',
           'Fabiola', 'Álvaro', 'Milagros', 'Sebastián', 'Romina', 'Bruno', 'Alejandra', 'Thiago', 'Paola', 'Adrián',
           'Nicole', 'Hugo', 'Isabella', 'Emilio', 'Mariana', 'Lorenzo', 'Andrea', 'Gonzalo', 'Rosario', 'Ismael']
APELLIDOS = ['Aguilar', 'Bustamante', 'Cárdenas', 'Delgado', 'Espinoza', 'Fernández', 'Galarza', 'Huamán', 'Ibarra',
             'Jiménez', 'Landa', 'Maldonado', 'Núñez', 'Olivera', 'Paredes', 'Quiroz', 'Rivas', 'Salazar', 'Tapia',
             'Uribe', 'Valdivia', 'Yupanqui', 'Zevallos', 'Alarcón', 'Benavides', 'Cornejo', 'Dávila', 'Escobar',
             'Farfán', 'Guerra']
AUTOS = [('Toyota', 'Yaris'), ('Hyundai', 'Accent'), ('Kia', 'Rio'), ('Nissan', 'Versa'), ('Suzuki', 'Swift'),
         ('Chevrolet', 'Sail'), ('Hyundai', 'Grand i10'), ('Kia', 'Picanto'), ('Toyota', 'Corolla'),
         ('Mitsubishi', 'Mirage')]
COLORES = ['Blanco', 'Plata', 'Negro', 'Gris', 'Rojo', 'Azul']
COMENT_PASAJERO = ['Viaje tranquilo y puntual.', 'Conductor amable, auto limpio.', 'Llegó rápido al punto de recojo.',
                   'Buen trato durante el recorrido.', 'Ruta eficiente, sin contratiempos.', 'Todo conforme.', '']
COMENT_CONDUCTOR = ['Pasajero puntual.', 'Buena comunicación.', 'Sin inconvenientes.', 'Muy cordial.', '']


def q(s):
    return "'" + str(s).replace('\\', '\\\\').replace("'", "''") + "'"


def km(a, b):
    r = 6371
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[2], b[1], b[2]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h)) * 1.3  # factor de rodeo urbano


def medio_sol(x):
    return round(round(x * 2) / 2, 2)


def main():
    rnd = random.Random(SEED)
    out = []
    w = out.append

    # --- personas -----------------------------------------------------------------------------
    combos = [(n, a) for n in NOMBRES for a in APELLIDOS]
    rnd.shuffle(combos)
    pasajeros = []   # (nombres, telefono, correo)
    for i in range(1, N_PASAJEROS + 1):
        n, a = combos.pop()
        pasajeros.append((f'{n} {a}', f'+51900{i:06d}', f'pasajero{i:03d}@{DOMINIO}'))
    conductores = []
    for i in range(1, N_CONDUCTORES + 1):
        n, a = combos.pop()
        conductores.append((f'{n} {a}', f'+51900{1000 + i:06d}', f'conductor{i:03d}@{DOMINIO}', f'QD{i:07d}'))
    placas, vehiculos = set(), []   # placa, correo_conductor, marca, modelo, color, anio
    letras = 'BCDFGHJKLMNPRSTVWXYZ'
    for i in range(N_VEHICULOS):
        while True:
            p = f'D{rnd.choice(letras)}{rnd.choice(letras)}-{rnd.randint(100, 999)}'
            if p not in placas:
                placas.add(p)
                break
        dueno = conductores[i % N_CONDUCTORES][2]
        marca, modelo = rnd.choice(AUTOS)
        vehiculos.append((p, dueno, marca, modelo, rnd.choice(COLORES), rnd.randint(2015, 2024)))

    # --- plan de solicitudes ---------------------------------------------------------------------
    cats = [c for c, k in CATEGORIAS for _ in range(k)]
    assert len(cats) == N_SOLICITUDES
    rnd.shuffle(cats)
    sols, ofs, trips = [], [], []
    for n, cat in enumerate(cats, 1):
        pas = pasajeros[rnd.randrange(N_PASAJEROS)]
        o, d = rnd.sample(LUGARES, 2)
        dist = km(o, d)
        precio = max(6.0, medio_sol((4 + 1.6 * dist) * rnd.uniform(0.9, 1.2)))
        hace = rnd.randint(400, 60000) if cat.startswith('viaje') else rnd.randint(5, 60000)
        sols.append((n, pas[2], o[0], d[0], precio, hace, cat))
        n_of = {'sin_ofertas': 0, 'abierta_con_ofertas': rnd.randint(1, 3), 'cancelada': rnd.randint(0, 2)}.get(cat, rnd.randint(1, 3))
        elegidas = rnd.sample(vehiculos, n_of)
        ganador = rnd.randrange(n_of) if cat.startswith('viaje') else -1
        etas = []
        for k, v in enumerate(elegidas):
            eta = rnd.randint(2, 25)
            etas.append(eta)
            monto = max(5.0, medio_sol(precio * rnd.uniform(0.85, 1.25)))
            ofs.append((n, k, v[0], monto, eta, 1 if k == ganador else 0))
        if cat.startswith('viaje'):
            eta = etas[ganador]
            inicio_hace = hace - eta - rnd.randint(3, 10)
            dur = int(dist * 3) + rnd.randint(5, 15)
            fin_hace = inicio_hace - dur
            metodo = rnd.choices(['efectivo', 'tarjeta', 'transferencia'], [5, 2, 3])[0]
            c_punt = rnd.choice([3, 4, 4, 5, 5, 5])
            p_punt = rnd.choice([3, 4, 5, 5, 5]) if rnd.random() < .7 else None
            final = {'viaje_pendiente': 'pendiente', 'viaje_en_curso': 'en_curso', 'viaje_finalizado': 'finalizado'}[cat]
            trips.append((n, final, inicio_hace, fin_hace, metodo, c_punt, rnd.choice(COMENT_PASAJERO), p_punt, rnd.choice(COMENT_CONDUCTOR)))
            assert fin_hace >= 5 and inicio_hace > fin_hace

    # --- SQL ---------------------------------------------------------------------------------------
    w('-- Generado por generar_demo_sql.py (semilla %d). Datos ficticios; no usar en producción.' % SEED)
    w('SET NAMES utf8mb4;\nUSE indrive_academico;\nSTART TRANSACTION;\nSET @ahora = NOW();')
    w('SET @max_sol = (SELECT COALESCE(MAX(id_solicitud),0) FROM solicitud);')
    w('INSERT INTO usuario (nombres,telefono,correo,fecha_registro) VALUES')
    filas = [f'({q(n)},{q(t)},{q(c)},@ahora - INTERVAL {rnd.randint(61, 400)} DAY)' for n, t, c in pasajeros]
    filas += [f'({q(n)},{q(t)},{q(c)},@ahora - INTERVAL {rnd.randint(61, 400)} DAY)' for n, t, c, _ in conductores]
    w(',\n'.join(filas) + ';')
    w('CREATE TEMPORARY TABLE demo_cond (correo VARCHAR(160), licencia VARCHAR(20));')
    w('INSERT INTO demo_cond VALUES ' + ','.join(f'({q(c)},{q(l)})' for _, _, c, l in conductores) + ';')
    w('INSERT INTO conductor (id_usuario,licencia) SELECT u.id_usuario,d.licencia FROM demo_cond d JOIN usuario u ON u.correo=d.correo ORDER BY d.licencia;')
    w('CREATE TEMPORARY TABLE demo_veh (placa VARCHAR(10), correo VARCHAR(160), marca VARCHAR(50), modelo VARCHAR(60), color VARCHAR(30), anio SMALLINT);')
    w('INSERT INTO demo_veh VALUES ' + ','.join(f'({q(p)},{q(c)},{q(m)},{q(mo)},{q(co)},{a})' for p, c, m, mo, co, a in vehiculos) + ';')
    w('INSERT INTO vehiculo (placa,id_conductor,marca,modelo,color,anio) SELECT v.placa,c.id_conductor,v.marca,v.modelo,v.color,v.anio FROM demo_veh v JOIN usuario u ON u.correo=v.correo JOIN conductor c ON c.id_usuario=u.id_usuario ORDER BY v.placa;')

    w('CREATE TEMPORARY TABLE demo_sol (n INT PRIMARY KEY, correo VARCHAR(160), origen VARCHAR(200), destino VARCHAR(200), precio DECIMAL(10,2), hace INT, categoria VARCHAR(30));')
    for i in range(0, len(sols), 100):
        w('INSERT INTO demo_sol VALUES ' + ','.join(f'({n},{q(c)},{q(o)},{q(d)},{p:.2f},{h},{q(k)})' for n, c, o, d, p, h, k in sols[i:i + 100]) + ';')
    w('INSERT INTO solicitud (id_usuario,origen,destino,precio_ofrecido,fecha_solicitud) SELECT u.id_usuario,s.origen,s.destino,s.precio,@ahora - INTERVAL s.hace MINUTE FROM demo_sol s JOIN usuario u ON u.correo=s.correo ORDER BY s.n;')
    w('CREATE TEMPORARY TABLE demo_map (n INT PRIMARY KEY, id_solicitud INT NOT NULL);')
    w('INSERT INTO demo_map SELECT ROW_NUMBER() OVER (ORDER BY id_solicitud),id_solicitud FROM solicitud WHERE id_solicitud > @max_sol;')

    w('CREATE TEMPORARY TABLE demo_of (n INT, k INT, placa VARCHAR(10), monto DECIMAL(10,2), eta SMALLINT, aceptada TINYINT, PRIMARY KEY (n,k));')
    for i in range(0, len(ofs), 100):
        w('INSERT INTO demo_of VALUES ' + ','.join(f'({n},{k},{q(p)},{m:.2f},{e},{a})' for n, k, p, m, e, a in ofs[i:i + 100]) + ';')
    w('INSERT INTO oferta (id_solicitud,placa,monto,tiempo_llegada) SELECT m.id_solicitud,d.placa,d.monto,d.eta FROM demo_of d JOIN demo_map m ON m.n=d.n ORDER BY d.n,d.k;')
    w('CREATE TEMPORARY TABLE demo_ofmap (n INT, k INT, id_oferta INT, aceptada TINYINT);')
    w('INSERT INTO demo_ofmap SELECT d.n,d.k,o.id_oferta,d.aceptada FROM demo_of d JOIN demo_map m ON m.n=d.n JOIN oferta o ON o.id_solicitud=m.id_solicitud AND o.placa=d.placa;')

    w("CREATE TEMPORARY TABLE demo_trip (n INT PRIMARY KEY, final VARCHAR(12), inicio_hace INT, fin_hace INT, metodo VARCHAR(15), c_punt TINYINT, c_com VARCHAR(500), p_punt TINYINT NULL, p_com VARCHAR(500));")
    for i in range(0, len(trips), 100):
        w('INSERT INTO demo_trip VALUES ' + ','.join(
            f'({n},{q(f)},{ih},{fh},{q(me)},{cp},{q(cc)},{"NULL" if pp is None else pp},{q(pc)})'
            for n, f, ih, fh, me, cp, cc, pp, pc in trips[i:i + 100]) + ';')
    # cancelación (solo solicitudes abiertas que ya pueden tener ofertas)
    w("UPDATE solicitud s JOIN demo_map m ON m.id_solicitud=s.id_solicitud JOIN demo_sol d ON d.n=m.n SET s.estado='cancelada' WHERE d.categoria='cancelada';")
    # viajes: se crean pendientes; el trigger viaje_ai marca la solicitud como aceptada
    w('INSERT INTO viaje (id_oferta) SELECT m.id_oferta FROM demo_ofmap m JOIN demo_trip t ON t.n=m.n WHERE m.aceptada=1 ORDER BY m.n;')
    w("UPDATE viaje v JOIN demo_ofmap m ON m.id_oferta=v.id_oferta AND m.aceptada=1 JOIN demo_trip t ON t.n=m.n SET v.estado='en_curso',v.hora_inicio=@ahora - INTERVAL t.inicio_hace MINUTE WHERE t.final IN ('en_curso','finalizado');")
    w("UPDATE viaje v JOIN demo_ofmap m ON m.id_oferta=v.id_oferta AND m.aceptada=1 JOIN demo_trip t ON t.n=m.n SET v.estado='finalizado',v.hora_fin=@ahora - INTERVAL t.fin_hace MINUTE WHERE t.final='finalizado';")
    # Los triggers de pago/calificacion hacen SELECT ... FOR UPDATE sobre viaje; MySQL (error 1442) no permite
    # que la sentencia lectora también use esa tabla. Por eso se materializan primero en tablas temporales.
    w("CREATE TEMPORARY TABLE demo_pago (id_viaje INT, metodo VARCHAR(15), monto DECIMAL(10,2), comision DECIMAL(10,2), fecha_pago DATETIME);")
    w("INSERT INTO demo_pago SELECT v.id_viaje,t.metodo,o.monto,ROUND(o.monto*0.10,2),v.hora_fin + INTERVAL 2 MINUTE FROM demo_trip t JOIN demo_ofmap m ON m.n=t.n AND m.aceptada=1 JOIN oferta o ON o.id_oferta=m.id_oferta JOIN viaje v ON v.id_oferta=o.id_oferta WHERE t.final='finalizado';")
    w("INSERT INTO pago (id_viaje,metodo,monto,comision,fecha_pago) SELECT id_viaje,metodo,monto,comision,fecha_pago FROM demo_pago ORDER BY id_viaje;")
    # el pasajero califica al conductor (siempre) y el conductor al pasajero (a veces)
    w("CREATE TEMPORARY TABLE demo_cal (id_viaje INT, id_usuario INT, puntaje TINYINT, comentario VARCHAR(500), autor_pasajero TINYINT);")
    w("INSERT INTO demo_cal SELECT v.id_viaje,s.id_usuario,t.c_punt,t.c_com,1 FROM demo_trip t JOIN demo_ofmap m ON m.n=t.n AND m.aceptada=1 JOIN oferta o ON o.id_oferta=m.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN viaje v ON v.id_oferta=o.id_oferta WHERE t.final='finalizado';")
    w("INSERT INTO demo_cal SELECT v.id_viaje,d.id_usuario,t.p_punt,t.p_com,0 FROM demo_trip t JOIN demo_ofmap m ON m.n=t.n AND m.aceptada=1 JOIN oferta o ON o.id_oferta=m.id_oferta JOIN vehiculo a ON a.placa=o.placa JOIN conductor d ON d.id_conductor=a.id_conductor JOIN viaje v ON v.id_oferta=o.id_oferta WHERE t.final='finalizado' AND t.p_punt IS NOT NULL;")
    w("INSERT INTO calificacion (id_viaje,id_usuario,puntaje,comentario) SELECT id_viaje,id_usuario,puntaje,comentario FROM demo_cal ORDER BY id_viaje,autor_pasajero DESC;")
    w('COMMIT;')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
