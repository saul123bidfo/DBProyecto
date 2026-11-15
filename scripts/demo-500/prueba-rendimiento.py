#!/usr/bin/env python3
"""Prueba de lectura HTTP contra inDrive Lab: 500 peticiones GET con validación de la respuesta.

Mide latencia, errores y tiempo total. IMPORTANTE: 500 peticiones correctas NO equivalen a
500 usuarios simultáneos. Se ejecutan dos pasadas:
  1) secuencial: 500 peticiones una tras otra (1 cliente);
  2) concurrente: las mismas 500 con N hilos (por defecto 10 clientes simultáneos).
Solo lectura. Uso: python3 prueba-rendimiento.py [URL_BASE] [HILOS]
"""
import json
import statistics
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:3000'
HILOS = int(sys.argv[2]) if len(sys.argv) > 2 else 10
TOTAL = 500

RUTAS = ['/api/health', '/api/dashboard'] + \
    [f'/api/data/solicitud?page={p}' for p in range(1, 22)] + \
    [f'/api/data/oferta?page={p}' for p in range(1, 31)] + \
    [f'/api/data/viaje?page={p}' for p in range(1, 10)] + \
    [f'/api/data/pago?page={p}' for p in range(1, 8)] + \
    ['/api/data/usuario?page=1', '/api/data/conductor?page=1', '/api/data/vehiculo?page=1', '/api/data/calificacion?page=1',
     '/api/data/solicitud?q=Miraflores', '/api/queries', '/api/explorer']


def peticion(i):
    ruta = RUTAS[i % len(RUTAS)]
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(BASE + ruta, timeout=30) as r:
            cuerpo = json.load(r)
            ok = r.status == 200 and cuerpo is not None
            if ruta.startswith('/api/data/'):
                ok = ok and 'rows' in cuerpo and cuerpo['total'] >= 1
            error = None if ok else f'respuesta inválida (HTTP {r.status})'
    except Exception as e:  # noqa: BLE001
        ok, error = False, repr(e)
    return ruta, (time.perf_counter() - t) * 1000, ok, error


def pasada(nombre, hilos):
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=hilos) as ex:
        res = list(ex.map(peticion, range(TOTAL)))
    total = time.perf_counter() - t0
    lat = sorted(r[1] for r in res)
    errores = [r for r in res if not r[2]]
    p = lambda x: lat[min(len(lat) - 1, int(len(lat) * x))]  # noqa: E731
    print(f'--- {nombre} ({hilos} cliente(s) en paralelo) ---')
    print(f'peticiones: {len(res)} | correctas: {len(res) - len(errores)} | errores: {len(errores)}')
    print(f'tiempo total: {total:.2f} s | rendimiento: {len(res) / total:.1f} peticiones/s')
    print(f'latencia ms: min {lat[0]:.1f} | media {statistics.mean(lat):.1f} | mediana {statistics.median(lat):.1f} | p95 {p(0.95):.1f} | p99 {p(0.99):.1f} | máx {lat[-1]:.1f}')
    for e in errores[:5]:
        print('  ERROR', e[0], e[3])
    return len(errores)


if __name__ == '__main__':
    print(f'Inicio: {time.strftime("%Y-%m-%d %H:%M:%S")} | base {BASE} | rutas distintas: {len(RUTAS)}')
    fallos = pasada('Pasada 1 secuencial', 1) + pasada('Pasada 2 concurrente', HILOS)
    sys.exit(1 if fallos else 0)
