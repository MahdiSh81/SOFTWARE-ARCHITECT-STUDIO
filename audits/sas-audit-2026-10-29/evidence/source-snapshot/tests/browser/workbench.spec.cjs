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
