"""Worker for optional installed validators. No automatic installs or remote refs."""
import json,sys
from pathlib import Path
if __name__=='__main__':
    try:
        mode=sys.argv[1];text=Path(sys.argv[2]).read_text()
        if mode=='yaml':
            import yaml
            print(json.dumps(yaml.safe_load(text),allow_nan=False));sys.exit(0)
        data=json.loads(text)
        if mode=='openapi':
            from openapi_spec_validator import validate_spec
            from validation_engine import _external_refs
            if _external_refs(data):raise ValueError('external references forbidden')
            validate_spec(data)
        elif mode=='project':
            from jsonschema import Draft202012Validator
            schema=json.loads((Path(__file__).resolve().parents[1]/'schemas/project-v2.schema.json').read_text())
            Draft202012Validator(schema).validate(data)
        else:raise ValueError('unknown validator')
        print(json.dumps({'status':'passed'}))
    except Exception as e:
        print(json.dumps({'status':'failed','error':type(e).__name__+': '+str(e)[:1500]}));sys.exit(1)
