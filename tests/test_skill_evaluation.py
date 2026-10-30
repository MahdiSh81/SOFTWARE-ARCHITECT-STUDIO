import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'tools'))
from skill_registry import discover_skills, loaded_bundle, inventory_bundle, route_task
from evaluation_records import enrich_capture, capture_identity, validate_review, summarize_captures, summarize_observations


def capture():
    return enrich_capture({'capture_schema': 1, 'id': 'capture-1', 'prompt': 'actual supplied prompt',
        'response': 'actual supplied response', 'reported_model': 'unknown', 'reviews': [],
        'quality_status': 'unreviewed'}, skills=['software-architecture'])


def review(c, reviewer='assessor-1'):
    return {'reviewer_id': reviewer, 'capture_id': c['id'], 'source_hash': capture_identity(c),
        'reviewed_at': '2026-10-30T10:00:00+03:30', 'rubric_version': 1,
        'scores': {k: 3 for k in ('correctness', 'evidence', 'risk_handling', 'constraint_adherence', 'usefulness')},
        'critical_failures': [], 'evidence_refs': ['fixture:acceptance-1'], 'calibrated': True,
        'calibration_reference': 'calibration:fixture-1', 'conclusion': 'Within the reviewed task scope.'}


class SkillRegistryTests(unittest.TestCase):
    def test_complete_packaged_library(self):
        registry = discover_skills()
        self.assertEqual(len(registry['skills']), 11)
        self.assertEqual(len({s['id'] for s in registry['skills']}), 11)
        expected = json.loads((BASE/'release/version.json').read_text())['version']
        self.assertTrue(all(s['version'] == expected for s in registry['skills']))

    def test_eighty_routing_contract_cases(self):
        cases = json.loads((BASE/'evals/routing-cases.json').read_text())['cases']
        self.assertEqual(len(cases), 80)
        for case in cases:
            with self.subTest(case=case):
                out = route_task(case['task'], override=case.get('override'))
                if 'expected_primary' in case:
                    self.assertIn(out['primary'], case['expected_primary'])
                if 'expected_ambiguous' in case:
                    self.assertEqual(out['ambiguous'], case['expected_ambiguous'])
                self.assertIn('suggestion only', out['execution'])

    def test_explicit_loaded_context_and_inventory_distinct(self):
        c = capture()
        self.assertEqual(len(c['declared_loaded_bundle']['entries']), 1)
        self.assertGreater(len(c['available_skill_bundle']['entries']), 11)
        self.assertEqual(c['review_source_hash'], capture_identity(c))

    def test_reference_and_specialist_change_affect_identity(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            p = root/'skills/software-architecture'; p.mkdir(parents=True)
            (p/'SKILL.md').write_text('---\nname: software-architecture\nversion: 0.9.0\n---\n# Core\n')
            refs=p/'references';refs.mkdir();(refs/'facts.md').write_text('Version A')
            a=inventory_bundle(root)
            (refs/'facts.md').write_text('Version B')
            b=inventory_bundle(root)
            self.assertNotEqual(a['bundle_hash'], b['bundle_hash'])
            self.assertEqual(loaded_bundle(root)['entries'][0]['path'], 'skills/software-architecture/SKILL.md')

    def test_bundle_traversal_and_unknown_skills_refused(self):
        for args in ({'skills':['missing']}, {'references':['../README.md']}, {'references':['/tmp/x.md']}):
            with self.subTest(args=args), self.assertRaises(ValueError):loaded_bundle(**args)
        with self.assertRaises(ValueError):route_task('anything',override='missing')


class SemanticReviewTests(unittest.TestCase):
    def test_malformed_marker_not_counted_as_review(self):
        c = capture(); c['reviews']=['unvalidated marker']
        with self.assertRaises(ValueError):summarize_captures([c])

    def test_two_attributed_calibrated_reviews_with_matching_source(self):
        c = capture();c['reviews']=[review(c),review(c,'assessor-2')]
        out = summarize_captures([c])
        self.assertEqual(out['reviewed'],1)
        self.assertTrue(out['semantic_gate_passed'])
        self.assertIn('not authenticated',out['scope'])

    def test_critical_semantic_failure_cannot_be_hidden_by_high_scores(self):
        c=capture();a=review(c);a['critical_failures']=['cross-tenant disclosure'];c['reviews']=[a,review(c,'assessor-2')]
        out=summarize_captures([c])
        self.assertFalse(out['semantic_gate_passed']);self.assertEqual(out['assessments'][0]['status'],'failed')

    def test_source_mismatch_and_response_edit_invalidate_review(self):
        c=capture();c['reviews']=[review(c)];c['response']='a different response'
        with self.assertRaises(ValueError):summarize_captures([c])

    def test_disagreement_retained_and_needs_adjudication(self):
        c=capture();a=review(c);b=review(c,'assessor-2');b['scores']['correctness']=4;c['reviews']=[a,b]
        out=summarize_captures([c]);self.assertEqual(out['assessments'][0]['status'],'adjudication_needed')
        self.assertEqual(out['disagreements'][0]['dimensions'],['correctness']);self.assertFalse(out['semantic_gate_passed'])

    def test_duplicate_reviewer_and_capture_rejected(self):
        c=capture();c['reviews']=[review(c),review(c)]
        with self.assertRaises(ValueError):summarize_captures([c])
        c['reviews']=[]
        with self.assertRaises(ValueError):summarize_captures([c,c])

    def test_false_calibration_and_missing_dimensions_rejected(self):
        c=capture();a=review(c);del a['calibration_reference']
        self.assertTrue(validate_review(a,c));a=review(c);del a['scores']['risk_handling']
        self.assertTrue(validate_review(a,c))

    def test_unreviewed_and_zero_capture_not_green(self):
        self.assertFalse(summarize_captures([])['semantic_gate_passed'])
        self.assertFalse(summarize_captures([capture()])['semantic_gate_passed'])

    def test_observations_require_consent_and_do_not_invent_unknown_metrics(self):
        record={'id':'obs-1','participant_alias':'person-A','task':'resume','consented':True,'completed':None,'time_seconds':None,'corrections':None}
        result=summarize_observations([record])
        self.assertEqual(result['tasks']['resume']['completion_unknown'],1)
        self.assertEqual(result['tasks']['resume']['measured_time_seconds'],[])
        self.assertNotIn('person-A',json.dumps(result))
        with self.assertRaises(ValueError):summarize_observations([{**record,'consented':False}])
        with self.assertRaises(ValueError):summarize_observations([record,record])
        with self.assertRaises(ValueError):summarize_observations([{**record,'time_seconds':float('nan')}])

    def test_schema_validates_actual_bundle_capture_and_review(self):
        try:from jsonschema import Draft202012Validator,FormatChecker
        except ImportError:self.skipTest('optional jsonschema unavailable')
        c=capture();a=review(c)
        for name,value in [('skill-registry-v1',discover_skills()),('skill-bundle-v1',c['declared_loaded_bundle']),('capture-lineage-v1',c),('semantic-review-v1',a),('skill-routing-v1',route_task('debug a failing test'))]:
            schema=json.loads((BASE/f'schemas/{name}.schema.json').read_text())
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema,format_checker=FormatChecker()).validate(value)


if __name__=='__main__':unittest.main()
