import copy,importlib.util,json,math,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE/'tools'))
from project_model import *
from safe_io import atomic_write,read_json,read_bytes,dumps,digest
from revision_store import init_project,load_project,snapshot,recover,commit_project,restore
from graph_engine import impacts,change_bundle
from artifact_compiler import handoff,resolve_generation,recover_handoff,compile_plan,readiness
from repository_evidence import repo_scan,fitness,evidence_delta
from validation_engine import validate,openapi_checks,bounded_process
from calculators import capacity,score,DIMENSIONS
from behavioral_eval import evaluate_cases
from workflow_tools import sqlite_schema_check,freshness,specialist_plan,research_kit,sensitivity

class ReleaseTests(unittest.TestCase):
 def setUp(self):self.p=json.loads((BASE/'tests/fixtures/rich-project.json').read_text())
 def root(self,temp,p=None):
  root=Path(temp)/'project';root.mkdir();atomic_write(root/'project.json',dumps(p or self.p));return root
 def cli(self,*args):return subprocess.run([sys.executable,str(BASE/'tools/architect_cli.py'),*map(str,args)],capture_output=True,text=True,timeout=20)
 def test_missing_envelope_rejected(self):self.assertTrue(project_checks({'schema_version':2}))
 def test_invalid_shapes_are_diagnostics(self):
  for field,value in [('revision',True),('name',None),('components',{}),('interfaces',[None]),('decisions',[{'id':'ADR-001','status':{}}]),('relationships',[{'id':{},'kind':'calls','from':{},'to':{}}])]:
   p=copy.deepcopy(self.p);p[field]=value;self.assertTrue(project_checks(p),field)
 def test_rich_fixture_valid(self):self.assertEqual(project_checks(self.p),[])
 @unittest.skipUnless(importlib.util.find_spec('jsonschema'),'optional jsonschema unavailable')
 def test_published_schema_agrees_with_fixtures(self):
  import jsonschema
  schema=read_json(BASE/'schemas/project-v2.schema.json');jsonschema.Draft202012Validator.check_schema(schema)
  jsonschema.validate(self.p,schema)
  for p in read_json(BASE/'tests/fixtures/conformance.json')['invalid']:
   self.assertTrue(project_checks(p));self.assertTrue(list(jsonschema.Draft202012Validator(schema).iter_errors(p)))
 def test_init_preserves_unrelated_history(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);(r/'HISTORY.md').write_text('human history')
   with self.assertRaises(ValueError):init_project(r,'new')
   self.assertEqual((r/'HISTORY.md').read_text(),'human history');self.assertFalse((r/'project.json').exists())
 @unittest.skipUnless(os.name=='posix','POSIX no-follow scope')
 def test_symlink_reads_and_writes_refused(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);victim=r/'victim';victim.write_text('sentinel');link=r/'link';link.symlink_to(victim)
   with self.assertRaises((ValueError,OSError)):read_bytes(link)
   with self.assertRaises((ValueError,OSError)):atomic_write(link,'bad')
   self.assertEqual(victim.read_text(),'sentinel')
 def test_snapshot_failure_retries_without_double_revision(self):
  import revision_store as rs
  with tempfile.TemporaryDirectory() as t:
   root=self.root(t);real=rs.atomic_write;failed=[False]
   def fault(path,*a,**k):
    if path==root/'project.json' and not failed[0]:failed[0]=True;raise OSError('injected')
    return real(path,*a,**k)
   with patch.object(rs,'atomic_write',side_effect=fault):
    with self.assertRaises(OSError):snapshot(root,'critical message')
   self.assertEqual(load_project(root)['revision'],1);snapshot(root,'critical message')
   self.assertEqual(load_project(root)['revision'],2);self.assertIn('critical message',(root/'HISTORY.md').read_text())
 def test_history_projection_failure_recoverable(self):
  import revision_store as rs
  with tempfile.TemporaryDirectory() as t:
   root=self.root(t);real=rs.atomic_write
   def fault(path,*a,**k):
    if path==root/'HISTORY.md':raise OSError('injected history failure')
    return real(path,*a,**k)
   with patch.object(rs,'atomic_write',side_effect=fault):
    with self.assertRaises(OSError):snapshot(root,'message survives')
   self.assertEqual(load_project(root)['revision'],2);recover(root);self.assertIn('message survives',(root/'HISTORY.md').read_text())
 def test_commit_conflict_preserves_project(self):
  with tempfile.TemporaryDirectory() as t:
   root=self.root(t);before=read_bytes(root/'project.json')
   with self.assertRaises(ValueError):commit_project(root,self.p,'change','wrong hash')
   self.assertEqual(before,read_bytes(root/'project.json'))
 def test_restore_as_new_revision(self):
  with tempfile.TemporaryDirectory() as t:
   root=self.root(t);snapshot(root,'baseline');p=load_project(root);p['brief']='changed';commit_project(root,p,'change',digest(load_project(root)))
   restore(root,1,digest(load_project(root)),'restore');r=load_project(root)
   self.assertEqual(r['revision'],4);self.assertEqual(r['brief'],self.p['brief'])
 def test_typed_graph_closure_cycles_order_invariant(self):
  p=copy.deepcopy(self.p);p['components']+=[{'id':'worker','requirements':[]}]
  p['relationships']+=[{'id':'EDGE-002','kind':'depends_on','from':{'group':'components','id':'worker'},'to':{'group':'components','id':'web-api'}},{'id':'EDGE-003','kind':'depends_on','from':{'group':'components','id':'web-api'},'to':{'group':'components','id':'worker'}}]
  a=impacts(p,['FR-001']);p['relationships'].reverse();b=impacts(p,['FR-001'])
  self.assertNotEqual(a.pop('source_hash'),b.pop('source_hash')) # bytes/array identity changed; impact semantics must not.
  self.assertEqual(a,b);self.assertIn('worker',[r['id'] for r in a['affected']['components']])
 def test_change_removed_requirement_is_supported(self):
  p=new_project('new');r=change_bundle(self.p,p);self.assertIn('FR-001',r['changed_requirements']);self.assertEqual(r['status'],'PROPOSED; not applied')
 def test_supersede_preserves_predecessor(self):
  p=copy.deepcopy(self.p);p['decisions'][0]['status']='Accepted';q=supersede(p,'ADR-001','ADR-002','new evidence')
  self.assertEqual(q['decisions'][0]['decision'],p['decisions'][0]['decision']);self.assertEqual(q['decisions'][1]['supersedes'],'ADR-001')
 def test_compiler_preserves_native_contracts_and_ids(self):
  files,r=compile_plan(self.p,include_private=True);self.assertEqual(json.loads(files['api.json']),self.p['api_contract']);self.assertEqual(json.loads(files['project.json']),self.p)
  self.assertIn('web-api',files['containers.mmd']);self.assertEqual(len(json.loads(files['tasks.json'])),1)
 def test_head_supported_and_duplicate_rejected_before_write(self):
  p=new_project('HEAD test');p['interfaces']=[{'id':'HEAD-001','method':'HEAD','path':'/health','operation':{'responses':{'204':{'description':'ok'}}}}]
  files,_=compile_plan(p);self.assertIn('head',json.loads(files['api.json'])['paths']['/health'])
  p['interfaces'].append({**p['interfaces'][0],'id':'HEAD-002'})
  with self.assertRaises(ValueError):compile_plan(p)
 def test_unordered_associations_do_not_invent_flows(self):
  p=copy.deepcopy(self.p);p['relationships']=[];files,_=compile_plan(p);self.assertNotIn('-->',files['containers.mmd'])
 def test_stale_owned_adr_removed_and_unowned_note_preserved(self):
  with tempfile.TemporaryDirectory() as t:
   root=self.root(t);out=Path(t)/'out';handoff(root,out);(out/'human-note.txt').write_text('private note')
   p=copy.deepcopy(self.p);p['decisions']=[];p['tasks'][0]['decisions']=[];atomic_write(root/'project.json',dumps(p));r=handoff(root,out,True)
   self.assertFalse((out/'adrs/ADR-001.md').exists());self.assertEqual((out/'human-note.txt').read_text(),'private note');self.assertNotIn('human-note.txt',r['generated'])
 def test_modified_owned_output_not_overwritten(self):
  with tempfile.TemporaryDirectory() as t:
   root=self.root(t);out=Path(t)/'out';handoff(root,out);(out/'architecture.md').write_text('human edit')
   with self.assertRaises(ValueError):handoff(root,out,True)
   self.assertEqual((out/'architecture.md').read_text(),'human edit')
 def test_committed_handoff_survives_projection_failure(self):
  import artifact_compiler as ac
  with tempfile.TemporaryDirectory() as t:
   root=self.root(t);out=Path(t)/'out';real=ac.atomic_write;failed=[False]
   def fault(path,*a,**k):
    if path==out/'api.json' and not failed[0]:failed[0]=True;raise OSError('projection fault')
    return real(path,*a,**k)
   with patch.object(ac,'atomic_write',side_effect=fault):r=handoff(root,out)
   self.assertIn('incomplete',r['legacy_projections']);self.assertTrue((resolve_generation(out)/'api.json').exists());recover_handoff(out);self.assertTrue((out/'api.json').exists())
 def test_readiness_waiver_not_verification(self):
  r=readiness(self.p,'review-ready');self.assertFalse(r['profile_satisfied']);self.assertEqual(r['dimensions']['runtime_verification'],'not run')
 def test_openapi_positive_fields_and_negative_shapes(self):
  p=copy.deepcopy(self.p['api_contract']);p['paths']['/records']['parameters']=[];p['paths']['/records']['summary']='ok';self.assertEqual(openapi_checks(p),[])
  self.assertTrue(openapi_checks([]));p['paths']['/records']['get']['responses']={};self.assertTrue(openapi_checks(p))
 def test_cli_bad_api_returns_json_not_traceback(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'api.json';f.write_text('[]');r=self.cli('validate',f);self.assertEqual(r.returncode,1);self.assertFalse(json.loads(r.stdout)['ok']);self.assertNotIn('Traceback',r.stderr)
 def test_optional_full_gate_cannot_hide_unavailable_tools(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'a.mmd';f.write_text('flowchart TD\n a-->b\n')
   with patch('validation_engine.shutil.which',return_value=None):r=validate(f,True,gate='full')
   self.assertFalse(r['policy_ok']);self.assertTrue(r['skipped'])
 def test_renderer_attempt_not_suppressed_by_heuristic(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'a.mmd';f.write_text('unsupported-new-syntax\n')
   with patch('validation_engine.shutil.which',return_value='/configured/mmdc'),patch('validation_engine.bounded_process',return_value={'status':'timed_out','output':''}) as worker:
    r=validate(f,True)
   self.assertTrue(worker.called);self.assertTrue(any(x['status']=='timed_out' for x in r['checks']))
 def test_timeout_retains_other_file_results(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'a.mmd').write_text('flowchart TD\n a-->b');(root/'z.json').write_text('{}')
   with patch('validation_engine.shutil.which',return_value='/configured/mmdc'),patch('validation_engine.bounded_process',return_value={'status':'timed_out','output':''}):r=validate(root,True)
   self.assertTrue(any(x['file']=='z.json' and x['status']=='passed' for x in r['checks']))
 def test_external_refs_blocked(self):
  p=copy.deepcopy(self.p['api_contract']);p['paths']['/x']={'$ref':'https://example.invalid/spec'};self.assertTrue(openapi_checks(p))
 def test_scanner_ci_and_relevant_quota(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'.github/workflows').mkdir(parents=True);(root/'.github/workflows/ci.yml').write_text('jobs: {}')
   for i in range(410):(root/(str(i)+'.txt')).write_text('noise')
   (root/'app.py').write_text('import os\n'*8+'@app.get("/late")\ndef f():pass\n')
   r=repo_scan(root,limit=2);self.assertEqual(r['scanned_count'],2);self.assertTrue(any('.github/' in x['path'] for x in r['observed_files']));self.assertTrue(any(x.get('route')=='/late' for x in r['static_declarations']))
 def test_scanner_comments_not_routes(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'a.py').write_text('# @app.get("/false")\ntext="@app.get(fake)"\n')
   self.assertEqual(repo_scan(root)['static_declarations'],[])
 @unittest.skipUnless(hasattr(os,'mkfifo'),'FIFO scope')
 def test_special_file_not_opened_and_entry_budget_honest(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);os.mkfifo(root/'blocked.py');r=repo_scan(root,max_entries=1);self.assertEqual(r['bytes_read'],0);self.assertTrue(any('special' in x['reason'] for x in r['omissions']))
   for i in range(20):(root/(str(i)+'.py')).write_text('')
   r=repo_scan(root,max_entries=2);self.assertFalse(r['enumeration_complete']);self.assertIsNone(r['total_candidate_files'])
 def test_cache_parity_and_fitness_counterexample(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'repo';root.mkdir();(root/'a.py').write_text('import forbidden.module\n');cache=Path(t)/'cache.json'
   a=repo_scan(root,cache=cache);b=repo_scan(root,cache=cache);self.assertEqual(a['dependency_edges'],b['dependency_edges']);self.assertEqual(b['cache_hits'],1)
   p=copy.deepcopy(self.p);p['fitness_rules']=[{'id':'RULE-001','kind':'forbid_import','source_prefix':'a.py','target_prefix':'forbidden'}];self.assertEqual(fitness(p,b)['rules'][0]['status'],'violation')
 def test_cache_preserves_unrelated_file(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'repo';root.mkdir();cache=Path(t)/'notes.json';original='{"notes":"keep me"}';cache.write_text(original)
   with self.assertRaisesRegex(ValueError,'preserved'):repo_scan(root,cache=cache)
   self.assertEqual(cache.read_text(),original)
 def test_nonstring_operation_id_is_typed_error(self):
  p=copy.deepcopy(self.p);p.pop('api_contract',None);p['interfaces'][0]['operation']={'operationId':[],'responses':{'200':{'description':'ok'}}}
  with self.assertRaisesRegex(ValueError,'operationId'):compile_plan(p)
 def test_numeric_overflow_nan_and_nonfinite_weights(self):
  d=read_json(BASE/'examples/capacity.json');d['peak_factor']=1e308
  with self.assertRaises(ValueError):capacity(d)
  w={**DIMENSIONS,'security':math.nan}
  with self.assertRaises(ValueError):score({'weights':w})
 def test_evaluation_gate_and_deterministic_length(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);cases={'cases':[{'id':'long','checks':[{'id':'length','max_chars':20}]}]};(r/'cases.json').write_text(json.dumps(cases));(r/'responses.json').write_text(json.dumps({'long':'x'*50}))
   out=self.cli('evaluate','--cases',r/'cases.json','--responses',r/'responses.json','--gate');self.assertEqual(out.returncode,1)
 def test_pathological_regex_times_out_without_false_pass(self):
  r=evaluate_cases({'cases':[{'id':'red','checks':[{'any_of':['(a+)+$']}]}]},{'red':'a'*40+'!'})
  self.assertEqual(r['checks_passed'],0);self.assertEqual(r['cases'][0]['checks'][0]['status'],'timed_out')
 def test_sqlite_allowlist_and_planning_tools(self):
  p=copy.deepcopy(self.p);p['data_models']=[{'id':'DATA-001','dialect':'sqlite','table':'records','columns':[{'name':'id','type':'INTEGER','primary_key':True}]}];p['decisions'][0]['data_models']=[];p['tasks'][0]['data_models']=[]
  self.assertEqual(sqlite_schema_check(p)['status'],'passed');self.assertIn('plan only',specialist_plan(p,'review')['status']);self.assertIn('no participants',research_kit()['status'])
 def test_dry_run_writes_nothing(self):
  with tempfile.TemporaryDirectory() as t:
   root=self.root(t);out=Path(t)/'out';r=handoff(root,out,dry_run=True);self.assertFalse(out.exists());self.assertIn('planned',r['status'])
 def test_default_disclosure_redacts_and_private_backup_preserves(self):
  p=copy.deepcopy(self.p);p['requirements'][0]['description']='Export token=TEST_ONLY_SECRET_ABC safely';p['private_extension']={'password':'do-not-share'}
  files,report=compile_plan(p);self.assertNotIn('TEST_ONLY_SECRET_ABC',files['requirements.md']);self.assertNotIn('private_extension',json.loads(files['project.json']));self.assertTrue(report['redactions'])
  private,_=compile_plan(p,include_private=True);self.assertEqual(json.loads(private['project.json']),p)
 def test_js_static_import_adapter_ignores_comments_and_templates(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'a.ts').write_text('// import x from "false"\nconst s=`\nimport x from "false2"\n`;\nimport { real } from "module";\n')
   r=repo_scan(root);self.assertEqual([d['target'] for d in r['static_declarations']],['module'])
 def test_actual_worker_timeout(self):
  r=bounded_process([sys.executable,'-c','import time;time.sleep(2)'],timeout=.1)
  self.assertEqual(r['status'],'timed_out')
 @unittest.skipUnless(importlib.util.find_spec('openapi_spec_validator'),'optional full OpenAPI validator unavailable')
 def test_actual_full_schema_worker(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'api.json';f.write_text(dumps(self.p['api_contract']));r=validate(f,full_openapi=True,gate='full');self.assertTrue(r['policy_ok'],r)
   self.assertTrue(any(c['check']=='OpenAPI full schema' and c['status']=='passed' for c in r['checks']))
 def test_cross_surface_capacity_cases(self):
  import shutil
  if not shutil.which('node'):self.skipTest('Node unavailable')
  d=read_json(BASE/'examples/capacity.json');cases=[{**d,'daily_requests':86400*i,'peak_factor':i+1,'assumed_compute_price_per_hour':.011,'assumed_storage_price_per_gb_month':.06,'assumed_egress_price_per_gb':.09} for i in (1,2,7,11)]
  script='const C=require('+json.dumps(str(BASE/'workbench/project-core.js'))+');let s="";process.stdin.on("data",x=>s+=x);process.stdin.on("end",()=>console.log(JSON.stringify(JSON.parse(s).map(C.capacity))));'
  child=subprocess.run(['node','-e',script],input=json.dumps(cases),capture_output=True,text=True,timeout=5);self.assertEqual(child.returncode,0,child.stderr)
  for case,j in zip(cases,json.loads(child.stdout)):
   py=capacity(case)
   for key,value in j.items():self.assertAlmostEqual(value,py[key],places=4,msg=key)

if __name__=='__main__':unittest.main()
