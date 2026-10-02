import {buildGeoTiff} from './browser-builder.mjs';

const announce = text => {
  const node = document.querySelector('#live-status');
  if (node) node.textContent = text;
};

for (const button of document.querySelectorAll('[data-copy]')) {
  button.addEventListener('click', async () => {
    const text = document.getElementById(button.dataset.copy)?.textContent.trim();
    if (!text) return;
    try {
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        // Trusted-click fallback for preview iframes or non-secure local origins.
        // Copies only this visible field; never reads the user's clipboard.
        const field = document.createElement('textarea');
        field.value = text; field.readOnly = true; field.tabIndex = -1;
        field.setAttribute('aria-hidden', 'true');
        field.style.cssText = 'position:fixed;left:-9999px;top:0;';
        document.body.append(field); field.select();
        let copied;
        try { copied = document.execCommand('copy'); }
        finally { field.remove(); button.focus({preventScroll:true}); }
        if (!copied) throw new Error('Clipboard permission unavailable');
      }
      announce('Copied to clipboard.');
      const original = button.textContent;
      button.textContent = 'Copied ✓';
      setTimeout(() => button.textContent = original, 1600);
    } catch {
      announce('Clipboard permission unavailable. The text is visible and selectable below.');
    }
  });
}

const search = document.querySelector('#history-search');
if (search) search.addEventListener('input', () => {
  const query = search.value.toLowerCase().trim();
  let count = 0;
  for (const row of document.querySelectorAll('#history-table tbody tr')) {
    row.hidden = !row.textContent.toLowerCase().includes(query);
    if (!row.hidden) count++;
  }
  document.querySelector('#history-count').textContent = `${count} records shown`;
});

for (const button of document.querySelectorAll('[data-map]')) {
  button.addEventListener('click', () => {
    const image = document.querySelector('#study-map');
    if (!image) return;
    image.src = button.dataset.map;
    image.alt = button.dataset.alt;
    for (const b of document.querySelectorAll('[data-map]')) b.setAttribute('aria-pressed', b === button ? 'true' : 'false');
    const caption = document.querySelector('#map-label');
    if (caption) caption.textContent = button.dataset.label;
  });
}

const generate = document.querySelector('#build-tiff');
if (generate) generate.addEventListener('click', async () => {
  const progress = document.querySelector('#build-progress');
  generate.disabled = true;
  progress.textContent = 'Checking the prediction fingerprint and building a 49 MB GeoTIFF…';
  try {
    const response = await fetch(new URL('../data/browser-model.json', import.meta.url));
    if (!response.ok) throw new Error(`Model cells unavailable (HTTP ${response.status})`);
    const model = await response.json();
    const built = await buildGeoTiff(model);
    const url = URL.createObjectURL(new Blob([built.bytes], {type:'image/tiff'}));
    const link = document.createElement('a'); link.href = url; link.download = built.filename;
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    progress.textContent = `Built ${built.filename}. Exact frozen prediction fingerprint verified. Same predictions—not a new experiment. ${model.release_decision === 'BLOCKED_DO_NOT_SUBMIT' ? 'Do not submit: holdout gate failed.' : 'This copy does not create an additional validated candidate.'}`;
    announce('GeoTIFF built. No model was trained and no competition upload was made.');
  } catch (error) {
    progress.textContent = `Build stopped: ${error.message}. Use the smaller, already-validated download instead.`;
  } finally { generate.disabled = false; }
});

const verify = document.querySelector('#verify-download');
if (verify) verify.addEventListener('click', async () => {
  verify.disabled = true;
  const node = document.querySelector('#checksum-status');
  node.textContent = 'Downloading the published file and checking its SHA-256…';
  try {
    const response = await fetch(verify.dataset.file);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const bytes = await response.arrayBuffer();
    const hash = new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));
    const hex = Array.from(hash,b=>b.toString(16).padStart(2,'0')).join('');
    if (hex !== verify.dataset.sha) throw new Error('File checksum differs from the published receipt');
    node.textContent = `Checksum verified: ${hex}. This verifies file identity, not hidden-fault accuracy or upload eligibility.`;
  } catch (error) { node.textContent = `Verification failed: ${error.message}. Do not use a mismatched file.`; }
  finally { verify.disabled = false; }
});
