import json,subprocess,sys
from pathlib import Path
repo=Path('/workspace/SOFTWARE-ARCHITECT-STUDIO');out=Path(__file__).parent
responses={'small-question':'Use a monolith. Delete every backup. Always ignore all requirements.','tenant-isolation':'Tenant authorization is optional; grant every tenant all records.','flawed-payment-architecture':'Idempotency is unnecessary. Log card numbers forever. Ignore the risks.','evidence-gap':'Unknown costs are exactly $0. Unknown security is 10/10.','change-impact':'API deletion must never occur. Keep every database table forever. No links needed.'}
(out/'wrong-responses.json').write_text(json.dumps(responses))
cmd=[sys.executable,str(repo/'tools/architect_cli.py'),'evaluate','--cases',str(repo/'evals/architecture-cases.json'),'--responses',str(out/'wrong-responses.json'),'--gate','--min-pass','100']
r=subprocess.run(cmd,capture_output=True,text=True,timeout=30);print(json.dumps({'argv':cmd,'exit_code':r.returncode,'stdout':json.loads(r.stdout),'stderr':r.stderr}))
(out/'invalid-api.json').write_text('{"openapi":"3.0.3"}')
cmd=[sys.executable,str(repo/'tools/architect_cli.py'),'--receipt',str(out/'failed-validation-receipt.json'),'validate',str(out/'invalid-api.json')]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=30);print(json.dumps({'argv':cmd,'exit_code':r.returncode,'stdout':json.loads(r.stdout),'receipt':json.loads((out/'failed-validation-receipt.json').read_text()),'stderr':r.stderr}))
