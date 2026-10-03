/* Real Chromium UI/download QA; external scientific/competition links are NOT crawled. */
import puppeteer from 'puppeteer-core';
import {launchOptions} from './browser_runtime.mjs';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';

const root=resolve('.');
const index=process.argv.indexOf('--base-url');
let base=index>=0 ? process.argv[index+1] : 'http://127.0.0.1:8088/';
if (!base.endsWith('/'))base+='/';
const parsed=new URL(base);
if (!['127.0.0.1','localhost','buffedlizard55-lab.github.io'].includes(parsed.hostname) && !parsed.hostname.endsWith('.e2b.app')) throw new Error('UI tests only access the local preview or this owner’s Pages, never competition endpoints');
if (parsed.username || parsed.password)throw new Error('Do not pass credentials to browser tests');
const out=resolve('.cache/ui');await mkdir(out,{recursive:true});
const downloads=resolve('.cache/ui-downloads');await mkdir(downloads,{recursive:true});
let server;
if(index<0){
  server=spawn(process.env.PYTHON || 'python3',['-u','-m','http.server','8088','--bind','0.0.0.0','--directory',resolve('.cache/pages-site')],{stdio:['ignore','pipe','pipe']});
  await new Promise((ok,fail)=>{
    const timeout=setTimeout(()=>fail(new Error('Test server did not start')),15000);
    server.stdout.on('data',b=>{if(String(b).includes('Serving HTTP')){clearTimeout(timeout);ok();}});
    server.on('exit',code=>{clearTimeout(timeout);fail(new Error('Test server exited '+code));});
  });
}
const errors=[],checks=[],consoleErrors=[],externalRequests=[];
const check=(name,pass,details={})=>{checks.push({name,pass,...details});if(!pass)errors.push(name);};
let browser;
try{
  browser=await puppeteer.launch(await launchOptions());
  const page=await browser.newPage();
  page.on('pageerror',e=>consoleErrors.push(e.message));
  page.on('request',req=>{const url=req.url();if(url.startsWith('http') && new URL(url).origin!==parsed.origin)externalRequests.push(url);});
  const cdp=await browser.target().createCDPSession();await cdp.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloads,eventsEnabled:true});
  for(const [label,width,height] of [['desktop',1440,900],['laptop',1366,768],['mobile',390,844],['small-mobile',375,667]]){
    await page.setViewport({width,height,deviceScaleFactor:1});await page.goto(base,{waitUntil:'networkidle0'});
    const visibility=await page.evaluate(()=>{
      const anchor=document.querySelector('.download-card a[download]');const box=anchor?.getBoundingClientRect();
      return {present:!!anchor,top:box?.top,bottom:box?.bottom,viewport:innerHeight,warning:document.querySelector('.download-card .notice')?.innerText.includes('Do not submit'),overflow:document.documentElement.scrollWidth>innerWidth+1,href:anchor?.getAttribute('href')};
    });
    check(label+' first-screen TIFF download',visibility.present && visibility.bottom<=height,visibility);
    check(label+' prominent do-not-submit warning',visibility.warning);
    check(label+' no horizontal page overflow',!visibility.overflow);
    await page.screenshot({path:out+'/'+label+'.png',fullPage:true});
  }
  await page.setViewport({width:1440,height:900});await page.goto(base,{waitUntil:'networkidle0'});
  await page.click('[data-map*="map-h25.png"]');
  check('historical map toggle',await page.$eval('#study-map',x=>x.src.includes('map-h25.png')));
  const published=JSON.parse(await readFile('evidence/dilcond_holdout.json','utf8')).oof_artifact;
  const direct=await page.evaluate(async href=>{const response=await fetch(href);const b=await response.arrayBuffer();return {ok:response.ok,bytes:b.byteLength,sha:[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('')};},published.path);
  check('one-click target serves exact TIFF bytes',direct.ok && direct.bytes===published.bytes && direct.sha===published.sha256,direct);
  let directName;
  const directReady=new Promise((ok,fail)=>{
    const timer=setTimeout(()=>fail(new Error('Direct TIFF download did not finish')),30000);
    const begin=e=>{directName=e.suggestedFilename;};
    const progress=e=>{if(e.state==='completed'){clearTimeout(timer);cdp.off('Browser.downloadWillBegin',begin);cdp.off('Browser.downloadProgress',progress);ok();}};
    cdp.on('Browser.downloadWillBegin',begin);cdp.on('Browser.downloadProgress',progress);
  });
  await page.click('.download-card a[download]');await directReady;
  const savedDirect=await readFile(downloads+'/'+directName);
  check('actual direct-click filename and downloaded SHA',directName===published.path.split('/').pop() && createHash('sha256').update(savedDirect).digest('hex')===published.sha256,{filename:directName});

  await page.goto(base+'docs/index.html',{waitUntil:'networkidle0'});check('nested landing offers same TIFF',!!await page.$('.download-card a[download]'));
  await page.goto(base+'docs/history.html',{waitUntil:'networkidle0'});
  await page.type('#history-search','0.2477');
  const visible=await page.$$eval('#history-table tbody tr',r=>r.filter(x=>!x.hidden).map(x=>x.textContent));
  check('search isolates reported H25 result',visible.length===1 && visible[0].includes('h25-1'));
  await page.goto(base+'docs/executive-summary.html',{waitUntil:'networkidle0'});
  await browser.defaultBrowserContext().overridePermissions(parsed.origin,['clipboard-read','clipboard-write','clipboard-sanitized-write']);
  await page.bringToFront();
  await page.click('[data-copy="submission-note"]');
  await page.waitForFunction(()=>document.querySelector('[data-copy="submission-note"]')?.textContent.startsWith('Copied'),{timeout:10000});
  const copied=await page.evaluate(()=>navigator.clipboard.readText());
  check('short note copy button works',copied===JSON.parse(await readFile('evidence/dilcond_holdout.json','utf8')).submission_note);
  await page.click('#verify-download');
  await page.waitForFunction(()=>document.querySelector('#checksum-status')?.textContent.startsWith('Checksum verified:'),{timeout:30000});check('interactive SHA verification',true);
  const finished=new Promise((ok,fail)=>{
    const timeout=setTimeout(()=>fail(new Error('Browser export download did not complete')),60000);
    cdp.on('Browser.downloadProgress',event=>{if(event.state==='completed'){clearTimeout(timeout);ok(event);}else if(event.state==='canceled'){clearTimeout(timeout);fail(new Error('Download cancelled'));}});
  });
  let downloadName;
  cdp.on('Browser.downloadWillBegin',event=>downloadName=event.suggestedFilename);
  await page.click('#build-tiff');await finished;
  await page.waitForFunction(()=>document.querySelector('#build-progress')?.textContent.startsWith('Built '),{timeout:15000});
  check('browser builds and downloads genuine TIFF',downloadName?.endsWith('-nan.tif') && (await stat(downloads+'/'+downloadName)).size>49_000_000,{filename:downloadName});
  check('browser copy warns same predictions and blocked gate',await page.$eval('#build-progress',e=>e.textContent.includes('Same predictions') && e.textContent.includes('Do not submit')));
  await page.screenshot({path:out+'/guide.png',fullPage:true});
  check('no JavaScript errors',consoleErrors.length===0,{consoleErrors});
  check('no external automatic requests',externalRequests.length===0,{externalRequests});
  for(const route of ['docs/research.html','docs/sources.html','docs/review.html']){
    const response=await page.goto(base+route,{waitUntil:'networkidle0'});check(route+' loads',response?.status()===200);
  }
}catch(error){errors.push(error.message);}
finally{if(browser)await browser.close();if(server)server.kill('SIGTERM');}
const receipt={checked_utc:new Date().toISOString(),base_url:base,status:errors.length?'FAIL':'PASS',checks,errors,download_directory:downloads,screenshots_directory:out,external_links_not_crawled:true};
await writeFile('evidence/browser_checks.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify(receipt,null,2));if(errors.length)process.exitCode=1;
