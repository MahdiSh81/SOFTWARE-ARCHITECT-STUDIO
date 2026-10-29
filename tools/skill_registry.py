"""Local skill discovery, explicit bundle provenance and conservative task suggestions.

Routing is a deterministic aid, not a measured model selector or authorization grant.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
from codec import digest

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
# Task ownership is deliberately small; references carry language-specific detail.
RULES = {
    'requirements-specification': (r'acceptance criteria', r'clarify.*requirement', r'discovery', r'feature scope', r'non.functional', r'contradict.*constraint'),
    'repository-intelligence': (r'map.*repo', r'unfamiliar.*code', r'dependency graph', r'architecture drift', r'scan.*repo', r'codebase.*understand'),
    'implementation-planning-and-change': (r'implement', r'scaffold', r'refactor', r'code change', r'patch', r'add.*feature'),
    'test-debug-verify': (r'debug', r'failing test', r'stack trace', r'regression', r'reproduce.*bug', r'test failure'),
    'security-review': (r'threat model', r'security review', r'secret leak', r'vulnerabilit', r'authorization review', r'privacy review'),
    'api-data-contracts': (r'openapi', r'asyncapi', r'contract.*compatib', r'api schema', r'data contract', r'resolve.*reference'),
    'frontend-interaction-and-accessibility': (r'keyboard', r'accessib', r'responsive', r'frontend', r'form.*(?:error|loading|state)', r'ui interaction'),
    'service-and-data-implementation': (r'idempotent.*(?:endpoint|worker)', r'database migration', r'backfill', r'transaction', r'event handler', r'backend'),
    'delivery-and-operations': (r'deploy', r'release gate', r'production incident', r'runbook', r'ci/cd', r'backup restore', r'latency incident'),
    'ai-system-evaluation-and-safety': (r'\brag\b', r'evaluate.*(?:prompt|model|agent)', r'compare.*prompt', r'llm.*(?:quality|safety)', r'retrieval.*(?:acl|isolation)', r'model.*benchmark'),
}


def _root(root=None):
    return Path(root).resolve() if root else DEFAULT_ROOT


def discover_skills(root=None):
    """Discover only regular skill roots below the selected package; do not load instructions."""
    root = _root(root)
    if not (root / 'skills').is_dir():
        raise ValueError('selected package has no skills directory')
    records = []
    paths = sorted((root / 'skills').glob('*/SKILL.md'))
    if len(paths) > 1000:
        raise ValueError('skill inventory exceeds entry budget')
    for path in paths:
        if path.is_symlink() or path.parent.is_symlink():
            raise ValueError('symlink skill definition disallowed')
        raw = path.read_bytes()
        if len(raw) > 256_000:
            raise ValueError('skill definition exceeds byte budget')
        text = raw.decode('utf-8')
        header = text.split('---', 2)[1] if text.startswith('---\n') else ''
        values = dict(re.findall(r'^([a-z_]+):\s*(.+)$', header, re.M))
        name = values.get('name', '').strip('"\'')
        if name != path.parent.name:
            raise ValueError('skill directory/name mismatch: ' + path.parent.name)
        records.append({'id': name, 'path': str(path.relative_to(root)),
                        'description': values.get('description', '').strip('"\''),
                        'version': values.get('version', 'unversioned'),
                        'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                        'references': [str(p.relative_to(root)) for p in sorted(path.parent.rglob('*.md')) if p != path]})
    return {'schema_version': 1, 'skills': records,
            'scope': 'local packaged skill definitions; discovery does not execute or grant tool authority'}


def loaded_bundle(root=None, skills=None, references=None):
    """Hash the explicitly declared loaded context. Caller declaration is not attestation."""
    root = _root(root)
    registry = {s['id']: s for s in discover_skills(root)['skills']}
    selected = ['software-architecture'] if skills is None else skills
    if not isinstance(selected, list) or len(selected) > 1000 or any(not isinstance(s, str) for s in selected):
        raise ValueError('skills must be an array of known skill IDs')
    refs = [] if references is None else references
    if not isinstance(refs, list) or len(refs) > 1000 or any(not isinstance(s, str) for s in refs):
        raise ValueError('references must be an array of package-relative Markdown paths')
    paths = set(refs)
    for name in selected:
        if name not in registry:
            raise ValueError('unknown skill: ' + name)
        paths.add(registry[name]['path'])
    entries = []
    for relative in sorted(paths):
        supplied = Path(relative)
        if supplied.is_absolute() or '..' in supplied.parts or supplied.suffix != '.md' or not supplied.parts or supplied.parts[0] != 'skills':
            raise ValueError('bundle reference must be a Markdown path beneath skills/')
        path = root / supplied
        if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
            raise ValueError('symlink bundle reference disallowed')
        if not path.is_file() or root not in path.resolve().parents:
            raise ValueError('missing or escaping skill reference')
        raw = path.read_bytes()
        if len(raw) > 256_000:
            raise ValueError('bundle entry exceeds byte budget')
        entries.append({'path': relative, 'skill_id': supplied.parts[1], 'sha256': hashlib.sha256(raw).hexdigest()})
    return {'schema_version': 1, 'entries': entries, 'bundle_hash': digest(entries),
            'provenance': 'caller-declared loaded files; not an authenticated context trace'}


def inventory_bundle(root=None):
    root = _root(root)
    registry = discover_skills(root)['skills']
    return loaded_bundle(root, [s['id'] for s in registry], [p for s in registry for p in s['references']])


def route_task(task, root=None, override=None):
    if not isinstance(task, str) or not task.strip() or len(task) > 20_000:
        raise ValueError('bounded nonempty task required')
    known = {s['id'] for s in discover_skills(root)['skills']}
    if override is not None and (not isinstance(override, str) or override not in known):
        raise ValueError('unknown routing override')
    scores = {name: sum(bool(re.search(pattern, task, re.I)) for pattern in patterns) for name, patterns in RULES.items() if name in known}
    candidates = sorted(({'skill': name, 'matches': score} for name, score in scores.items() if score), key=lambda x: (-x['matches'], x['skill']))
    # A conceptual answer needs no implementation pipeline or file-based context.
    conceptual = bool(re.match(r'\s*(?:what is|explain|compare|why|define)\b', task, re.I)) and not re.search(r'\b(?:implement|debug|fix|evaluate|review|deploy|change)\b|acceptance criteria|feature scope|prompt variants', task, re.I)
    ambiguous = bool(candidates and len(candidates) > 1 and candidates[0]['matches'] == candidates[1]['matches']) and not conceptual
    primary = override or ('software-architecture' if conceptual or not candidates else candidates[0]['skill'])
    return {'schema_version': 1, 'primary': primary, 'owner': primary, 'skills': [primary], 'selected_skills': [primary],
            'candidates': candidates, 'ambiguous': ambiguous and override is None,
            'confidence': 'high' if override else 'low' if ambiguous or not candidates else 'medium',
            'status': 'manual_override' if override else 'needs_clarification' if ambiguous else 'suggested',
            'reason': 'explicit user/host override' if override else 'conceptual advice remains with coordinator' if conceptual else 'deterministic term matches; review task ownership before acting',
            'execution': 'suggestion only; no skill invocation, tool permission or measured model-quality claim'}
