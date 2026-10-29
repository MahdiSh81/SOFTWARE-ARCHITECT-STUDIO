import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from architect_cli import capacity, score, validate, validate_mermaid


class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.sample = dict(daily_requests=86400, peak_factor=8, average_payload_kb=2,
                           records_per_day=1000, average_record_bytes=1000,
                           retention_days=100, storage_overhead_multiplier=2,
                           replica_count=2, monthly_compute_hours=730)

    def test_capacity_formulas(self):
        result = capacity(self.sample)
        self.assertEqual(result['average_qps'], 1)
        self.assertEqual(result['peak_qps'], 8)
        self.assertEqual(result['logical_retained_gb'], .1)
        self.assertEqual(result['physical_storage_gb'], .4)
        self.assertIsNone(result['monthly_cost'])

    def test_zero_prices_are_valid(self):
        for k in ('compute', 'storage', 'egress'):
            pass
        self.sample.update(assumed_compute_price_per_hour=0, assumed_storage_price_per_gb_month=0, assumed_egress_price_per_gb=0)
        self.assertEqual(capacity(self.sample)['monthly_cost'], 0)

    def test_nan_rejected(self):
        self.sample['peak_factor'] = float('nan')
        with self.assertRaises(ValueError): capacity(self.sample)

    def test_negative_rejected(self):
        self.sample['records_per_day'] = -1
        with self.assertRaises(ValueError): capacity(self.sample)

    def test_fractional_replica_rejected(self):
        self.sample['replica_count'] = 1.5
        with self.assertRaises(ValueError): capacity(self.sample)

class ScoringTests(unittest.TestCase):
    def test_empty_is_not_evaluated(self):
        result = score({'scores': {}})
        self.assertIsNone(result['score_percent'])
        self.assertEqual(result['evaluated_weight_percent'], 0)

    def test_partial_coverage_not_zeroed(self):
        result = score({'scores': {'security': 4, 'reliability': 2}})
        self.assertAlmostEqual(result['score_percent'], (25 + 20 * .5) / 45 * 100, places=2)
        self.assertEqual(result['evaluated_weight_percent'], 45)
        self.assertIn('provisional', result['status'])

    def test_bad_score_rejected(self):
        with self.assertRaises(ValueError): score({'scores': {'security': 5}})

    def test_bad_weights_rejected(self):
        with self.assertRaises(ValueError): score({'scores': {}, 'weights': {'security': 100}})

class ValidationTests(unittest.TestCase):
    def test_valid_mermaid(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / 'flow.mmd'
            f.write_text('flowchart LR\n  a[Client] --> b[API]\n')
            self.assertEqual(validate_mermaid(f), [])
            r = validate(Path(t))
            self.assertTrue(r['ok'])
            self.assertTrue(r['skipped'])

    def test_dangling_arrow(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / 'bad.mmd'
            f.write_text('flowchart LR\n  a -->\n')
            self.assertTrue(any('dangling' in i for i in validate_mermaid(f)))
            self.assertFalse(validate(Path(t))['ok'])

    def test_json_error(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'data.json').write_text('{no')
            self.assertFalse(validate(Path(t))['ok'])

    def test_api_basic(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'api.yaml').write_text('openapi: 3.0.3\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}\n')
            self.assertTrue(validate(Path(t))['ok'])

if __name__ == '__main__':
    unittest.main()
