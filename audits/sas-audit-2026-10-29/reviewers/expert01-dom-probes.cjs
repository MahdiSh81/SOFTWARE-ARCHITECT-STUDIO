'use strict';
const fs=require('fs');
const vm=require('vm');
const {createRequire}=require('module');
const repo='/workspace/SOFTWARE-ARCHITECT-STUDIO';
const testPath=repo+'/tests/test_workbench.cjs';
const original=fs.readFileSync(testPath,'utf8');
// Reuse the checkout's actual minimal DOM harness without modifying its source.
const header=original.slice(0,original.indexOf("test('lossless rich"));
const helpers=original.slice(original.indexOf('class Element'),original.indexOf("test('corrupt startup"));
const harness=header+helpers;
const runtime={require:createRequire(testPath),__dirname:repo+'/tests',console,process,TextEncoder,Blob};
vm.createContext(runtime);
const probes=String.raw`
const observations=[];
{
 const u=ui();u.elements.name.value='A real tenant reporting app';u.elements.brief.value='Build an app for five staff to export authorized tenant reports.';
 u.elements.depth.value='Quick advice';u.elements.depth.onchange();
 observations.push({id:'unapplied-brief-depth-change',status:'reproduced',visibleName:u.elements.name.value,visibleBrief:u.elements.brief.value,canonical:JSON.parse(u.run('JSON.stringify(state.project)')),lostTypedValues:u.elements.brief.value===''});
}
{
 const u=ui(JSON.stringify(C.importDocument(rich)));
 u.elements.recordList.children[1].children[1].click();
 u.elements.recordGroup.value='components';u.elements.recordGroup.onchange();
 const retainedRecord=JSON.parse(u.elements.recordJSON.value);
 u.elements.recordApply.onclick();
 observations.push({id:'record-collection-context-change',status:'reproduced',retainedRecordID:retainedRecord.id,componentInserted:u.run("state.project.components.some(x=>x.id==='FR-002')"),statusText:u.elements.status.textContent});
}
{
 const p=C.blank('Only a brief so far');p.brief='Customer supplied domain constraints';p.components=[{id:'main-api',name:'Existing customer component'}];
 const u=ui(JSON.stringify(C.importDocument(p)));u.elements.sampleBtn.onclick();
 observations.push({id:'sample-overwrites-brief-component-project',status:'reproduced',projectName:u.elements.name.value,components:JSON.parse(u.run('JSON.stringify(state.project.components.map(x=>x.id))')),brief:u.elements.brief.value,undoAvailable:u.run('undo.length>0'),sourceConfirmsNoDialog:true});
}
{
 const p=C.blank('Components-only project');p.components=[{id:'main-api',name:'Existing customer component'}];const u=ui(JSON.stringify(C.importDocument(p)));u.elements.newBtn.onclick();
 observations.push({id:'new-project-components-only',status:'reproduced',componentCount:u.run('state.project.components.length'),sourceConfirmationCondition:'requirements.length || decisions.length || brief',undoAvailable:u.run('undo.length>0')});
}
{
 const p=C.blank('Beginner reporting app');p.brief='A small app for staff to export tenant reports.';
 const u=ui(JSON.stringify(C.importDocument(p)));u.elements.audience.value='Beginner';u.elements.audience.onchange();
 observations.push({id:'browser-continuation-content',status:'observed',resume:JSON.parse(u.run('JSON.stringify(C.resume(state.project))')),excluded:{brief:!Object.hasOwn(C.resume(p),'brief'),sourceHash:!Object.hasOwn(C.resume(p),'source_hash'),requirements:!Object.hasOwn(C.resume(p),'requirements')}});
}
globalThis.probeResults={method:'Checkout actual inline UI script and project-core.js under the checkout minimal Node DOM harness. Not browser layout, persistence lifecycle, or assistive-technology validation.',observations};
`;
vm.runInContext(harness+probes,runtime,{timeout:10000});
const result=JSON.stringify(runtime.probeResults,null,2)+'\n';
fs.writeFileSync('/workspace/sas-audit-2026-10-29/reviewers/expert01-dom-probes.json',result);
console.log(result);
