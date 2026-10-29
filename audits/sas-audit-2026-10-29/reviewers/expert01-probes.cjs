'use strict';
const fs=require('fs');
const path=require('path');
const {chromium}=require('/workspace/sas-browser/node_modules/playwright');
const output='/workspace/sas-audit-2026-10-29/reviewers';
const source='/workspace/SOFTWARE-ARCHITECT-STUDIO';
const result={method:'Actual Chromium via installed Playwright; file:// offline workbench; synthetic task walkthroughs, no human participants',browser:null,checks:[]};
function record(id,observation){result.checks.push({id,...observation});}
(async()=>{
 let context;
 try {
  context=await chromium.launchPersistentContext(path.join(output,'expert01-browser-profile'),{executablePath:'/usr/bin/chromium',headless:true,viewport:{width:1280,height:1000},args:['--disable-dev-shm-usage']});
  result.browser=context.browser()?.version()??'persistent context';
  const page=await context.newPage();
  await page.goto('file://'+source+'/workbench/index.html');
  await page.locator('#status').filter({hasText:'Workspace ready'}).waitFor();
  record('startup',{status:'passed',statusText:await page.locator('#status').innerText()});
  await page.screenshot({path:path.join(output,'expert01-workbench-desktop.png'),fullPage:true});
  await page.locator('#name').fill('A real tenant reporting app');
  await page.locator('#brief').fill('Build an app for five staff to export authorized tenant reports.');
  await page.locator('#depth').selectOption('Quick advice');
  record('unapplied-brief-depth-change',{status:'observed',visibleName:await page.locator('#name').inputValue(),visibleBrief:await page.locator('#brief').inputValue(),canonical:await page.evaluate(()=>({name:state.project.name,brief:state.project.brief,depth:state.project.preferences.depth})),lostTypedValues:(await page.locator('#brief').inputValue())===''});
  const rich=JSON.parse(fs.readFileSync(path.join(source,'tests/fixtures/rich-project.json'),'utf8'));
  await page.evaluate(p=>{state=C.importDocument(p);render();},rich);
  await page.locator('[data-panel=records]').click();
  await page.locator('#recordList .item').nth(1).getByRole('button',{name:'Edit JSON'}).click();
  await page.locator('#recordGroup').selectOption('components');
  const retainedRecord=JSON.parse(await page.locator('#recordJSON').inputValue());
  await page.locator('#recordApply').click();
  record('record-collection-context-change',{status:'observed',retainedRecordID:retainedRecord.id,componentInserted:await page.evaluate(()=>state.project.components.some(x=>x.id==='FR-002')),statusText:await page.locator('#status').innerText()});
  await page.evaluate(()=>{state=C.importDocument(C.blank('Only a brief so far'));state.project.brief='Customer supplied private domain constraints';state.project.components=[{id:'main-api',name:'Existing customer component'}];render();});
  await page.locator('[data-panel=project]').click();
  let dialogs=0;
  page.on('dialog',async d=>{dialogs++;await d.accept();});
  await page.locator('#sampleBtn').click();
  record('sample-overwrites-brief-component-project',{status:'observed',confirmationDialogs:dialogs,projectName:await page.locator('#name').inputValue(),components:await page.evaluate(()=>state.project.components.map(x=>x.id)),brief:await page.locator('#brief').inputValue(),undoAvailable:await page.evaluate(()=>undo.length>0)});
  await page.evaluate(()=>{state=C.importDocument(C.blank('Customer project'));state.project.brief='Build tenant report app';state.project.components=[{id:'main-api',name:'Existing customer component'}];render();});
  const dialogsBeforeNew=dialogs;
  await page.locator('#newBtn').click();
  record('new-project-with-brief',{status:'observed',confirmationDialogs:dialogs-dialogsBeforeNew});
  await page.evaluate(()=>{state=C.importDocument(C.blank('Components-only project'));state.project.components=[{id:'main-api',name:'Existing customer component'}];render();});
  const dialogsBeforeComponentNew=dialogs;
  await page.locator('#newBtn').click();
  record('new-project-components-only',{status:'observed',confirmationDialogs:dialogs-dialogsBeforeComponentNew,componentCount:await page.evaluate(()=>state.project.components.length)});
  await page.evaluate(()=>{state=C.importDocument(C.blank('Beginner reporting app'));state.project.brief='A small app for staff to export tenant reports.';render();});
  await page.locator('#audience').selectOption('Beginner');
  await page.locator('[data-panel=records]').click();
  record('beginner-first-requirement',{status:'observed',recordEditorInitialValue:await page.locator('#recordJSON').inputValue(),visibleInputs:await page.locator('#records input, #records textarea').evaluateAll(xs=>xs.map(x=>({id:x.id,placeholder:x.placeholder||null})))});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(output,'expert01-workbench-mobile.png'),fullPage:true});
  record('narrow-viewport',{status:'observed',dimensions:await page.evaluate(()=>({viewport:innerWidth,documentWidth:document.documentElement.scrollWidth})),screenshot:'expert01-workbench-mobile.png'});
  record('browser-continuation-content',{status:'observed',resume:await page.evaluate(()=>C.resume(state.project))});
 } catch(e) {result.error={name:e.name,message:e.message};process.exitCode=1;}
 finally {if(context)await context.close();fs.writeFileSync(path.join(output,'expert01-browser-probes.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));}
})();
