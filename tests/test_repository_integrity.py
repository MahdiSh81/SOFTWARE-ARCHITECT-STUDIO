"""Regression invariants from audit I06; fixtures never execute repository code."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from project_model import new_project
from repository_evidence import repo_scan, fitness, evidence_delta
from graph_engine import impacts, change_bundle


class RepositoryIntegrityTests(unittest.TestCase):
    def rule(self, prefix='', target='forbidden'):
        p = new_project('Import rule')
        p['fitness_rules'] = [{'id': 'RULE-001', 'kind': 'forbid_import', 'source_prefix': prefix, 'target_prefix': target}]
        return p

    def test_failed_and_unsupported_extraction_cannot_pass(self):
        for name, text in [('a.py', 'this is bad Python !!!'), ('a.go', 'package main\nimport "forbidden"')]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as t:
                root = Path(t); (root / name).write_text(text)
                scan = repo_scan(root)
                self.assertEqual(fitness(self.rule(), scan)['rules'][0]['status'], 'unknown')
                self.assertTrue(scan['omissions'])

    def test_fresh_supported_clean_scope_passes(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root / 'a.py').write_text('import allowed\n')
            self.assertEqual(fitness(self.rule(), repo_scan(root))['rules'][0]['status'], 'satisfied-in-scope')

    def test_parser_failure_diagnostics_survive_cache(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'repo'; root.mkdir(); (root / 'a.py').write_text('bad syntax !')
            cache = Path(t) / 'cache.json'
            cold, warm = repo_scan(root, cache=cache), repo_scan(root, cache=cache)
            self.assertEqual(warm['cache_hits'], 1)
            self.assertEqual(cold['coverage'], warm['coverage'])
            self.assertEqual(cold['omissions'], warm['omissions'])
            self.assertEqual(cold['observed_files'][0]['extraction'], warm['observed_files'][0]['extraction'])

    def test_cache_tampering_cannot_prove_clean(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'repo'; root.mkdir(); (root / 'a.py').write_text('import forbidden\n')
            cache = Path(t) / 'cache.json'; repo_scan(root, cache=cache)
            data = json.loads(cache.read_text()); entry = next(iter(data['entries'].values())); entry['items'] = []; entry['edges'] = []
            cache.write_text(json.dumps(data))
            self.assertEqual(fitness(self.rule(), repo_scan(root, cache=cache))['rules'][0]['status'], 'unknown')
            self.assertEqual(fitness(self.rule(), repo_scan(root))['rules'][0]['status'], 'violation')

    def test_edge_quota_independent_of_declarations(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root / 'ci.json').write_text(json.dumps({'jobs': {'one': {'needs': [str(i) for i in range(101)]}}}))
            scan = repo_scan(root)
            self.assertEqual(len(scan['dependency_edges']), 100)
            self.assertTrue(any(x['reason'] == 'edge quota' and x['count'] == 1 for x in scan['omissions']))
            self.assertEqual(scan['coverage'], 'partial')

    def test_descriptor_failure_is_typed(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root / 'package.json').write_text('{broken')
            scan = repo_scan(root)
            self.assertEqual(scan['observed_files'][0]['extraction'], 'parse_failed')
            self.assertEqual(scan['coverage'], 'partial')

    def test_python_manifests_extract_packages_but_not_imports(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / 'pyproject.toml').write_text('[project]\ndependencies=["forbidden>=1"]\n')
            (root / 'requirements.txt').write_text('other==1\n')
            scan = repo_scan(root)
            self.assertEqual({e['target'] for e in scan['dependency_edges']}, {'forbidden', 'other'})
            self.assertEqual(fitness(self.rule(), scan)['rules'][0]['status'], 'unknown')

    def test_relative_import_preserves_syntax_and_symbol(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root / 'a.py').write_text('from . import forbidden\nfrom ..domain import x\n')
            scan = repo_scan(root)
            self.assertEqual([e['target'] for e in scan['dependency_edges']], ['.forbidden', '..domain'])
            self.assertEqual([e['relative_level'] for e in scan['dependency_edges']], [1, 2])
            self.assertEqual(scan['dependency_edges'][0]['imported_names'], ['forbidden'])
            self.assertEqual(fitness(self.rule(), scan)['rules'][0]['status'], 'violation')

    def test_js_does_not_cross_statement_boundary(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root / 'a.ts').write_text('export const marker = 1\nimport x from "forbidden";\n')
            scan = repo_scan(root)
            self.assertEqual([(e['line'], e['target']) for e in scan['dependency_edges']], [(2, 'forbidden')])

    def test_cache_write_failure_retains_scan_and_quota(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'repo'; root.mkdir(); (root / 'a.py').write_text('import a\n' * 2000)
            with patch('safe_io.atomic_write', side_effect=OSError('disk full')):
                scan = repo_scan(root, cache=Path(t) / 'cache.json')
            self.assertEqual(scan['scanned_count'], 1)
            self.assertEqual(len(scan['static_declarations']), 100)
            self.assertIn('cache write failed', scan['cache_status'])
            self.assertTrue(any(x['reason'] == 'declaration quota' and x['count'] == 1900 for x in scan['omissions']))
            self.assertIn('cooperative', scan['deadline_enforcement'])

    def test_delta_rejects_invalid_and_incomparable_envelopes(self):
        with self.assertRaisesRegex(ValueError, 'envelope'):
            evidence_delta({}, {})
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            (Path(a) / 'a.py').write_text('import a\n'); (Path(b) / 'a.py').write_text('import b\n')
            first, second = repo_scan(a), repo_scan(b)
            self.assertEqual(evidence_delta(first, second)['status'], 'unknown')
            self.assertEqual(evidence_delta(first, second, allow_cross_tree=True)['changed'], ['a.py'])
            second['observed_files'].append(second['observed_files'][0])
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                evidence_delta(first, second, allow_cross_tree=True)

    def test_interface_change_reaches_tasks_and_verifications(self):
        p = new_project('Typed impact')
        p['requirements'] = [{'id': 'FR-001', 'description': 'Read data'}]
        p['interfaces'] = [{'id': 'API-001', 'method': 'GET', 'path': '/old', 'requirements': ['FR-001']}]
        p['tasks'] = [{'id': 'TASK-001', 'interfaces': ['API-001']}]
        p['verifications'] = [{'id': 'VER-001', 'requirements': ['FR-001']}]
        q = copy.deepcopy(p); q['interfaces'][0]['path'] = '/new'
        result = change_bundle(p, q)
        self.assertEqual(result['changed_requirements'], [])
        self.assertEqual(result['proposed_impact']['affected']['tasks'][0]['id'], 'TASK-001')
        self.assertEqual(impacts(p, ['FR-001'])['affected']['verifications'][0]['id'], 'VER-001')
        self.assertEqual(change_bundle(p, p)['proposed_impact']['seeds'], [])

    def test_parser_timeout_and_missing_parser_are_distinct(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root / 'compose.yaml').write_text('services: {}')
            with patch('validation_engine.parse_yaml', side_effect=ValueError('bounded YAML parse timed_out')):
                self.assertEqual(repo_scan(root)['observed_files'][0]['extraction'], 'timed_out')
            with patch('validation_engine.parse_yaml', side_effect=ImportError('not installed')):
                self.assertEqual(repo_scan(root)['observed_files'][0]['extraction'], 'blocked')

    def test_malformed_cache_entry_is_recomputed(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'repo'; root.mkdir(); (root / 'a.py').write_text('import forbidden')
            cache = Path(t) / 'cache.json'; repo_scan(root, cache=cache)
            data = json.loads(cache.read_text()); next(iter(data['entries'].values()))['status'] = []
            cache.write_text(json.dumps(data))
            scan = repo_scan(root, cache=cache)
            self.assertEqual(scan['cache_hits'], 0)
            self.assertEqual(fitness(self.rule(), scan)['rules'][0]['status'], 'violation')

    def test_evidence_matches_published_schema(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest('optional jsonschema not installed')
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root / 'a.py').write_text('import os')
            schema = json.loads((Path(__file__).resolve().parents[1] / 'schemas/evidence-v1.schema.json').read_text())
            Draft202012Validator(schema).validate(repo_scan(root))

    def test_changed_relationship_seeds_endpoints(self):
        p = new_project('Graph')
        p['components'] = [{'id': 'CMP-001'}, {'id': 'CMP-002'}]
        q = copy.deepcopy(p)
        q['relationships'] = [{'id': 'EDGE-001', 'kind': 'calls', 'from': {'group': 'components', 'id': 'CMP-001'}, 'to': {'group': 'components', 'id': 'CMP-002'}}]
        result = change_bundle(p, q)
        self.assertEqual(len(result['proposed_impact']['seeds']), 2)
        self.assertEqual(result['baseline_impact']['seeds'], [])


if __name__ == '__main__':
    unittest.main()
