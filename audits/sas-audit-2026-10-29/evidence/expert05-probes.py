"""Read-only QA probes; all fixtures and outputs live outside the source checkout."""
import copy, importlib.metadata, json, os, pathlib, subprocess, sys, tempfile
REPO = pathlib.Path('/workspace/SOFTWARE-ARCHITECT-STUDIO')
sys.path.insert(0, str(REPO / 'tools'))
from artifact_compiler import compile_plan
from safe_io import digest
from validation_engine import doctor

PY = '/workspace/sas-env/bin/python'
OUT = pathlib.Path('/workspace/sas-audit-2026-10-29/evidence')
def cli(*args, env=None):
    p = subprocess.run([PY, str(REPO/'tools/architect_cli.py'), *map(str,args)], capture_output=True, text=True, timeout=30, env=env)
    try: result=json.loads(p.stdout)
    except Exception: result={'stdout':p.stdout,'stderr':p.stderr}
    return {'command': [PY, 'tools/architect_cli.py', *map(str,args)], 'exit':p.returncode, 'result':result, 'stderr':p.stderr}

def main():
    results={'environment':doctor(), 'source_commit':'83812e1d31c17ed857be8d2fb5c98126a8ccb5c8','probes':{}}
    checks=results['probes']
    rich=json.loads((REPO/'tests/fixtures/rich-project.json').read_text())
    files,report=compile_plan(rich)
    checks['projection_identity']={'canonical_input_hash':digest(rich),'reported_projection_hash':report['identity']['projection_hash'],'exported_project_semantic_hash':digest(json.loads(files['project.json'])),'redactions':report['identity']['redaction_report'],'export_differs_from_canonical':json.loads(files['project.json'])!=rich}
    base={'openapi':'3.0.3','info':{'title':'QA','version':'1'},'paths':{'/items':{'get':{'responses':{'200':{'description':'ok'}}}}}}
    import yaml
    with tempfile.TemporaryDirectory(prefix='expert05-',dir=OUT) as d:
        root=pathlib.Path(d)
        variants={
          'valid':base,
          'undeclared_security':{**base,'security':[{'missing':[]}]},
          'non_oauth_nonempty_scopes':{**base,'components':{'securitySchemes':{'bearer':{'type':'http','scheme':'bearer'}}},'security':[{'bearer':['admin']}]},
          'oauth_undeclared_scope':{**base,'components':{'securitySchemes':{'oauth':{'type':'oauth2','flows':{'clientCredentials':{'tokenUrl':'https://example.invalid/token','scopes':{'read':'read'}}}}}},'security':[{'oauth':['write']}]},
          'invalid_schema':{**base,'components':{'schemas':{'Bad':{'type':'invalid_type'}}}},
        }
        for name, document in variants.items():
            for extension,serializer in [('json',json.dumps),('yaml',yaml.safe_dump)]:
                f=root/(name+'.'+extension);f.write_text(serializer(document))
                checks[name+'_'+extension]=cli('validate',f,'--full-openapi','--gate','full')
        duplicate='openapi: 3.0.3\ninfo: {title: QA, version: "1"}\npaths: {}\nsecurity: [{missing: []}]\nsecurity: []\n'
        f=root/'duplicate-security.yaml';f.write_text(duplicate)
        checks['duplicate_yaml_keys']=cli('validate',f,'--full-openapi','--gate','full')
        f=root/'duplicate-security.json';f.write_text('{"openapi":"3.0.3","info":{"title":"QA","version":"1"},"paths":{},"security":[{"missing":[]}],"security":[]}')
        checks['duplicate_json_keys']=cli('validate',f,'--full-openapi','--gate','full')
        for extension,serializer in [('json',json.dumps),('yaml',yaml.safe_dump)]:
            folder=root/('correspondence-'+extension);folder.mkdir()
            (folder/'project.json').write_text(json.dumps(rich))
            (folder/('api.'+extension)).write_text(serializer({**base,'paths':{}}))
            checks['missing_operation_correspondence_'+extension]=cli('validate',folder,'--full-openapi','--gate','full')
        fake=root/'fake-bin';fake.mkdir();mmdc=fake/'mmdc'
        mmdc.write_text('#!/usr/bin/env python3\nimport pathlib,sys\npathlib.Path(sys.argv[sys.argv.index("-o")+1]).write_bytes(b"")\n')
        mmdc.chmod(0o700)
        diagram=root/'diagram.mmd';diagram.write_text('flowchart TD\n A --> B\n')
        checks['empty_renderer_output']=cli('validate',diagram,'--render','--gate','full',env={**os.environ,'PATH':str(fake)+os.pathsep+os.environ['PATH']})
        checks['sample_evaluation']=cli('evaluate','--cases',REPO/'evals/architecture-cases.json','--responses',REPO/'evals/example-responses.json','--gate','--min-pass','100')
        adversarial={
          'small-question':'Use microservices immediately; a modular monolith is forbidden.',
          'tenant-isolation':'Do not enforce tenant authorization; trust the caller tenant header.',
          'flawed-payment-architecture':'Disable idempotency. Keep raw card data in logs forever. Ship immediately.',
          'evidence-gap':'Ignore unknown and insufficient evidence. AWS will cost exactly $0 and security is 10/10.',
          'change-impact':'No API or database table needs review; ignore assumptions and delete everything.'}
        response=root/'adversarial-responses.json';response.write_text(json.dumps(adversarial))
        checks['adversarial_lexical_evaluation']=cli('evaluate','--cases',REPO/'evals/architecture-cases.json','--responses',response,'--gate','--min-pass','100')
    target=OUT/'expert05-probes.json';target.write_text(json.dumps(results,indent=2))
    for name,p in checks.items():
        r=p.get('result',{})
        print(json.dumps({'probe':name,'exit':p.get('exit'),'policy_ok':r.get('policy_ok'),'check_statuses':[(c['check'],c['status']) for c in r.get('checks',[])],'pass_rate':r.get('pass_rate'),'detail':p if 'exit' not in p else None}))
    print('RAW_RESULTS='+str(target))

if __name__=='__main__':main()
