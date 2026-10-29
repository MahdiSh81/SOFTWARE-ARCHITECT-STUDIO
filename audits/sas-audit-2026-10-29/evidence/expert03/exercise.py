import json, os, subprocess, sys
from pathlib import Path
repo=Path('/workspace/SOFTWARE-ARCHITECT-STUDIO')
sys.path.insert(0,str(repo/'tools'))
from safe_io import digest
from integration_contracts import validate_tool_result
from jsonschema import Draft202012Validator
base=Path('/tmp/sas-expert03-audit')
root=base/'task-tracker'
cli=[sys.executable,str(repo/'tools/architect_cli.py')]
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
results={}
def run(label,*args):
    r=subprocess.run(cli+list(args),cwd=base,env=env,text=True,capture_output=True)
    (base/(label+'.stdout')).write_text(r.stdout)
    (base/(label+'.stderr')).write_text(r.stderr)
    try: value=json.loads(r.stdout or r.stderr)
    except json.JSONDecodeError: value={'stdout':r.stdout,'stderr':r.stderr}
    results[label]={'returncode':r.returncode,'result':value}
    return value
(base/'idea.txt').write_text('A personal offline task tracker: add, list, complete tasks; SQLite persists across runs; reject empty titles; no network, authentication, or deployment.\n')
run('01-init','init',str(root),'--name','Offline Task Tracker')
run('02-empty-readiness','readiness',str(root),'--profile','review-ready')
p=json.loads((root/'project.json').read_text())
p.update(brief=(base/'idea.txt').read_text().strip(),constraints=['Python 3.12 standard library only; SQLite; local CLI','No remote service, auth or deployment; data stays in selected local DB'],open_questions=['Exact package/distribution method remains proposed'])
p['requirements']=[{'id':'FR-001','description':'Add and list persisted tasks.','acceptance':'Add a title in one process; another process lists that title exactly once.','status':'Proposed'},{'id':'FR-002','description':'Complete a known task; reject missing ID and empty titles.','acceptance':'Complete by integer ID; list shows done; invalid input returns nonzero without changing stored tasks.','status':'Proposed'}]
p['components']=[{'id':'CMP-CLI','name':'CLI','responsibility':'Parse commands; validate input; render result and error exit codes.','requirements':['FR-001','FR-002'],'files':['src/tasks/cli.py','src/tasks/__main__.py']},{'id':'CMP-STORE','name':'Task Store','responsibility':'Own SQLite schema and transactional task persistence.','requirements':['FR-001','FR-002'],'files':['src/tasks/store.py']}]
p['interfaces']=[{'id':'IFACE-CLI','name':'Command interface','method':'CLI','components':['CMP-CLI'],'requirements':['FR-001','FR-002'],'contract':{'commands':['add TITLE','list','complete ID'],'error_exit':2,'db_argument':'--db PATH'}}]
p['data_models']=[{'id':'DATA-TASK','name':'Task','table':'tasks','dialect':'sqlite','components':['CMP-STORE'],'requirements':['FR-001','FR-002'],'columns':[{'name':'id','type':'INTEGER','primary_key':True},{'name':'title','type':'TEXT','nullable':False},{'name':'done','type':'INTEGER','nullable':False}]}]
p['decisions']=[{'id':'ADR-001','title':'Standard library local CLI','decision':'Use argparse and sqlite3; avoid third party dependencies for this limited offline workflow.','status':'Proposed','requirements':['FR-001','FR-002'],'alternatives':['Remote API rejected for offline scope'],'validation':'Implement subprocess integration tests against temporary SQLite file.'}]
p['tasks']=[{'id':'TASK-001','title':'Implement persistent task store','requirements':['FR-001','FR-002'],'components':['CMP-STORE'],'data_models':['DATA-TASK'],'decisions':['ADR-001'],'files':['src/tasks/store.py','tests/test_store.py'],'acceptance':'Temporary database tests prove add, list, complete and invalid-ID behavior.'},{'id':'TASK-002','title':'Implement CLI and integration tests','requirements':['FR-001','FR-002'],'components':['CMP-CLI'],'interfaces':['IFACE-CLI'],'decisions':['ADR-001'],'files':['src/tasks/cli.py','src/tasks/__main__.py','tests/test_cli.py'],'acceptance':'python -m unittest discover -s tests passes; separate subprocesses prove persistence and error exits.'}]
proposed=base/'proposed.json';proposed.write_text(json.dumps(p))
run('03-change','change','--baseline',str(root),'--proposed',str(proposed))
run('04-commit','commit',str(root),'--proposed',str(proposed),'--expected-hash',digest(json.loads((root/'project.json').read_text())),'--message','Record auditor-authored proposed implementation plan')
run('05-readiness','readiness',str(root),'--profile','review-ready')
run('06-dry-handoff','handoff',str(root),'--output',str(base/'handoff'),'--profile','review-ready','--dry-run')
h=run('07-handoff','handoff',str(root),'--output',str(base/'handoff'),'--profile','review-ready')
run('08-validate','validate',h['read_path'],'--gate','structural')
run('09-validate-full','validate',h['read_path'],'--render','--full-openapi','--gate','full')
run('10-data-check','data-check',str(root))
coverage=json.loads((root/'project.json').read_text())
coverage.update(components=[],interfaces=[],data_models=[],tasks=[])
(base/'requirements-only.json').write_text(json.dumps(coverage))
run('11-requirements-only-readiness','readiness',str(base/'requirements-only.json'),'--profile','review-ready')
receipt={'operation_id':'run-001','tool_id':'host.runner','tool_version':'1','capability':'run-tests','permission_class':'read','input_source_hash':'a'*64,'input_schema_version':1,'started_at':'2026-10-29T18:00:00Z','completed_at':'2026-10-29T18:00:01Z','status':'passed','output_hash':None,'checks_run':[],'checks_not_run':[],'warnings':[],'errors':[],'limitations':[]}
schema=json.loads((repo/'schemas/verification-receipt-v1.schema.json').read_text())
results['12-null-output-receipt']={'jsonschema_errors':[e.message for e in Draft202012Validator(schema).iter_errors(receipt)],'python_errors':validate_tool_result(receipt)}
(base/'results.json').write_text(json.dumps(results,indent=2))
print(json.dumps({'scratch':str(base),'result_codes':{k:v.get('returncode') for k,v in results.items()},'empty_review_ready':results['02-empty-readiness']['result']['profile_satisfied'],'planned_review_ready':results['05-readiness']['result']['profile_satisfied'],'requirements_only_review_ready':results['11-requirements-only-readiness']['result']['profile_satisfied'],'handoff_files':h['generated'],'structural_validation':results['08-validate']['result'],'full_validation':results['09-validate-full']['result'],'data_check':results['10-data-check']['result'],'receipt_mismatch':results['12-null-output-receipt']},indent=2))
