import {test} from 'node:test';
import assert from 'node:assert/strict';
import {startupError} from '../server/startup-errors.js';
test('diferencia puerto ocupado de MySQL apagado',()=>{
 assert.match(startupError({code:'EADDRINUSE'},{port:3010}),/3010.*ocupado/);
 assert.match(startupError({code:'ECONNREFUSED'},{dbPort:3307}),/MySQL.*3307/);
});
test('explica bloqueo del sandbox y no revela contraseñas de errores originales',()=>{
 assert.match(startupError({code:'EPERM'}),/fuera del sandbox/);
 const secret='clave-prueba-no-real';
 assert.ok(!startupError({code:'ER_ACCESS_DENIED_ERROR',message:secret}).includes(secret));
 assert.ok(!startupError({code:'UNKNOWN_ERROR',message:secret}).includes(secret));
});
