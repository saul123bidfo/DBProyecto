import {test} from 'node:test';
import assert from 'node:assert/strict';
import {validate} from '../server/entities.js';
import {splitSQL} from '../scripts/sql-parser.js';
import fs from 'node:fs';
test('rechaza inyección de tipos, puntajes fraccionarios y referencias inválidas',()=>{
 for(const body of [{id_viaje:1,id_usuario:2,puntaje:4.5},{id_viaje:0,id_usuario:2,puntaje:5},{id_viaje:1,id_usuario:[],puntaje:5},{id_viaje:'1 OR 1=1',id_usuario:2,puntaje:5}])assert.throws(()=>validate('calificacion',body));
});
test('valida importes positivos y precisión monetaria',()=>{for(const monto of [-1,0,1.111,Infinity])assert.throws(()=>validate('oferta',{id_solicitud:1,placa:'ABC-123',monto,tiempo_llegada:3}));assert.equal(validate('oferta',{id_solicitud:1,placa:'ABC-123',monto:'19.50',tiempo_llegada:'3'}).monto,19.5);});
test('no permite cambiar el autor al editar una calificación',()=>{assert.deepEqual(validate('calificacion',{id_usuario:999,id_viaje:999,puntaje:4,comentario:'Corregido'},true),{puntaje:4,comentario:'Corregido'});});
test('campos obligatorios y correo válidos',()=>{assert.throws(()=>validate('usuario',{nombres:' ',telefono:'1234567',correo:'a@b.test'}));assert.throws(()=>validate('usuario',{nombres:'Ana',telefono:'1234567',correo:'invalido'}));});
test('parser conserva cuerpos de triggers y separa los scripts completos',()=>{const schema=splitSQL(fs.readFileSync('database/01-schema.sql','utf8'));assert.equal(schema.filter(s=>s.startsWith('CREATE TABLE')).length,8);assert.equal(schema.filter(s=>s.startsWith('CREATE TRIGGER')).length,18);assert.ok(schema.find(s=>s.startsWith('CREATE TRIGGER viaje_bi')).includes("SIGNAL SQLSTATE '45000'"));assert.throws(()=>splitSQL('SELECT 1'));});
