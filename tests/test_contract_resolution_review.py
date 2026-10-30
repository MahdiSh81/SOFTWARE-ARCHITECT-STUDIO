"""Independent review counterexamples for the new contract/hand-off boundary."""
import copy
import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'tools'))
from project_model import new_project, require_project
from contract_resolution import resolve_contracts, normalized
from artifact_compiler import compile_plan, readiness


def project():
    value = new_project('Working record application')
    value['requirements'] = [{'id': 'FR-001', 'description': 'Create and read stored records',
                              'acceptance': 'A created record can be fetched'}]
    value['interfaces'] = [{'id': 'API-001', 'method': 'get', 'path': '/records',
                            'operation': {'responses': {'200': {'description': 'OK'}}},
                            'authentication': 'public'}]
    return value


class ContractResolutionReviewTests(unittest.TestCase):
    def test_anonymous_auth_alternative_cannot_satisfy_required_intent(self):
        for security in ([{}], [{'bearer': []}, {}]):
            with self.subTest(security=security):
                p = project()
                p['security_schemes'] = {'bearer': {'type': 'http', 'scheme': 'bearer'}}
                p['interfaces'][0]['operation']['security'] = security
                p['interfaces'][0]['authentication'] = {'policy': 'required'}
                resolved = resolve_contracts(require_project(p))
                self.assertTrue(any(c['field'] == 'authentication' for c in resolved['conflicts']), resolved)

    def test_untrusted_policy_shape_is_a_diagnostic_not_a_crash(self):
        p = project()
        p['interfaces'][0]['authentication'] = {'policy': []}
        result = resolve_contracts(p)
        self.assertTrue(result['conflicts'])

    def test_native_contract_respects_explicit_public_intent_without_mutating_bytes(self):
        p = project()
        native = {'openapi': '3.0.3', 'info': {'title': 'Records', 'version': '1'},
                  'paths': {'/records': {'get': copy.deepcopy(p['interfaces'][0]['operation'])}}}
        p['api_contract'] = native
        p['interfaces'][0].pop('operation')
        for intent in ('public', {'policy': 'public'}):
            p['interfaces'][0]['authentication'] = intent
            resolved = resolve_contracts(p)
            self.assertEqual(resolved['authentication'][0]['policy'], 'public')
            self.assertEqual(resolved['api'], native)

    def test_equivalent_inline_and_offline_ref_contracts_agree(self):
        p = project()
        op = p['interfaces'][0]['operation']
        op['responses']['200']['content'] = {'application/json': {'schema': {'type': 'string'}}}
        native_op = copy.deepcopy(op)
        native_op['responses']['200']['content']['application/json']['schema'] = {'$ref': '#/components/schemas/Result'}
        p['api_contract'] = {'openapi': '3.0.3', 'info': {'title': 'Records', 'version': '1'},
                             'components': {'schemas': {'Result': {'type': 'string'}}},
                             'paths': {'/records': {'get': native_op}}}
        self.assertFalse(resolve_contracts(p)['conflicts'])

    def test_nonempty_requirements_without_implementation_coverage_are_not_complete(self):
        p = new_project('Working record application')
        p['requirements'] = [{'id': 'FR-001', 'description': 'Create and read stored records',
                              'acceptance': 'A created record can be fetched'}]
        result = readiness(p, 'review-ready')
        self.assertFalse(result['profile_satisfied'], result)
        self.assertTrue(result['blockers'])

    def test_reference_array_indices_use_json_pointer_rules(self):
        document = {'items': [{'type': 'string'}], 'a/b': {'type': 'integer'}}
        for ref in ('#/items/-1', '#/items/00', '#/items/+0', '#/items/-', '#/items/1', '#/a~2b'):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                normalized({'$ref': ref}, document)
        self.assertEqual(normalized({'$ref': '#/items/0'}, document), {'type': 'string'})
        self.assertEqual(normalized({'$ref': '#/a~1b'}, document), {'type': 'integer'})
        self.assertEqual(normalized({'$ref': '#/a%2Fb'}, {'a': {'b': {'type': 'number'}}}), {'type': 'number'})

    def test_default_rich_export_remains_reloadable_and_regenerable(self):
        fixture = json.loads((BASE / 'tests/fixtures/rich-project.json').read_text())
        files, report = compile_plan(fixture)
        exported = require_project(json.loads(files['project.json']))
        regenerated, _ = compile_plan(exported)
        self.assertEqual(json.loads(files['api.json']), json.loads(regenerated['api.json']))
        self.assertEqual(report['identity']['exported_project_hash'], report['identity']['projection_hash'])
        self.assertNotIn('AGENTS.md', files)
        self.assertIn('architecture-constraints.json', files)


if __name__ == '__main__':
    unittest.main()
