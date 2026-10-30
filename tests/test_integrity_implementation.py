"""Audit counterexamples for canonical state and self-contained handoffs."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'tools'))
from artifact_compiler import compile_plan, readiness
from contract_resolution import resolve_contracts
from project_model import new_project, project_checks, supersede
from revision_store import init_project, load_project, commit_project, recover
from safe_io import digest, dumps
from operations_profile import operational_readiness, FIELDS


class IntegrityImplementationTests(unittest.TestCase):
    def fixture(self):
        return json.loads((BASE / 'tests/fixtures/rich-project.json').read_text())

    def test_shareable_export_is_self_contained_and_named_hashes_match(self):
        p = self.fixture()
        files, report = compile_plan(p)
        exported = json.loads(files['project.json'])
        second, _ = compile_plan(exported)
        self.assertEqual(json.loads(files['api.json']), json.loads(second['api.json']))
        self.assertEqual(report['identity']['exported_project_hash'], digest(exported))
        self.assertEqual(report['identity']['exported_project_bytes_sha256'], digest(files['project.json'].encode()))
        self.assertIn('/custom_extension', report['identity']['redaction_report']['omitted_paths'])
        self.assertNotIn('AGENTS.md', files)
        self.assertIn('architecture-constraints.json', files)

    def test_authentication_prose_cannot_disappear_into_green_readiness(self):
        p = new_project('Private API')
        p['requirements'] = [{'id':'FR-001','description':'Protected data','acceptance':'Unauthenticated request denied'}]
        p['interfaces'] = [{'id':'API-001','method':'GET','path':'/private','authentication':'BearerAuth required',
                            'operation':{'responses':{'200':{'description':'OK'}}}}]
        self.assertFalse(readiness(p,'review-ready')['profile_satisfied'])
        with self.assertRaisesRegex(ValueError,'authentication'):
            compile_plan(p)

    def test_native_and_embedded_contract_disagreement_is_rejected(self):
        p=self.fixture()
        p['interfaces'][0]['operation']['responses']['200']['description']='Documentation may differ'
        self.assertFalse(resolve_contracts(p)['conflicts'])
        p['interfaces'][0]['operation']['responses']['200']['content']['application/json']['schema']={'type':'integer'}
        with self.assertRaisesRegex(ValueError,'contract conflicts'):
            compile_plan(p)

    def test_empty_project_valid_draft_but_not_review_ready(self):
        p=new_project('Empty')
        self.assertEqual(project_checks(p),[])
        self.assertFalse(readiness(p,'review-ready')['profile_satisfied'])

    def test_operational_profile_reports_unknowns_without_execution_claims(self):
        p=new_project('Operations')
        self.assertEqual(operational_readiness(p)['status'],'not_applicable')
        p['operations']={'owner':'Team A'}
        report=operational_readiness(p)
        self.assertEqual(report['status'],'partial')
        self.assertIn('rollback',report['unknown'])
        p['operations']={name:'declared intent' for name in FIELDS}
        report=operational_readiness(p)
        self.assertEqual(report['status'],'specified')
        self.assertEqual(report['runtime_verification'],'not_run')
        files,_=compile_plan(p)
        self.assertEqual(json.loads(files['operations.json'])['restore_drill'],'not_run')

    def test_invalid_native_paths_return_conflicts_not_attribute_errors(self):
        p=new_project('Malformed')
        p['api_contract']={'paths':[]}
        self.assertTrue(resolve_contracts(p)['conflicts'])

    def test_known_reference_shape_is_checked_in_every_group(self):
        p=new_project('Typed')
        p['requirements']=[{'id':'FR-001','description':'Work','tasks':[{}]}]
        self.assertTrue(project_checks(p))

    def test_supersession_chain_has_no_copied_approval_or_repeated_successor(self):
        p=new_project('History')
        p['decisions']=[{'id':'ADR-001','status':'Accepted','decision':'Use SQLite','approval_origin':'owner'}]
        q=supersede(p,'ADR-001','ADR-002','new workload')
        self.assertNotIn('approval_origin',q['decisions'][1])
        self.assertEqual(q['decisions'][1]['predecessor_approval_origin'],'owner')
        with self.assertRaisesRegex(ValueError,'already superseded'):
            supersede(q,'ADR-001','ADR-003','duplicate')
        q['decisions'][1]['supersedes']='ADR-999'
        self.assertTrue(project_checks(q))

    def test_cross_project_commit_preserves_original(self):
        with tempfile.TemporaryDirectory() as t:
            init_project(t,'A');old=load_project(t)
            with self.assertRaisesRegex(ValueError,'identity mismatch'):
                commit_project(t,new_project('B'),'replace',digest(old))
            self.assertEqual(load_project(t),old)

    def test_advertised_project_limit_composes_into_recovery_journal(self):
        with tempfile.TemporaryDirectory() as t:
            init_project(t,'Large');old=load_project(t);p=copy.deepcopy(old)
            p['brief']='x'*(5*1024*1024-len(dumps(p).encode())-64)
            self.assertFalse(project_checks(p))
            commit_project(t,p,'at limit',digest(old))
            self.assertEqual(load_project(t)['brief'],p['brief'])
            self.assertEqual(recover(t)['status'],'committed')


if __name__=='__main__':unittest.main()
