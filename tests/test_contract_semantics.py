"""Contract comparison must preserve user fields, literal values and ref semantics."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from project_model import new_project
from contract_resolution import resolve_contracts
from validation_engine import contract_correspondence, openapi_checks, _external_refs, validate


def fixture(authored, native, version='3.0.3'):
    p = new_project('Contract semantics')
    def operation(schema):
        return {'security': [], 'responses': {'200': {'description': 'OK',
                'content': {'application/json': {'schema': copy.deepcopy(schema)}}}}}
    p['interfaces'] = [{'id':'API-001', 'method':'GET', 'path':'/records',
                        'authentication':'public', 'operation':operation(authored)}]
    p['api_contract'] = {'openapi':version, 'info':{'title':'Records', 'version':'1'},
                         'paths':{'/records':{'get':operation(native)}},
                         'components':{'schemas':{'Result':{'type':'string'}}}}
    return p


class ContractSemanticsTests(unittest.TestCase):
    def test_property_names_that_resemble_documentation_are_preserved(self):
        for name in ('description', 'summary', 'example', 'examples', 'x-customer'):
            with self.subTest(name=name):
                p=fixture({'type':'object','properties':{name:{'type':'string'}}},
                          {'type':'object','properties':{name:{'type':'integer'}}})
                self.assertTrue(resolve_contracts(p)['conflicts'])

    def test_literal_enum_and_default_values_are_not_documentation(self):
        for keyword in ('enum','const','default'):
            a={'description':'first'};b={'description':'second'}
            if keyword=='enum':a,b=[a],[b]
            with self.subTest(keyword=keyword):
                p=fixture({keyword:a},{keyword:b},'3.1.1')
                self.assertTrue(resolve_contracts(p)['conflicts'])

    def test_openapi30_reference_sibling_cannot_override_target(self):
        p=fixture({'type':'integer'},
                  {'$ref':'#/components/schemas/Result','type':'integer'})
        self.assertTrue(resolve_contracts(p)['conflicts'])

    def test_openapi30_ignored_reference_sibling_does_not_create_conflict(self):
        p=fixture({'type':'string'},
                  {'$ref':'#/components/schemas/Result','type':'integer'})
        self.assertFalse(resolve_contracts(p)['conflicts'])

    def test_openapi31_schema_ref_siblings_are_conjunctive_not_overrides(self):
        p=fixture({'type':'integer'},
                  {'$ref':'#/components/schemas/Result','type':'integer'},'3.1.1')
        self.assertTrue(resolve_contracts(p)['conflicts'])

    def test_cross_artifact_comparison_keeps_named_fields(self):
        schema={'type':'object','properties':{'description':{'type':'string'}}}
        p=fixture(schema,schema)
        api=copy.deepcopy(p['api_contract'])
        api['paths']['/records']['get']['responses']['200']['content']['application/json']['schema']['properties']['description']['type']='integer'
        self.assertTrue(contract_correspondence(p,api))

    def test_real_documentation_differences_remain_ignored(self):
        p=fixture({'type':'string','description':'authored documentation'},
                  {'type':'string','description':'native documentation'})
        self.assertFalse(resolve_contracts(p)['conflicts'])

    def test_literal_ref_and_opaque_schema_keywords_are_not_reinterpreted(self):
        for keyword in ('const', 'dependentRequired', 'x-validation'):
            a={'$ref':'literal user value','description':['first']}
            b={'$ref':'literal user value','description':['second']}
            with self.subTest(keyword=keyword):
                self.assertTrue(resolve_contracts(fixture({keyword:a},{keyword:b},'3.1.1'))['conflicts'])

    def test_ref_is_a_legal_property_name_not_a_reference_at_map_level(self):
        schema={'type':'object','properties':{'$ref':{'type':'string'}}}
        self.assertFalse(resolve_contracts(fixture(schema,schema))['conflicts'])

    def test_openapi31_response_reference_does_not_inherit_schema_sibling_rules(self):
        p=fixture({'type':'string'},{'type':'string'},'3.1.1')
        response=p['api_contract']['paths']['/records']['get']['responses']['200']
        p['api_contract']['components']['responses']={'Result':copy.deepcopy(response)}
        p['api_contract']['paths']['/records']['get']['responses']['200']={
            '$ref':'#/components/responses/Result',
            'content':{'application/json':{'schema':{'type':'integer'}}}}
        self.assertFalse(resolve_contracts(p)['conflicts'])

    def test_reference_policy_does_not_treat_instance_data_as_references(self):
        for name in ('const', 'enum', 'default'):
            literal={'$ref':'https://example.invalid/literal-data'}
            schema={name:[literal] if name=='enum' else literal}
            p=fixture(schema,schema,'3.1.1')
            with self.subTest(keyword=name):
                self.assertFalse(_external_refs(p['api_contract']))
                self.assertEqual(openapi_checks(p['api_contract']),[])

    def test_property_named_ref_is_not_an_invalid_reference(self):
        schema={'properties':{'$ref':{'type':'string'}}}
        api=fixture(schema,schema)['api_contract']
        self.assertEqual(openapi_checks(api),[])

    def test_real_schema_reference_is_still_blocked(self):
        schema={'properties':{'payload':{'$ref':'https://example.invalid/real-reference'}}}
        self.assertTrue(_external_refs(fixture(schema,schema)['api_contract']))

    def test_example_value_refs_are_data_but_component_example_refs_are_real(self):
        p=fixture({'type':'string'},{'type':'string'})
        p['api_contract']['components']['examples']={'Sample':{'value':{'$ref':'literal value'}}}
        self.assertFalse(_external_refs(p['api_contract']))
        p['api_contract']['components']['examples']['Other']={'$ref':'https://example.invalid/actual-example-ref'}
        self.assertTrue(_external_refs(p['api_contract']))

    @unittest.skipUnless(importlib.util.find_spec('openapi_spec_validator'), 'optional full validator unavailable')
    def test_installed_full_gate_accepts_literal_ref_values_without_fetching(self):
        literal={'$ref':'https://example.invalid/literal-data'}
        schema={'enum':[literal], 'default':literal}
        api=fixture(schema,schema,'3.1.1')['api_contract']
        api['components']['examples']={'Sample':{'value':literal}}
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'api.json';p.write_text(json.dumps(api))
            result=validate(p,full_openapi=True,gate='full')
        self.assertTrue(result['policy_ok'],result)
        self.assertTrue(any(c['check']=='OpenAPI full schema' and c['status']=='passed' for c in result['checks']))


if __name__=='__main__':unittest.main()
