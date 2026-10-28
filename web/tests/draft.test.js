import {test} from 'node:test';
import assert from 'node:assert/strict';
import {buildDraft} from '../api/_draft.js';
import {validateNarration} from '../api/_lib.js';
test('Base de datos produce un borrador de 5 escenas válido',()=>{
 const r=buildDraft('Base de datos');
 assert.equal(r.isAI,false);
 assert.equal(r.source,'plantilla');
 assert.equal(r.scenes.length,5);
 assert.match(r.texto,/tabla|registro|consulta/i);
 assert.equal(validateNarration(r.texto),r.texto);
});
test('Acepta un término corto como DNS',()=>{
 const r=buildDraft('DNS');
 assert.equal(r.scenes.length,5);
 assert.equal(validateNarration(r.texto),r.texto);
});
test('Para temas desconocidos devuelve estructura explícitamente editable',()=>{
 const r=buildDraft('Qué es un sistema de pagos con terminal');
 assert.equal(r.scenes.length,5);
 assert.equal(r.isAI,false);
 assert.equal(validateNarration(r.texto),r.texto);
 assert.match(r.texto,/borrador inicial/);
});
test('Entradas inválidas se rechazan',()=>{
 for(const v of ['', 'ab', 'x'.repeat(351), null])assert.throws(()=>buildDraft(v));
});
test('Temas largos mantienen formato correcto',()=>{
 const r=buildDraft('Conoce sobre herramientas digitales '.repeat(9).slice(0,340));
 assert.equal(validateNarration(r.texto),r.texto);
});
