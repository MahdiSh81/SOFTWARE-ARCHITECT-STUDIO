"""Read-only adapter/CLI probes; outputs remain outside the checkout."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path('/workspace/SOFTWARE-ARCHITECT-STUDIO')
sys.path.insert(0, str(REPO / 'tools'))
from integration_contracts import validate_capability_manifest, validate_tool_result
from jsonschema import Draft202012Validator, FormatChecker
from validation_engine import openapi_checks

SCHEMAS = {k: json.loads((REPO / 'schemas' / f'{k}-v1.schema.json').read_text())
           for k in ('tool-capability', 'verification-receipt')}
MANIFEST = {'schema_version': 1, 'tool_id': 'ci.runner', 'tool_version': '1.0.0',
            'capabilities': [{'operation_id': 'run-tests', 'description': 'Run tests',
                              'permission_class': 'read', 'input_schema': {'type': 'object'},
                              'output_schema': {'type': 'object'}, 'idempotent': True,
                              'timeout_seconds': 60}]}
RECEIPT = {'operation_id': 'op-001', 'tool_id': 'ci.runner', 'tool_version': '1.0.0',
           'capability': 'run-tests', 'permission_class': 'read',
           'input_source_hash': 'a' * 64, 'input_schema_version': 1,
           'started_at': '2026-10-29T10:00:00Z', 'completed_at': '2026-10-29T10:00:01Z',
           'status': 'passed', 'output_hash': 'b' * 64,
           'checks_run': ['unit'], 'checks_not_run': [], 'warnings': [], 'errors': [],
           'limitations': []}
RESULTS = []

def probe(name, kind, value):
    fn = validate_capability_manifest if kind == 'tool-capability' else validate_tool_result
    try:
        actual = {'issues': fn(value)}
    except Exception as exc:
        actual = {'exception': type(exc).__name__, 'message': str(exc)}
    schema = Draft202012Validator(SCHEMAS[kind], format_checker=FormatChecker())
    schema_errors = [e.message for e in schema.iter_errors(value)]
    RESULTS.append({'name': name, 'custom': actual, 'json_schema_issues': schema_errors})

probe('baseline_manifest', 'tool-capability', MANIFEST)
probe('baseline_receipt', 'verification-receipt', RECEIPT)
v = copy.deepcopy(MANIFEST); v['extra_authority'] = 'deploy'; probe('manifest_unknown_root', 'tool-capability', v)
v = copy.deepcopy(MANIFEST); v['capabilities'][0]['secret'] = 'not-a-real-secret'; probe('manifest_unknown_capability', 'tool-capability', v)
v = copy.deepcopy(MANIFEST); v['schema_version'] = True; probe('manifest_boolean_version', 'tool-capability', v)
v = copy.deepcopy(MANIFEST); v['capabilities'].append(copy.deepcopy(v['capabilities'][0])); probe('manifest_duplicate_id', 'tool-capability', v)
v = copy.deepcopy(MANIFEST); v['capabilities'][0]['input_schema'] = {'type': 42}; probe('manifest_invalid_embedded_schema', 'tool-capability', v)
v = copy.deepcopy(MANIFEST); v['capabilities'][0]['permission_class'] = []; probe('manifest_unhashable_permission', 'tool-capability', v)
v = copy.deepcopy(RECEIPT); v['extra_authority'] = 'deploy'; probe('receipt_unknown_field', 'verification-receipt', v)
v = copy.deepcopy(RECEIPT); v['artifact_refs'] = 42; probe('receipt_bad_artifact_refs', 'verification-receipt', v)
v = copy.deepcopy(RECEIPT); v['authorization_reference'] = 42; probe('receipt_bad_optional_authorization', 'verification-receipt', v)
v = copy.deepcopy(RECEIPT); v['output_hash'] = None; probe('receipt_passed_null_hash', 'verification-receipt', v)
v = copy.deepcopy(RECEIPT); v['started_at'] = '2026-10-29 10:00:00Z'; probe('receipt_non_rfc3339_timestamp', 'verification-receipt', v)
v = copy.deepcopy(RECEIPT); v['completed_at'] = '2026-10-29T09:00:00Z'; probe('receipt_reversed_time', 'verification-receipt', v)
v = copy.deepcopy(RECEIPT); v['status'] = {}; probe('receipt_unhashable_status', 'verification-receipt', v)
v = copy.deepcopy(RECEIPT); v['permission_class'] = []; probe('receipt_unhashable_permission', 'verification-receipt', v)

def cli(argv):
    result = subprocess.run([sys.executable, str(REPO / 'tools/architect_cli.py'), *map(str, argv)],
                            capture_output=True, text=True, cwd=REPO,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=20)
    def parsed(value):
        try: return json.loads(value)
        except ValueError: return value
    return {'exit': result.returncode, 'stdout': parsed(result.stdout), 'stderr': parsed(result.stderr)}

with tempfile.TemporaryDirectory(prefix='sas-expert08-') as tmp:
    root = Path(tmp)
    bad = root / 'bad-capability.json'; bad.write_text(json.dumps({'schema_version': 1, 'capabilities': []}))
    RESULTS.append({'name': 'cli_full_gate_invalid_capability', **cli(['validate', bad, '--gate', 'full'])})
    api = root / 'api.json'; api.write_text(json.dumps({'openapi': '3.0.3', 'info': {}, 'paths': {}}))
    receipt = root / 'failed-gate-receipt.json'
    result = cli(['--receipt', receipt, 'validate', api, '--gate', 'structural'])
    result['receipt'] = json.loads(receipt.read_text())
    result['receipt_contract_issues'] = validate_tool_result(result['receipt'])
    RESULTS.append({'name': 'cli_failed_gate_receipt', **result})
    target = root / 'missing'; receipt = root / 'error-receipt.json'
    result = cli(['--receipt', receipt, 'resume', target]); result['receipt_exists'] = receipt.exists()
    RESULTS.append({'name': 'cli_input_error_no_receipt', **result})
    receipt_dir = root / 'receipt-directory'; receipt_dir.mkdir(); project = root / 'project'
    result = cli(['--receipt', receipt_dir, 'init', project, '--name', 'Receipt failure test'])
    result['project_exists_after_error'] = (project / 'project.json').exists()
    RESULTS.append({'name': 'cli_receipt_failure_after_init', **result})
    RESULTS.append({'name': 'cli_parse_error', **cli(['resume'])})

print(json.dumps({'python': sys.version.split()[0], 'results': RESULTS}, indent=2))
