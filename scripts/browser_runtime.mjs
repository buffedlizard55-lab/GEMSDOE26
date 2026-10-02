/* Portable test-only NSS/NSPR libraries from the integrity-locked Chromium package.
   No root package manager, remote browser downloads or disabled TLS validation. */
import {readFile,writeFile,mkdir,access} from 'node:fs/promises';
import {brotliDecompressSync} from 'node:zlib';
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';
import chromium from '@sparticuz/chromium';
export async function launchOptions(){
  const folder=resolve('.cache/browser-libs');await mkdir(folder,{recursive:true});
  try{await access(folder+'/lib/libnspr4.so');}catch{
    const archive=await readFile(new URL('../node_modules/@sparticuz/chromium/bin/al2023.tar.br',import.meta.url));
    await writeFile(folder+'/al2023.tar',brotliDecompressSync(archive));
    const extracted=spawnSync('tar',['-xf',folder+'/al2023.tar','-C',folder,'--no-same-owner'],{encoding:'utf8'});
    if(extracted.status!==0)throw new Error('Bundled test-library extraction failed: '+extracted.stderr);
  }
  // Keep normal web-origin security. Only sandbox flags needed by this container remain.
  const args=chromium.args.filter(arg=>!['--disable-web-security','--allow-running-insecure-content','--disable-site-isolation-trials'].includes(arg));
  return {args,executablePath:await chromium.executablePath(),headless:true,
    env:{...process.env,LD_LIBRARY_PATH:folder+'/lib'+(process.env.LD_LIBRARY_PATH?':'+process.env.LD_LIBRARY_PATH:'')}};
}
