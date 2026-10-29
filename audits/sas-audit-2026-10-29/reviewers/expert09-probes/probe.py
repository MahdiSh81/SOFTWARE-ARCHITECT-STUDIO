"""Focused read-only operations probes; outputs only outside the frozen checkout."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest

ROOT = Path('/workspace/SOFTWARE-ARCHITECT-STUDIO')
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from repository_evidence import repo_scan
from validation_engine import doctor

def run(args):
    p = subprocess.run(args, cwd=OUT, capture_output=True, text=True, timeout=15,
                       env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    return {'argv': args, 'exit_code': p.returncode,
            'stdout': p.stdout, 'stderr': p.stderr}

tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
manifest = json.loads((ROOT / 'release/source-manifest.json').read_text())
listed = manifest['files']
result = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'doctor': doctor(), 'tracked_count': len(tracked), 'manifest_count': len(listed),
          'manifest_missing_paths': sorted(p for p in listed if not (ROOT / p).is_file()),
          'manifest_changed_paths': sorted(p for p, h in listed.items() if (ROOT / p).is_file()
                                           and hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h),
          'manifest_unlisted_tracked_paths': sorted(set(tracked) - set(listed) - {'release/source-manifest.json'}),
          'python_discovered_count': unittest.defaultTestLoader.discover(str(ROOT / 'tests')).countTestCases(),
          'python_static_test_methods': sum(sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                                               and n.name.startswith('test') for n in ast.walk(ast.parse(p.read_text())))
                                            for p in (ROOT / 'tests').glob('test_*.py')),
          'node_static_sync_calls': len(re.findall(r'^test\(', (ROOT / 'tests/test_workbench.cjs').read_text(), re.M)),
          'node_static_async_checks': len(set(re.findall(r"name:'(failed oversized-envelope[^']+)'", (ROOT / 'tests/test_workbench.cjs').read_text()))),
          'browser_static_test_calls': len(re.findall(r'\btest\(', (ROOT / 'tests/browser/workbench.spec.cjs').read_text()))}
result['missing_manifest_script'] = run([sys.executable, str(ROOT / 'tools/check_source_manifest.py'), '--check'])
bad = OUT / 'invalid-input'; bad.mkdir(exist_ok=True)
(bad / 'bad.json').write_text('{broken')
receipt = OUT / 'failed-validation-receipt.json'
result['invalid_validation'] = run([sys.executable, str(ROOT / 'tools/architect_cli.py'),
                                    '--receipt', str(receipt), 'validate', str(bad), '--gate', 'structural'])
result['failed_validation_receipt'] = json.loads(receipt.read_text())
cache = OUT / 'scan-cache.json'
if cache.exists():
    cache.unlink()
for label in ('cold', 'warm'):
    begin = time.monotonic()
    scan = repo_scan(ROOT, cache=cache)
    result['scan_' + label] = {k: scan[k] for k in ('scanned_count', 'entries_visited', 'eligible_discovered',
               'bytes_read', 'skipped_files', 'enumeration_complete', 'coverage', 'stop_reasons', 'cache_hits', 'source_fingerprint')}
    result['scan_' + label].update(duration_seconds=round(time.monotonic() - begin, 6),
                                  declarations=len(scan['static_declarations']), edges=len(scan['dependency_edges']))
small = OUT / 'bounded-input'; small.mkdir(exist_ok=True)
for i in range(4):
    (small / f'item{i}.py').write_text('import os\n')
scan = repo_scan(small, max_entries=2)
result['bounded_scan'] = {k: scan[k] for k in ('entries_visited', 'total_candidate_files', 'discovered_files',
                                           'enumeration_complete', 'coverage', 'stop_reasons')}
descriptor = OUT / 'invalid-descriptor'; descriptor.mkdir(exist_ok=True)
(descriptor / 'compose.yaml').write_text('services:\n  web: [\n')
scan = repo_scan(descriptor)
result['invalid_descriptor_scan'] = {k: scan[k] for k in ('scanned_count', 'observed_files', 'static_declarations',
                                  'dependency_edges', 'omissions', 'coverage', 'stop_reasons')}
result['git_status_after'] = subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True)
(OUT / 'evidence.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, indent=2, sort_keys=True))
