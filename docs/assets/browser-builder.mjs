/* Exact frozen prediction re-export. No training, no API upload, no new candidate. */
export function fromBase64(text) {
  if (typeof text !== 'string') throw new Error('Invalid binary payload');
  const raw = atob(text);
  return Uint8Array.from(raw, c => c.charCodeAt(0));
}

export function decodeFootprint(bytes, total) {
  if (!Number.isSafeInteger(total) || total < 1 || total > 20_000_000) throw new Error('Invalid grid size');
  const fp = new Uint8Array(total);
  let cursor = 0, position = 0, inside = false;
  while (cursor < bytes.length) {
    let value = 0, shift = 0;
    for (;;) {
      if (cursor >= bytes.length || shift > 49) throw new Error('Truncated or oversized footprint run');
      const byte = bytes[cursor++];
      value += (byte & 127) * 2 ** shift;
      if (!(byte & 128)) break;
      shift += 7;
    }
    if (!Number.isSafeInteger(value) || position + value > total) throw new Error('Footprint overflow');
    if (inside) fp.fill(1, position, position + value);
    position += value;
    inside = !inside;
  }
  if (position !== total) throw new Error('Incomplete footprint');
  return fp;
}

export function decodeModel(model) {
  if (model.width !== 3292 || model.height !== 3730 || model.footprint_pixels !== 5167373) throw new Error('Not the pinned competition grid');
  const total = model.width * model.height;
  const fp = decodeFootprint(fromBase64(model.footprint_runs_base64), total);
  let count = 0;
  for (const bit of fp) count += bit;
  if (count !== model.footprint_pixels) throw new Error('Footprint count mismatch');
  const encoded = fromBase64(model.positive_indices_base64);
  if (encoded.length % 4 || encoded.length / 4 !== model.positive_pixels) throw new Error('Prediction count mismatch');
  const view = new DataView(encoded.buffer, encoded.byteOffset, encoded.byteLength);
  const positives = new Uint32Array(encoded.length / 4);
  let previous = -1;
  for (let i = 0; i < positives.length; i++) {
    const index = view.getUint32(i * 4, true);
    if (index >= total || !fp[index] || index <= previous) throw new Error('Unsorted, duplicate or out-of-footprint prediction');
    positives[i] = index;
    previous = index;
  }
  if (!/^[a-f0-9]{64}$/.test(model.prediction_sha256)) throw new Error('Missing prediction fingerprint');
  return {fp, positives, width: model.width, height: model.height};
}

export async function fingerprint(model, decoded) {
  const {fp, positives, width, height} = decoded;
  const packedLength = Math.ceil(fp.length / 8);
  const canonical = new Uint8Array(8 + packedLength + fp.length * 4);
  const view = new DataView(canonical.buffer);
  // Matches NumPy's canonical shape [height,width], little-bit-order mask, and <f4 scores.
  view.setUint32(0, height, true); view.setUint32(4, width, true);
  for (let i = 0; i < fp.length; i++) if (fp[i]) canonical[8 + (i >> 3)] |= 1 << (i & 7);
  for (const index of positives) view.setFloat32(8 + packedLength + index * 4, 1, true);
  const hash = new Uint8Array(await crypto.subtle.digest('SHA-256', canonical));
  const hex = Array.from(hash, b => b.toString(16).padStart(2, '0')).join('');
  if (hex !== model.prediction_sha256) throw new Error('Prediction fingerprint does not match evaluated file');
  return hex;
}

function ascii(text) { return new TextEncoder().encode(text + '\0'); }
function shortArray(values) { const bytes = new Uint8Array(values.length * 2); const v = new DataView(bytes.buffer); values.forEach((x,i) => v.setUint16(i*2,x,true)); return bytes; }
function doubleArray(values) { const bytes = new Uint8Array(values.length * 8); const v = new DataView(bytes.buffer); values.forEach((x,i) => v.setFloat64(i*8,x,true)); return bytes; }

export async function buildGeoTiff(model, stamp = new Date().toISOString()) {
  if (typeof stamp !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(stamp) ||
      !Number.isFinite(Date.parse(stamp)) || new Date(stamp).toISOString().slice(0,19) !== stamp.slice(0,19)) throw new Error('Valid ISO UTC timestamp required');
  const decoded = decodeModel(model);
  const verified = await fingerprint(model, decoded);
  const {width, height, fp, positives} = decoded;
  const scalar = (tag, type, value) => ({tag, type, count: 1, value});
  const tags = [scalar(256,4,width), scalar(257,4,height), scalar(258,3,32), scalar(259,3,1),
    scalar(262,3,1), scalar(273,4,0), scalar(277,3,1), scalar(278,4,height),
    scalar(279,4,width*height*4), scalar(284,3,1), scalar(339,3,3),
    {tag:305,type:2,data:ascii('GEMSDOE26 browser format copy; SAME frozen predictions; unscored')},
    {tag:306,type:2,data:ascii(stamp.slice(0,19).replaceAll('-',':').replace('T',' '))},
    {tag:33550,type:12,data:doubleArray([100,100,0])},
    {tag:33922,type:12,data:doubleArray([0,0,0,243350,4508550,0])},
    {tag:34735,type:3,data:shortArray([1,1,0,4,1024,0,1,1,1025,0,1,1,3072,0,1,32611,3076,0,1,9001])},
    {tag:42113,type:2,data:ascii('nan')}
  ].sort((a,b) => a.tag-b.tag);
  const sizes = {2:1,3:2,4:4,12:8};
  let offset = 8 + 2 + tags.length*12 + 4;
  for (const tag of tags) if (tag.data) {
    tag.count = tag.data.length / sizes[tag.type];
    if (tag.data.length > 4) {
      offset = Math.ceil(offset/8)*8;
      tag.offset = offset;
      offset += tag.data.length;
    }
  }
  const pixelsOffset = Math.ceil(offset/8)*8;
  tags.find(t => t.tag === 273).value = pixelsOffset;
  const bytes = new Uint8Array(pixelsOffset + width*height*4);
  const dv = new DataView(bytes.buffer);
  dv.setUint16(0,0x4949,true); dv.setUint16(2,42,true); dv.setUint32(4,8,true);
  dv.setUint16(8,tags.length,true);
  tags.forEach((tag,i) => {
    const location = 10+i*12;
    dv.setUint16(location,tag.tag,true); dv.setUint16(location+2,tag.type,true);
    dv.setUint32(location+4,tag.count,true);
    if (tag.data) {
      if (tag.data.length <= 4) bytes.set(tag.data,location+8);
      else { dv.setUint32(location+8,tag.offset,true); bytes.set(tag.data,tag.offset); }
    } else if (tag.type === 3) dv.setUint16(location+8,tag.value,true);
    else dv.setUint32(location+8,tag.value,true);
  });
  // Explicit endianness; every footprint value is finite 0/1, outside is NaN.
  for (let i = 0; i < fp.length; i++) dv.setFloat32(pixelsOffset+i*4,fp[i] ? 0 : NaN,true);
  for (const index of positives) dv.setFloat32(pixelsOffset+index*4,1,true);
  return {bytes, fingerprint: verified,
    filename: `gems26-browser-copy-${stamp.replace(/[^0-9]/g,'').slice(0,17)}-${verified.slice(0,12)}-nan.tif`,
    note: 'Format-only copy of evaluated H26-SSL-v1; same predictions, NOT a new candidate; do not submit while research gate is blocked.'};
}
