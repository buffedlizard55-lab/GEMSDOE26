/* Produce a real browser-writer TIFF for independent Rasterio validation. */
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {buildGeoTiff} from '../docs/assets/browser-builder.mjs';
const model=JSON.parse(await readFile(new URL('../docs/data/browser-model.json',import.meta.url),'utf8'));
const output=resolve(process.argv[2] || '.cache/browser-export.tif');
if (!output.startsWith(resolve('.cache')+'/')) throw new Error('Scratch export must remain in .cache');
const result=await buildGeoTiff(model,'2026-10-02T19:00:00.000Z');
await mkdir(dirname(output),{recursive:true});await writeFile(output,result.bytes);
console.log(JSON.stringify({path:output,bytes:result.bytes.length,prediction_sha256:result.fingerprint,filename:result.filename,scope:'Format-only copy, not a new model'}));
