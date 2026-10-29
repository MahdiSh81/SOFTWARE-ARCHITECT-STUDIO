const { test, expect } = require('@playwright/test');
test('opens workbench and keyboard focus works', async ({ page }) => {
 await page.goto('/workbench/index.html'); await expect(page.locator('#main')).toBeVisible();
 await expect(page.locator('#status')).toContainText('Workspace ready'); await expect(page.locator('#name')).toBeVisible();
 await page.keyboard.press('Tab'); await expect(page.locator(':focus')).not.toHaveCount(0);
});
test('edits persist in local browser storage', async ({ page }) => {
 await page.goto('/workbench/index.html'); await page.locator('#name').fill('Browser verification project');
 await page.locator('#brief').fill('Real-browser persistence test.'); await page.locator('#briefApply').click();
 await expect.poll(() => page.evaluate(() => { const v=localStorage.getItem('software-architect-studio-v07'); return v ? JSON.parse(v).project.name : null; })).toBe('Browser verification project');
});
test('two tabs retain both drafts when writes interleave', async ({ context }) => {
 const a=await context.newPage(),b=await context.newPage(); await Promise.all([a.goto('/workbench/index.html'),b.goto('/workbench/index.html')]);
 await Promise.all([a.evaluate(()=>{state.project.name='First writer';return persist();}),b.evaluate(()=>{state.project.name='Second writer';return persist();})]);
 const drafts=await a.evaluate(()=>{const out=[];for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k&&k.startsWith('software-architect-studio-v07.draft.'))out.push(JSON.parse(localStorage.getItem(k)).project.name);}return out;});
 expect(drafts).toContain('First writer'); expect(drafts).toContain('Second writer');
});
test('project export downloads a portable project', async ({ page }) => {
 await page.goto('/workbench/index.html'); const download=page.waitForEvent('download'); await page.locator('#projectExport').click();
 expect((await download).suggestedFilename()).toMatch(/project\.json$/);
});
test('pending brief survives preference changes, persisted draft and reload', async ({ page }) => {
 await page.goto('/workbench/index.html');
 await page.locator('#brief').fill('متن ذخیره نشده');
 await page.locator('#depth').selectOption('Full specification');
 await expect(page.locator('#brief')).toHaveValue('متن ذخیره نشده');
 await expect.poll(() => page.evaluate(() => JSON.parse(localStorage.getItem('software-architect-studio-v07') || '{}').ui?.editorDrafts?.project?.brief)).toBe('متن ذخیره نشده');
 await page.reload(); await expect(page.locator('#brief')).toHaveValue('متن ذخیره نشده');
 expect(await page.locator('#brief').evaluate(e => getComputedStyle(e).direction)).toBe('rtl');
 await page.locator('#briefApply').click();
 expect(await page.evaluate(() => state.project.brief)).toBe('متن ذخیره نشده');
});
test('collection switches isolate drafts and common fields preserve unknown data', async ({ page }) => {
 await page.goto('/workbench/index.html');
 await page.evaluate(() => { state=C.importDocument(C.blank());state.project.requirements=[{id:'FR-001',description:'Original',extra:{preserve:true}}];render(); });
 await page.locator('button[data-panel="records"]').click();
 await page.getByRole('button',{name:'Edit fields / JSON'}).click();
 await page.locator('#recordLabel').fill('Pending field edit');
 await page.locator('#recordGroup').selectOption('components');
 await expect(page.locator('#recordJSON')).toHaveValue('{}');
 await page.locator('#recordApply').click();
 expect(await page.evaluate(() => state.project.components.length)).toBe(0);
 await page.locator('#recordGroup').selectOption('requirements');
 await expect(page.locator('#recordLabel')).toHaveValue('Pending field edit');
 await page.locator('#recordFieldsApply').click();
 expect(await page.evaluate(() => state.project.requirements[0])).toMatchObject({id:'FR-001',description:'Pending field edit',extra:{preserve:true}});
});
test('sample and new guards preserve components-only project when declined', async ({ page }) => {
 await page.goto('/workbench/index.html');
 await page.evaluate(() => {state=C.importDocument(C.blank());state.project.components=[{id:'cmp-1',name:'Retain'}];render();});
 page.on('dialog',dialog=>dialog.dismiss());
 await page.locator('#newBtn').click();
 expect(await page.evaluate(()=>state.project.components[0].name)).toBe('Retain');
 await page.locator('#sampleBtn').click();
 expect(await page.evaluate(()=>state.project.components[0].name)).toBe('Retain');
});
test('constraints export is structured project data with original acceptance provenance', async ({ page }) => {
 await page.goto('/workbench/index.html');
 await page.evaluate(() => {state.project.decisions=[{id:'ADR-001',status:'Accepted',decision:'Imported fact',approval_origin:'external import'}];render();});
 await page.locator('button[data-panel="tools"]').click();
 const downloaded=page.waitForEvent('download');await page.locator('#rulesExport').click();
 const download=await downloaded;expect(download.suggestedFilename()).toBe('architecture-constraints.json');
 const stream=await download.createReadStream(),parts=[];for await(const part of stream)parts.push(part);
 expect(JSON.parse(Buffer.concat(parts).toString()).decisions[0].approval_origin).toBe('external import');
});
test('test server does not expose repository files or metadata',async({request})=>{
 for(const path of ['/.git/config','/README.md','/tools/architect_cli.py','/workbench/../README.md','/workbench/not-an-asset'])expect((await request.get(path)).status()).toBe(404);
});
