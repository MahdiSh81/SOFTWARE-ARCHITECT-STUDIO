import json,sys,hashlib,tempfile
from pathlib import Path
sys.path.insert(0,'/workspace/SOFTWARE-ARCHITECT-STUDIO/tools')
from project_model import VERSION,new_project,project_checks,resume_packet,supersede
from workflow_tools import capture_response,capture_summary,record_run
from artifact_compiler import compile_plan
from safe_io import digest
repo=Path('/workspace/SOFTWARE-ARCHITECT-STUDIO')
out={}
p=new_project('Governance probe');p['decisions']=[{'id':'ADR-001','status':'Accepted','title':'Use SQL','decision':'Use SQLite','approval_origin':{'approver':'historical user','source':'old-session'}}]
q=supersede(p,'ADR-001','ADR-002','new evidence')
out['supersession_origin']={'replacement':q['decisions'][1],'resume':resume_packet(q)}
r=supersede(q,'ADR-001','ADR-003','second successor of same predecessor')
out['repeated_supersession']={'errors':project_checks(r),'decisions':r['decisions']}
bad=new_project('Broken provenance');bad['decisions']=[{'id':'ADR-001','status':'Accepted','decision':'Use SQL','supersedes':'ADR-999','superseded_by':'ADR-777','approval_origin':False}]
out['invalid_lifecycle_accepted']={'errors':project_checks(bad),'resume':resume_packet(bad)}
c=capture_response('actual prompt fixture','actual response fixture','unknown','skillhash')
out['capture_fields']=sorted(c)
out['malformed_summary']=capture_summary([{'id':'same','reviews':['not a rubric']},{'id':'same','reviews':[{}]}])
with tempfile.TemporaryDirectory() as tmp:
 receipt=record_run(Path(tmp)/'receipt.json','validate',{'policy_ok':False,'ok':False,'checks':[{'status':'failed'}]},.1)
 out['failed_gate_receipt']=receipt
fixture=json.loads((repo/'tests/fixtures/rich-project.json').read_text());files,report=compile_plan(fixture)
out['projection_identity']={'canonical_input_hash':report['identity']['canonical_input_hash'],'projection_hash':report['identity']['projection_hash'],'exported_project_semantic_hash':digest(json.loads(files['project.json'])),'artifact_project_bytes_hash':report['identity']['artifact_hashes']['project.json'],'opaque_fixture_keys':sorted(set(fixture)-set(json.loads(files['project.json'])))}
manifest=json.loads((repo/'release/source-manifest.json').read_text())
# Match source manifest map without assuming its key name.
entries=next(v for v in manifest.values() if isinstance(v,dict) and all(isinstance(h,str) and len(h)==64 for h in v.values()))
mismatches=[name for name,h in entries.items() if (repo/name).exists() and hashlib.sha256((repo/name).read_bytes()).hexdigest()!=h]
out['release_manifest']={'declared_release':manifest.get('release'),'current_cli_version':VERSION,'tracked_entries':len(entries),'hash_mismatches':mismatches,'manifest_keys':list(manifest)}
out['metadata_versions']={f:json.loads((repo/f).read_text()).get('version',json.loads((repo/f).read_text()).get('release')) for f in ['plugin.json','.claude-plugin/plugin.json','capabilities.json','IMPLEMENTATION_STATUS.json','release/verification.json'] if (repo/f).exists()}
print(json.dumps(out,ensure_ascii=False,indent=2))
