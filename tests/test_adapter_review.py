"""Independent negative controls for local adapter evidence and partial effects."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import execution_adapter as adapter


class AdapterReviewTests(unittest.TestCase):
    def test_all_skipped_unittest_does_not_meet_executed_minimum(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'repo'; root.mkdir(); (root / 'source.txt').write_text('unchanged')
            program = 'import unittest\n@unittest.skip("fixture")\nclass T(unittest.TestCase):\n def test_skip(self):pass\nunittest.main()\n'
            policy = {'schema_version': 1, 'root': str(root), 'authorization_reference': 'synthetic-review', 'allow_checks': True, 'checks': {'suite': {'argv': [sys.executable, '-c', program], 'kind': 'test', 'minimum_tests': 1}}}
            receipt = adapter.run_checks(root, ['suite'], policy, expected_source_hash=adapter.inspect(root)['source_hash'], state_root=Path(t) / 'state')
            self.assertEqual(receipt['status'], 'failed')
            self.assertEqual(receipt['details']['checks'][0]['tests_executed'], 0)

    def test_journal_failure_after_write_preserves_observed_effect_result(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'repo'; root.mkdir(); (root / 'a.txt').write_text('before')
            state = Path(t) / 'state'
            plan = adapter.propose_change(root, [{'path': 'a.txt', 'content': 'after'}])
            policy = {'schema_version': 1, 'root': str(root), 'authorization_reference': 'synthetic-review', 'allow_write': True, 'allowed_paths': ['a.txt'], 'approved_plan_hash': plan['plan_hash']}
            original = adapter.atomic_write
            state_writes = []
            def disk_failure(path, data, *args, **kwargs):
                if Path(path).parent == state and Path(path).name == 'review-op.json':
                    state_writes.append(path)
                    if len(state_writes) > 1:
                        raise OSError('synthetic operation-store full')
                return original(path, data, *args, **kwargs)
            with patch.object(adapter, 'atomic_write', side_effect=disk_failure):
                receipt = adapter.apply_change(root, plan, policy, operation_id='review-op', state_root=state)
            self.assertEqual((root / 'a.txt').read_text(), 'after')
            self.assertIn('a.txt', receipt['observed_effects'])
            self.assertIn(receipt['status'], {'partial', 'passed'})
            self.assertEqual(receipt.get('receipt_status'), 'failed')
            self.assertEqual(adapter.recover(root, 'review-op', state_root=state)['status'], 'committed')


if __name__ == '__main__':
    unittest.main()
