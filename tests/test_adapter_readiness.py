"""Fresh post-0.9 release review: malformed plans must fail before effects."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import execution_adapter as adapter
from safe_io import digest


class AdapterReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'source'
        self.root.mkdir()
        (self.root / 'a.txt').write_text('original a')
        (self.root / 'b.txt').write_text('original b')
        self.state = Path(self.tmp.name) / 'operations'
        self.policy = {'schema_version': 1, 'root': str(self.root), 'authorization_reference': 'review-fixture',
                       'allow_write': True, 'allowed_paths': ['a.txt', 'b.txt']}

    def plan(self):
        return adapter.propose_change(self.root, [{'path': 'a.txt', 'content': 'new a'},
                                                  {'path': 'b.txt', 'content': 'new b'}])

    def rehash(self, plan):
        plan['plan_hash'] = digest({k: plan[k] for k in ('schema_version', 'root', 'input_source_hash', 'changes')})
        return plan

    def assert_original(self):
        self.assertEqual((self.root / 'a.txt').read_text(), 'original a')
        self.assertEqual((self.root / 'b.txt').read_text(), 'original b')

    def test_standard_library_request_validation_checks_shapes_and_bounds(self):
        bad = [
            ('propose_change', {'changes': []}),
            ('propose_change', {'changes': [{'path': 'a.txt'}]}),
            ('run_checks', {'names': ['one', 'one'], 'expected_source_hash': 'a' * 64}),
            ('run_checks', {'names': ['one'], 'expected_source_hash': None}),
            ('recover', {'operation_id': '../other'}),
            ('apply_change', {'plan': []}),
        ]
        with patch.dict(sys.modules, {'jsonschema': None}):
            for op, request in bad:
                with self.subTest(operation=op, request=request):
                    with self.assertRaises(ValueError):
                        adapter.validate_request(op, request)

    def test_valid_multi_file_apply_also_works_without_jsonschema(self):
        with patch.dict(sys.modules, {'jsonschema': None}):
            plan = self.plan()
            adapter.validate_request('apply_change', {'plan': plan, 'operation_id': 'stdlib-valid'})
            result = adapter.apply_change(self.root, plan, self.policy,
                                          operation_id='stdlib-valid', state_root=self.state)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['observed_effects'], ['a.txt', 'b.txt'])
        self.assertEqual((self.root / 'a.txt').read_text(), 'new a')
        self.assertEqual((self.root / 'b.txt').read_text(), 'new b')

    def test_proposal_requires_explicit_content_before_it_can_mean_delete(self):
        with self.assertRaises(ValueError):
            adapter.propose_change(self.root, [{'path': 'a.txt'}])
        self.assert_original()

    def test_unknown_plan_version_rejected_even_with_matching_plan_hash(self):
        plan = self.plan()
        plan['schema_version'] = 99
        with self.assertRaises(ValueError):
            adapter.apply_change(self.root, self.rehash(plan), self.policy, state_root=self.state)
        self.assert_original()
        self.assertFalse(self.state.exists())

    def test_empty_plan_rejected_before_any_operation_record(self):
        plan = self.plan()
        plan['changes'] = []
        with self.assertRaises(ValueError):
            adapter.apply_change(self.root, self.rehash(plan), self.policy, state_root=self.state)
        self.assert_original()
        self.assertFalse(self.state.exists())

    def test_duplicate_plan_paths_rejected_before_writing(self):
        plan = self.plan()
        plan['changes'].append(copy.deepcopy(plan['changes'][0]))
        with self.assertRaises(ValueError):
            adapter.apply_change(self.root, self.rehash(plan), self.policy, state_root=self.state)
        self.assert_original()

    def test_all_file_preconditions_are_checked_before_first_mutation(self):
        plan = self.plan()
        plan['changes'][1]['before_hash'] = 'b' * 64
        with self.assertRaises(ValueError):
            adapter.apply_change(self.root, self.rehash(plan), self.policy, state_root=self.state)
        self.assert_original()

    def test_unreadable_subtree_cannot_produce_a_complete_source_identity(self):
        child = self.root / 'blocked'
        child.mkdir()
        (child / 'hidden.txt').write_text('must not disappear')
        real_scandir = adapter.os.scandir
        def fail_subtree(path):
            if Path(path) == child:
                raise PermissionError('synthetic enumeration denial')
            return real_scandir(path)
        with patch.object(adapter.os, 'scandir', side_effect=fail_subtree):
            with self.assertRaises(OSError):
                adapter.inspect(self.root)

    def test_policy_version_and_expiry_have_core_type_checks(self):
        plan = self.plan()
        for patch_value in ({'schema_version': True}, {'expires_at': 17}):
            with self.subTest(patch_value=patch_value):
                with self.assertRaises(ValueError):
                    adapter.apply_change(self.root, plan, {**self.policy, **patch_value}, state_root=self.state)
        self.assert_original()


if __name__ == '__main__':
    unittest.main()
