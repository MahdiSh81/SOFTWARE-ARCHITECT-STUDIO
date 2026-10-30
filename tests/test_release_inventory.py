import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('source_inventory', ROOT / 'tools/check_source_manifest.py')
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def test_detects_changed_missing_and_unlisted_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'tools').mkdir()
            (root / 'release').mkdir()
            (root / 'release/version.json').write_text('{"version":"0.9.0"}')
            source = root / 'tools/sample.py'
            source.write_text('original')
            before = inventory.inventory(root)
            source.write_text('changed')
            (root / 'tools/new.py').write_text('new')
            diff = inventory.compare(before, inventory.inventory(root))
            self.assertEqual(diff['changed'], ['tools/sample.py'])
            self.assertEqual(diff['unlisted'], ['tools/new.py'])
            source.unlink()
            self.assertEqual(inventory.compare(before, inventory.inventory(root))['missing'], ['tools/sample.py'])

    def test_history_and_generated_dependencies_are_not_current_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'release').mkdir()
            (root / 'release/version.json').write_text('{}')
            for name in ('audits/old/source.py', 'tools/__pycache__/sample.pyc',
                         'tests/browser/node_modules/example.js', 'release/verification.json'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('historical or generated')
            self.assertEqual(list(inventory.inventory(root)), ['release/version.json'])

    def test_readme_version_drift_fails_current_identity_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            names = ('release/version.json', 'plugin.json', '.codex-plugin/plugin.json',
                     'capabilities.json', 'tests/browser/package.json',
                     'tests/browser/package-lock.json', 'tools/project_model.py',
                     'README.md', 'skills/software-architecture/SKILL.md',
                     'workbench/index.html')
            for name in names:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, p)
            (root / 'README.md').write_text('# Software Architect Studio 0.0.0\n')
            self.assertTrue(any('README.md' in issue for issue in inventory.version_issues(root)))
