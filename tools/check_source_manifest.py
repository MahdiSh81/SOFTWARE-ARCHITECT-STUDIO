"""Check the explicitly scoped live plugin inventory and current release identity.

Audit snapshots and release reports/receipts are not live source members;
release/version.json remains part of the current package identity. A manifest is an integrity inventory, not a signature.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

LIVE_DIRS = ('.codex-plugin', '.github', 'docs', 'evals', 'examples', 'research',
             'schemas', 'skills', 'strategy', 'tests', 'tools', 'workbench')
EXCLUDED = {'__pycache__', 'node_modules', '.venv', 'test-results', 'playwright-report'}
ROOT_FILES = ('.app.json', '.gitignore', 'README.md', 'CHANGELOG.md',
              'IMPLEMENTATION_STATUS.json', 'capabilities.json', 'plugin.json',
              'requirements-validation.txt', 'requirements-validation.lock')


def inventory(root):
    root = Path(root)
    files = {root / name for name in ROOT_FILES if (root / name).is_file()}
    files.add(root / 'release/version.json')
    for name in LIVE_DIRS:
        base = root / name
        if base.exists():
            for path in base.rglob('*'):
                if any(part in EXCLUDED for part in path.relative_to(base).parts):
                    continue
                if path.is_symlink():
                    raise ValueError('symlink in live package: ' + str(path.relative_to(root)))
                if path.is_file():
                    files.add(path)
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}


def version_issues(root):
    root = Path(root)
    version = json.loads((root / 'release/version.json').read_text())['version']
    issues = []
    for name in ('plugin.json', '.codex-plugin/plugin.json', 'capabilities.json',
                 'tests/browser/package.json', 'tests/browser/package-lock.json'):
        value = json.loads((root / name).read_text()).get('version')
        if value != version:
            issues.append(f'{name}: version {value!r}, expected {version!r}')
    lock = json.loads((root / 'tests/browser/package-lock.json').read_text())
    if lock.get('packages', {}).get('', {}).get('version') != version:
        issues.append('tests/browser/package-lock.json: root package version mismatch')
    patterns = {'tools/project_model.py': r"VERSION\s*=\s*['\"]([^'\"]+)",
                'README.md': r'^# Software Architect Studio ([0-9.]+)',
                'skills/software-architecture/SKILL.md': r'Software Architect Studio[^\n]*?(\d+\.\d+\.\d+)'}
    for name, pattern in patterns.items():
        match = re.search(pattern, (root / name).read_text(), re.M)
        if not match or match.group(1) != version:
            issues.append(f'{name}: current release identity does not match {version}')
    html = (root / 'workbench/index.html').read_text()
    for pattern in (r'<title>[^<]*Workbench ([0-9.]+)', r'toolkit ([0-9.]+)'):
        match = re.search(pattern, html)
        if not match or match.group(1) != version:
            issues.append('workbench/index.html: display version mismatch')
    for skill in sorted((root / 'skills').glob('*/SKILL.md')):
        match = re.search(r'^version:\s*([0-9.]+)\s*$', skill.read_text(), re.M)
        if not match or match.group(1) != version:
            issues.append(f'{skill.relative_to(root)}: skill version mismatch')
    return issues


def compare(expected, current):
    return {'missing': sorted(expected.keys() - current.keys()),
            'unlisted': sorted(current.keys() - expected.keys()),
            'changed': sorted(k for k in expected.keys() & current.keys()
                              if expected[k] != current[k])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--write', action='store_true', help='Refresh after reviewing intended source changes')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    path = root / 'release/source-manifest.json'
    try:
        issues = version_issues(root)
        if issues:
            print(json.dumps({'ok': False, 'version_issues': issues}, indent=2))
            return 1
        files = inventory(root)
        if args.write:
            version = json.loads((root / 'release/version.json').read_text())['version']
            payload = {'release': version, 'hash': 'sha256',
                       'scope': 'Live plugin source, skills, schemas, docs, examples, tests and CI; excludes audits/**, generated dependencies/results, release reports/receipts except version.json and this self-referential manifest.',
                       'files': files}
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
            print(json.dumps({'ok': True, 'written': str(path.relative_to(root)), 'files': len(files)}))
            return 0
        expected = json.loads(path.read_text())
        diff = compare(expected['files'], files)
        release = json.loads((root / 'release/version.json').read_text())['version']
        ok = not any(diff.values()) and expected.get('release') == release
        print(json.dumps({'ok': ok, 'files': len(files), 'differences': diff,
                          'manifest_release': expected.get('release'), 'expected_release': release}, indent=2))
        return 0 if ok else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'ok': False, 'error': type(exc).__name__ + ': ' + str(exc)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
