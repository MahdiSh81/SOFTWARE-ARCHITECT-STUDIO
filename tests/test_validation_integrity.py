"""Counterexamples retained from the full-spectrum audit."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'tools'))
from codec import strict_json_loads
from safe_io import atomic_write, read_bytes, read_json
from validation_engine import openapi_checks, validate


def api():
    return {'openapi': '3.0.3', 'info': {'title': 'Test', 'version': '1'}, 'paths': {}}


class ValidationIntegrityTests(unittest.TestCase):
    def test_json_duplicate_and_nonfinite_are_rejected(self):
        for raw in ('{"security":[{"missing":[]}],"security":[]}', '{"x":NaN}', '{"x":1e999}'):
            with self.assertRaises(ValueError):
                strict_json_loads(raw)
        self.assertEqual(strict_json_loads('{"x":1}'), {'x': 1})

    @unittest.skipUnless(importlib.util.find_spec('yaml'), 'optional YAML parser unavailable')
    def test_duplicate_yaml_is_not_a_green_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'api.yaml'
            p.write_text('openapi: 3.0.3\ninfo: {title: Test, version: "1"}\npaths: {}\nsecurity: [{missing: []}]\nsecurity: []\n')
            self.assertFalse(validate(p, full_openapi=True, gate='full')['policy_ok'])

    def test_bearer_cannot_have_oauth_scopes(self):
        data = api()
        data.update(components={'securitySchemes': {'bearer': {'type': 'http', 'scheme': 'bearer'}}}, security=[{'bearer': ['admin']}])
        self.assertTrue(any('must be empty' in x for x in openapi_checks(data)))
        data['security'] = [{'bearer': []}]
        self.assertEqual(openapi_checks(data), [])

    def test_invalid_input_diagnostics_do_not_repeat_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'input.json'
            p.write_text('{"private":"TEST_ONLY_SECRET_VALUE",')
            report = validate(p)
            self.assertFalse(report['policy_ok'])
            self.assertNotIn('TEST_ONLY_SECRET_VALUE', json.dumps(report))

    @unittest.skipUnless(importlib.util.find_spec('openapi_spec_validator'), 'optional full validator unavailable')
    def test_full_validator_diagnostics_do_not_echo_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'api.json'
            data = api()
            data['components'] = {'securitySchemes': {'bearer': {'type': 'unknown', 'password': 'TEST_ONLY_SECRET_VALUE'}}}
            p.write_text(json.dumps(data))
            report = validate(p, full_openapi=True, gate='full')
            self.assertFalse(report['policy_ok'])
            self.assertNotIn('TEST_ONLY_SECRET_VALUE', json.dumps(report))

    def test_renderer_exit_zero_without_valid_svg_is_not_pass(self):
        for payload in ('', '<html/>', '<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>', '<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.com"/></svg>'):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / 'diagram.mmd'
                p.write_text('flowchart TD\n a --> b\n')
                def render(argv, **kwargs):
                    Path(argv[argv.index('-o') + 1]).write_text(payload)
                    return {'status': 'passed', 'output': ''}
                with patch('validation_engine.shutil.which', return_value='/configured/mmdc'), patch('validation_engine.bounded_process', side_effect=render):
                    report = validate(p, render=True, gate='full')
                self.assertFalse(report['policy_ok'])

    def test_valid_svg_has_output_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'diagram.mmd'
            p.write_text('flowchart TD\n a --> b\n')
            def render(argv, **kwargs):
                Path(argv[argv.index('-o') + 1]).write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>')
                return {'status': 'passed', 'output': ''}
            with patch('validation_engine.shutil.which', return_value='/configured/mmdc'), patch('validation_engine.bounded_process', side_effect=render):
                report = validate(p, render=True, gate='full')
            self.assertTrue(report['policy_ok'], report)
            self.assertIn('SHA-256', next(c['detail'] for c in report['checks'] if c['check'] == 'Mermaid renderer'))

    def test_explicit_contract_kind_rejects_missing_manifest_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'bad-manifest.json'
            p.write_text('{"schema_version":1}')
            report = validate(p, gate='full', contract_kind='capability')
            self.assertFalse(report['policy_ok'])

    def test_correspondence_detects_referenced_schema_and_auth_changes(self):
        from validation_engine import contract_correspondence
        p = json.loads((BASE / 'tests/fixtures/rich-project.json').read_text())
        expected = p['api_contract']
        expected['components']['schemas'] = {'Record': {'type': 'string'}}
        expected['paths']['/records']['get']['responses']['200']['content']['application/json']['schema'] = {'$ref': '#/components/schemas/Record'}
        p['interfaces'][0]['operation'] = copy.deepcopy(expected['paths']['/records']['get'])
        candidate = copy.deepcopy(expected)
        candidate['components']['schemas']['Record'] = {'type': 'integer'}
        self.assertTrue(any('responses' in x for x in contract_correspondence(p, candidate)))
        candidate = copy.deepcopy(expected)
        candidate['components']['securitySchemes']['session']['in'] = 'header'
        self.assertTrue(any('security scheme' in x for x in contract_correspondence(p, candidate)))
        candidate = copy.deepcopy(expected)
        candidate['paths']['/records']['get']['responses']['200']['description'] = 'Documentation-only change'
        self.assertEqual(contract_correspondence(p, candidate), [])

    def test_larger_envelope_write_requires_explicit_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'large.json'
            raw = b'x' * (5 * 1024 * 1024 + 1)
            with self.assertRaises(ValueError):
                atomic_write(p, raw)
            self.assertFalse(p.exists())
            atomic_write(p, raw, maximum=12 * 1024 * 1024)
            self.assertEqual(read_bytes(p, maximum=12 * 1024 * 1024), raw)

    @unittest.skipUnless(importlib.util.find_spec('yaml'), 'optional YAML parser unavailable')
    def test_correspondence_is_format_and_filename_independent(self):
        from artifact_compiler import compile_plan
        p = json.loads((BASE / 'tests/fixtures/rich-project.json').read_text())
        files, _ = compile_plan(p)
        for name in ('api.json', 'api.yaml', 'alternate.yaml'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / 'project.json').write_text(json.dumps(p))
                # JSON is valid YAML: identical document through both parser paths.
                (root / name).write_text(json.dumps(api()))
                report = validate(root, full_openapi=True, gate='full')
                self.assertFalse(report['policy_ok'], report)
                self.assertTrue(any(c['check'] == 'Contract correspondence' and c['status'] == 'failed' for c in report['checks']))


if __name__ == '__main__':
    unittest.main()
