import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {decodeFootprint,decodeModel,fingerprint,buildGeoTiff} from '../docs/assets/browser-builder.mjs';
const model=JSON.parse(await readFile(new URL('../docs/data/browser-model.json',import.meta.url),'utf8'));

test('LEB128 footprint rejects truncation/overflow/empty grid',()=>{
  assert.deepEqual([...decodeFootprint(Uint8Array.of(2,3,1),6)],[0,0,1,1,1,0]);
  assert.throws(()=>decodeFootprint(Uint8Array.of(128),6));
  assert.throws(()=>decodeFootprint(Uint8Array.of(7),6));
  assert.throws(()=>decodeFootprint(Uint8Array.of(1),0));
  assert.throws(()=>decodeFootprint(Uint8Array.of(2),6));
});

test('real frozen model has exact dimensions/count/fingerprint',async()=>{
  const decoded=decodeModel(model);assert.equal(decoded.positives.length,60068);
  assert.equal(decoded.fp.length,12279160);
  assert.equal(await fingerprint(model,decoded),model.prediction_sha256);
});

test('incorrect counts, duplicates/outside predictions, and SHA tampering fail closed',async()=>{
  assert.throws(()=>decodeModel({...model,width:1}));
  assert.throws(()=>decodeModel({...model,positive_pixels:model.positive_pixels+1}));
  const bad=Buffer.from(model.positive_indices_base64,'base64');bad.writeUInt32LE(0,0);
  assert.throws(()=>decodeModel({...model,positive_indices_base64:bad.toString('base64')}));
  await assert.rejects(()=>fingerprint({...model,prediction_sha256:'0'.repeat(64)},decodeModel(model)));
});

test('full uncompressed float32 classic TIFF has pinned sample type and EPSG',async()=>{
  const {bytes,filename}=await buildGeoTiff(model,'2026-10-02T19:00:00.000Z');
  assert.ok(filename.endsWith('-nan.tif'));assert.ok(filename.includes(model.prediction_sha256.slice(0,12)));
  const dv=new DataView(bytes.buffer);assert.equal(dv.getUint16(0,true),0x4949);assert.equal(dv.getUint16(2,true),42);
  const entries=dv.getUint16(8,true);const tags=new Map();
  for(let i=0;i<entries;i++){const offset=10+i*12;tags.set(dv.getUint16(offset,true),{type:dv.getUint16(offset+2,true),count:dv.getUint32(offset+4,true),value:dv.getUint32(offset+8,true)});}
  assert.equal(tags.get(256).value,3292);assert.equal(tags.get(257).value,3730);
  assert.equal(tags.get(258).value,32);assert.equal(tags.get(339).value,3);
  assert.equal(tags.get(277).value,1);assert.equal(tags.get(42113).value,0x006e616e);
  const geo=tags.get(34735).value;const keys=[];for(let i=0;i<20;i++)keys.push(dv.getUint16(geo+i*2,true));assert.ok(keys.includes(32611));
  assert.equal(bytes.length-tags.get(273).value,12279160*4);
  assert.ok(Number.isNaN(dv.getFloat32(tags.get(273).value,true)));
});

test('copy timestamp is a real UTC instant, not an arbitrary/path-like label',async()=>{
  for(const stamp of ['2026-02-30T00:00:00.000Z','2026-99-99T00:00:00Z','2026-10-02T19:00:00+01:00','../../escape']) await assert.rejects(()=>buildGeoTiff(model,stamp));
});
