"""Bounded read-only source evidence; no inspected repository code is executed.

Parse deadlines are cooperative. Cached observations are untrusted accelerators and
cannot independently establish a clean architecture fitness result.
"""
from __future__ import annotations
import ast
import copy
import datetime
import json
import math
import os
import re
import stat
import time
from pathlib import Path
from project_model import require_project, VERSION
from safe_io import digest, read_bytes, guard

IGNORE = {'.git', 'node_modules', '.next', 'dist', 'build', '__pycache__', 'vendor', '.venv', 'coverage', '.architecture-history', '.architecture-generations'}
MANIFESTS = {'package.json', 'pyproject.toml', 'requirements.txt', 'go.mod', 'Cargo.toml', 'pom.xml', 'build.gradle', 'Dockerfile', 'docker-compose.yml', 'compose.yaml', 'Makefile'}
SOURCE = {'.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.java', '.cs', '.php', '.rb', '.sql', '.kt'}
CONFIG = {'.json', '.yaml', '.yml', '.toml', '.tf'}
ADAPTER_VERSION = 'local-static-2'
PER_FILE_RECORDS = 100
CACHE_MAX_BYTES = 4 * 1024 * 1024


def minimize(text):
    from disclosure import redact_text
    text = redact_text(text)
    text = re.sub(r'(?i)(token|secret|password|api[_-]?key)\s*[:=]\s*[\"\']?[^\s\"\',;)]+', r'\1=[REDACTED]', text)
    text = re.sub(r'([\"\'])(?:(?!\1).)*?\1', '[literal withheld]', text)
    return text[:160]


def _python(text):
    tree = ast.parse(text)
    items, edges = [], []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            level = node.level if isinstance(node, ast.ImportFrom) else 0
            module = node.module if isinstance(node, ast.ImportFrom) else None
            names = [a.name for a in node.names]
            # Preserve relative syntax and imported symbols; never guess package roots.
            targets = [a.name for a in node.names] if isinstance(node, ast.Import) else [('.' * level) + (module or name) for name in ([''] if module else names)]
            for target in targets:
                detail = {'target': target, 'module': module, 'relative_level': level, 'imported_names': names, 'resolution': 'unresolved' if level else 'declared module', 'line': node.lineno, 'end_line': getattr(node, 'end_lineno', node.lineno)}
                items.append({**detail, 'observation': 'parsed Python import', 'class': 'PARSED'})
                edges.append({**detail, 'kind': 'imports'})
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}:
                    if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                        items.append({'line': dec.lineno, 'end_line': getattr(dec, 'end_lineno', dec.lineno), 'observation': 'parsed route decorator candidate', 'method': dec.func.attr.upper(), 'route': dec.args[0].value, 'class': 'PARSED; framework binding unverified'})
    return items, edges


def _javascript(text):
    # Only static import and export-from declarations; do not cross statement starts.
    token = re.compile(r'(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)|(?P<string>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(?P<template>`(?:\\.|[^`\\])*`)|(?P<word>[A-Za-z_$][\w$]*)|(?P<punct>[^\s])')
    tokens, line, end = [], 1, 0
    for m in token.finditer(text):
        line += text[end:m.start()].count('\n')
        at = line
        line += m[0].count('\n')
        end = m.end()
        if m.lastgroup not in {'comment', 'template'}:
            tokens.append((m.lastgroup, m[0], at))
    items, edges = [], []
    for i, (kind, value, at) in enumerate(tokens):
        if kind != 'word' or value not in {'import', 'export'}:
            continue
        tail = tokens[i + 1:i + 80]
        if not tail:
            continue
        # export const/function/default are not module re-exports; import() is dynamic.
        if value == 'export' and tail[0][1] not in {'{', '*', 'type'}:
            continue
        if value == 'import' and tail[0][1] in {'(', '.'}:
            continue
        target = None
        if value == 'import' and tail[0][0] == 'string':
            target = tail[0][1][1:-1]
        else:
            for j, entry in enumerate(tail[:-1]):
                if entry[1] in {';', 'import', 'export', '='} or entry[2] > at + 8:
                    break
                if entry[:2] == ('word', 'from') and tail[j + 1][0] == 'string':
                    target = tail[j + 1][1][1:-1]
                    break
        if target:
            items.append({'line': at, 'observation': 'JS/TS static module token declaration', 'target': target, 'class': 'TOKENIZED; unresolved'})
            edges.append({'kind': 'imports', 'target': target, 'line': at, 'resolution': 'unresolved'})
    return items, edges


def _descriptor(name, text, timeout=2):
    """Return supported declarations; failures propagate into typed extraction status."""
    if name.endswith('.json'):
        from codec import strict_json_loads
        data = strict_json_loads(text)
    elif name.endswith(('.yaml', '.yml')):
        from validation_engine import parse_yaml
        data = parse_yaml(text, timeout)
    elif name.endswith('.toml'):
        import tomllib
        data = tomllib.loads(text)
    elif name == 'requirements.txt':
        items, edges = [], []
        for line, raw in enumerate(text.splitlines(), 1):
            raw = raw.strip()
            if not raw or raw.startswith('#'):
                continue
            match = re.match(r'^([A-Za-z0-9][A-Za-z0-9_.-]*)(?:\[[^\]]+\])?(?:\s*[<>=!~;].*)?$', raw)
            if not match:
                raise NotImplementedError('requirements options/URLs/includes require manual review')
            target = match[1]
            items.append({'line': line, 'observation': 'Python requirement declaration', 'target': target, 'class': 'DECLARED CONFIG'})
            edges.append({'kind': 'package-depends-on', 'target': target, 'line': line})
        return items, edges
    else:
        raise NotImplementedError('no descriptor adapter for this format')
    if not isinstance(data, dict):
        raise ValueError('descriptor must be a mapping')
    items, edges = [], []
    if name == 'package.json':
        for kind in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies'):
            if kind in data and not isinstance(data[kind], dict):
                raise ValueError(kind + ' must be a mapping')
            for target in sorted(data.get(kind, {})):
                items.append({'line': 1, 'observation': kind, 'target': target, 'class': 'DECLARED CONFIG; whole-document span'})
                edges.append({'kind': 'package-depends-on', 'target': target, 'line': 1})
    if name == 'pyproject.toml':
        dependencies = data.get('project', {}).get('dependencies', [])
        if not isinstance(dependencies, list) or any(not isinstance(x, str) for x in dependencies):
            raise ValueError('project.dependencies must be strings')
        for requirement in dependencies:
            match = re.match(r'[A-Za-z0-9][A-Za-z0-9_.-]*', requirement)
            if not match:
                raise ValueError('invalid project dependency')
            items.append({'line': 1, 'observation': 'project.dependencies', 'target': match[0], 'class': 'DECLARED CONFIG; whole-document span'})
            edges.append({'kind': 'package-depends-on', 'target': match[0], 'line': 1})
    for key in ('services', 'jobs'):
        if key in data and not isinstance(data[key], dict):
            raise ValueError(key + ' must be a mapping')
        for identifier, entry in data.get(key, {}).items():
            items.append({'line': 1, 'observation': key + ' descriptor', 'target': identifier, 'class': 'DECLARED CONFIG; not deployed; whole-document span'})
            if isinstance(entry, dict):
                dependencies = entry.get('depends_on', []) if key == 'services' else entry.get('needs', [])
                if isinstance(dependencies, str):
                    dependencies = [dependencies]
                if not isinstance(dependencies, (list, dict)) or any(not isinstance(x, str) for x in dependencies):
                    raise ValueError('descriptor dependencies must be names')
                edges.extend({'kind': 'depends-on', 'source': identifier, 'target': target, 'line': 1} for target in dependencies)
    if 'openapi' in data or 'asyncapi' in data:
        collection = 'paths' if 'openapi' in data else 'channels'
        if not isinstance(data.get(collection), dict):
            raise ValueError(collection + ' must be a mapping')
        items.extend({'line': 1, 'observation': collection + ' contract entry', 'target': target, 'class': 'DECLARED CONTRACT; whole-document span'} for target in data[collection])
    return items, edges


def _extract(path, text, kind, timeout):
    status, diagnostics, adapter = 'parsed', [], 'descriptor'
    try:
        suffix = path.suffix.lower()
        if suffix == '.py':
            adapter = 'python-ast'
            items, edges = _python(text)
        elif suffix in {'.js', '.ts', '.tsx', '.jsx'}:
            adapter = 'js-static-tokens'
            items, edges = _javascript(text)
            status = 'tokenized'
        elif kind in {'manifest', 'infrastructure/config'}:
            items, edges = _descriptor(path.name, text, timeout)
        else:
            raise NotImplementedError('no language adapter')
    except NotImplementedError:
        status, items, edges = 'unsupported', [], []
        diagnostics.append({'reason': 'unsupported adapter; content identity only'})
    except ImportError:
        status, items, edges = 'blocked', [], []
        diagnostics.append({'reason': 'required descriptor parser unavailable'})
    except (ValueError, SyntaxError, TypeError, RecursionError, UnicodeError) as error:
        status, items, edges = ('timed_out' if str(error).startswith('bounded YAML parse timed_out') else 'parse_failed'), [], []
        diagnostics.append({'reason': 'parser error', 'error_type': type(error).__name__, 'line': getattr(error, 'lineno', None)})
    counts = {'declarations': len(items), 'edges': len(edges)}
    if len(items) > PER_FILE_RECORDS:
        diagnostics.append({'reason': 'declaration quota', 'count': len(items) - PER_FILE_RECORDS})
    if len(edges) > PER_FILE_RECORDS:
        diagnostics.append({'reason': 'edge quota', 'count': len(edges) - PER_FILE_RECORDS})
    if any('quota' in d['reason'] for d in diagnostics):
        status = 'partial'
    return {'status': status, 'adapter': adapter, 'diagnostics': diagnostics, 'items': items[:PER_FILE_RECORDS], 'edges': edges[:PER_FILE_RECORDS], 'extracted_counts': counts}


def repo_scan(root, project=None, limit=400, *, max_entries=10000, max_bytes=10_000_000, deadline=5.0, include_snippets=False, cache=None):
    root = guard(root)
    if not root.is_dir():
        raise ValueError('Expected a local repository directory')
    for key, value in [('limit', limit), ('max_entries', max_entries), ('max_bytes', max_bytes)]:
        if type(value) is not int or not 1 <= value <= 10_000_000:
            raise ValueError(key + ' must be a positive bounded integer')
    if isinstance(deadline, bool) or not isinstance(deadline, (int, float)) or not math.isfinite(deadline) or not 0 < deadline <= 60:
        raise ValueError('deadline must be in (0,60] seconds')
    start = time.monotonic()
    stack, candidates, omissions, stop = [root], [], [], []
    visited = files = 0
    complete = True
    cache_path = guard(cache) if cache is not None else None
    while stack:
        base = stack.pop()
        if time.monotonic() - start > deadline:
            stop.append('enumeration deadline'); complete = False; break
        children = []
        try:
            with os.scandir(base) as entries:
                for entry in entries:
                    if visited >= max_entries or time.monotonic() - start > deadline:
                        complete = False; stop.append('entry/time budget'); break
                    visited += 1
                    rel = Path(entry.path).relative_to(root).as_posix()
                    try:
                        info = entry.stat(follow_symlinks=False)
                        if stat.S_ISLNK(info.st_mode):
                            omissions.append({'path': rel, 'reason': 'symlink'}); continue
                        if stat.S_ISDIR(info.st_mode):
                            if entry.name in IGNORE:
                                omissions.append({'path': rel, 'reason': 'excluded directory'})
                            else:
                                children.append(Path(entry.path))
                            continue
                        files += 1
                        if not stat.S_ISREG(info.st_mode):
                            omissions.append({'path': rel, 'reason': 'special file; never opened'}); continue
                        path = Path(entry.path)
                        if cache_path is not None and path == cache_path:
                            continue
                        suffix = path.suffix.lower()
                        kind = 'manifest' if path.name in MANIFESTS else 'infrastructure/config' if suffix in CONFIG or '.github' in path.parts else 'source' if suffix in SOURCE else None
                        if kind is None:
                            omissions.append({'path': rel, 'reason': 'unsupported extension'}); continue
                        priority = 0 if kind == 'manifest' or '.github' in path.parts else 1 if kind == 'infrastructure/config' else 2
                        candidates.append((priority, rel, path, kind))
                    except OSError:
                        omissions.append({'path': rel, 'reason': 'inaccessible metadata'})
        except OSError:
            omissions.append({'path': str(base.relative_to(root)), 'reason': 'inaccessible directory'})
        if not complete:
            break
        stack.extend(sorted(children, reverse=True))
    observed, declarations, dependencies = [], [], []
    read = byte_count = cache_hits = 0
    cached, new_cache = {}, {}
    if cache_path is not None and cache_path.exists():
        from safe_io import read_json
        saved = read_json(cache_path)
        if not isinstance(saved, dict) or type(saved.get('cache_schema')) is not int or saved.get('cache_schema') not in {1, 2} or not isinstance(saved.get('entries'), dict):
            raise ValueError('Unowned or invalid cache file preserved; choose a new cache path')
        if saved.get('cache_schema') == 2 and saved.get('adapter_version') == ADAPTER_VERSION and saved.get('root') == str(root):
            cached = saved['entries']
    for _, rel, path, kind in sorted(candidates):
        if read >= limit or time.monotonic() - start > deadline:
            stop.append('read count/time budget'); omissions.append({'path': rel, 'reason': 'not read due to budget'}); continue
        try:
            remaining = min(300_000, max_bytes - byte_count)
            if remaining < 1:
                stop.append('total byte budget'); omissions.append({'path': rel, 'reason': 'not read due to byte budget'}); continue
            blob = read_bytes(path, remaining)
            byte_count += len(blob); read += 1
            sha = digest(blob)
            text = blob.decode('utf-8', errors='strict')
            key = rel + ':' + sha
            extraction = cached.get(key)
            if not _valid_cached_extraction(extraction):
                extraction = _extract(path, text, kind, max(.05, min(2, deadline - (time.monotonic() - start))))
                from disclosure import minimized
                extraction = minimized(extraction)
                provenance = 'fresh extraction'
            else:
                extraction = copy.deepcopy(extraction)
                cache_hits += 1
                provenance = 'untrusted cache; recollect without cache for a clean fitness gate'
            new_cache[key] = extraction
            observed.append({'path': rel, 'kind': kind, 'line': 1, 'observation': 'regular file read; static evidence only', 'bytes': len(blob), 'sha256': sha, 'source': 'local', 'source_revision': 'unpinned local tree', 'extractor_version': ADAPTER_VERSION, 'extraction': extraction['status'], 'adapter': extraction['adapter'], 'extracted_counts': extraction['extracted_counts'], 'emitted_counts': {'declarations': len(extraction['items']), 'edges': len(extraction['edges'])}, 'evidence_provenance': provenance})
            omissions.extend({'path': rel, **detail} for detail in extraction['diagnostics'])
            for item in extraction['items']:
                item = copy.deepcopy(item)
                item.update(path=rel, sha256=sha)
                if include_snippets:
                    lines = text.splitlines()
                    item['snippet'] = minimize(lines[max(0, min(len(lines) - 1, item.get('line', 1) - 1))]) if lines else ''
                declarations.append(item)
            dependencies.extend({**edge, 'path': rel, 'sha256': sha} for edge in extraction['edges'])
            if time.monotonic() - start > deadline:
                stop.append('cooperative parse deadline exceeded')
        except (OSError, ValueError, UnicodeError):
            omissions.append({'path': rel, 'reason': 'unread: unavailable, nonregular, invalid encoding or byte budget exceeded'})
    cache_status = 'not requested'
    if cache_path is not None:
        from safe_io import atomic_write, dumps
        serialized = dumps({'cache_schema': 2, 'adapter_version': ADAPTER_VERSION, 'root': str(root), 'entries': new_cache, 'trust': 'editable performance data, not verification evidence', 'retention': 'local opt-in; delete to purge'})
        if len(serialized.encode()) > CACHE_MAX_BYTES:
            cache_status = 'not saved: cache byte budget exceeded'
        else:
            try:
                atomic_write(cache_path, serialized)
                cache_status = 'saved'
            except (OSError, ValueError):
                cache_status = 'not saved: cache write failed; scan evidence retained'
    elapsed = time.monotonic() - start
    result = {'schema_version': 1, 'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source_ref': 'unpinned local tree; resolved commit not inferred', 'claim_class': 'OBSERVED STATIC SOURCE', 'root': str(root), 'adapter': 'local-static', 'adapter_version': ADAPTER_VERSION, 'observed_files': observed, 'static_declarations': declarations, 'dependency_edges': dependencies, 'scanned_count': read, 'total_candidate_files': files if complete else None, 'discovered_files': files, 'entries_visited': visited, 'eligible_discovered': len(candidates), 'bytes_read': byte_count, 'skipped_files': len(omissions), 'omissions': omissions, 'enumeration_complete': complete, 'coverage': 'partial' if stop or omissions else 'complete within supported static scope', 'stop_reasons': sorted(set(stop)), 'cache_hits': cache_hits, 'cache_status': cache_status, 'elapsed_seconds': elapsed, 'deadline_seconds': deadline, 'deadline_enforcement': 'cooperative including parsing; not a hard wall-clock bound', 'deadline_overrun_seconds': max(0, elapsed - deadline), 'collection_policy': {'limit': limit, 'max_entries': max_entries, 'max_bytes': max_bytes, 'per_file_bytes': 300_000, 'per_file_records': PER_FILE_RECORDS}, 'source_fingerprint': digest([{k: record[k] for k in ('path', 'sha256')} for record in observed]), 'coverage_note': 'Read-only bounded static evidence. Python AST, narrow JS static imports, JSON/YAML/TOML and conservative Python requirements adapters; no runtime/full dependency/framework guarantee. Local source is not commit-pinned. Snippets off by default.'}
    if project is not None:
        require_project(project)
        deviations = []
        for component in project['components']:
            for rel in component.get('files', []):
                try:
                    if Path(rel).is_absolute() or '..' in Path(rel).parts:
                        raise ValueError('escaping path')
                    path = guard(root / rel, root)
                    if not path.exists(): status = 'not found'
                    elif not path.is_file(): status = 'not a regular file'
                    elif rel not in {o['path'] for o in observed}: status = 'exists but unread/excluded'
                    else: continue
                except (OSError, ValueError):
                    status = 'unverifiable path; symlink/escape/inaccessible'
                deviations.append({'component': component['id'], 'path': rel, 'status': status, 'reason': 'mapped path requires scoped review; absence of behavior not proven'})
        result['drift_candidates'] = deviations
        result['unmapped_components'] = [c['id'] for c in project['components'] if not c.get('files')]
    return result


def _valid_cached_extraction(value):
    return isinstance(value, dict) and isinstance(value.get('status'), str) and value.get('status') in {'parsed', 'tokenized', 'partial', 'unsupported', 'blocked', 'parse_failed', 'timed_out'} and isinstance(value.get('adapter'), str) and isinstance(value.get('diagnostics'), list) and all(isinstance(x, dict) and isinstance(x.get('reason'), str) for x in value['diagnostics']) and isinstance(value.get('items'), list) and isinstance(value.get('edges'), list) and len(value['items']) <= PER_FILE_RECORDS and len(value['edges']) <= PER_FILE_RECORDS and all(isinstance(x, dict) for x in value['items'] + value['edges']) and isinstance(value.get('extracted_counts'), dict)


def _validate_envelope(scan):
    if not isinstance(scan, dict) or scan.get('schema_version') != 1 or not all(isinstance(scan.get(k), str) and scan[k] for k in ('adapter', 'adapter_version', 'root', 'coverage_note')) or not isinstance(scan.get('observed_files'), list):
        raise ValueError('invalid evidence envelope')
    for collection in ('dependency_edges', 'omissions', 'stop_reasons'):
        if collection in scan and not isinstance(scan[collection], list):
            raise ValueError('invalid evidence ' + collection)
    if any(not isinstance(edge, dict) for edge in scan.get('dependency_edges', [])) or any(not isinstance(item, dict) for item in scan.get('omissions', [])):
        raise ValueError('invalid evidence edge/omission')
    seen = set()
    for record in scan['observed_files']:
        if not isinstance(record, dict):
            raise ValueError('invalid observed file')
        path, sha = record.get('path'), record.get('sha256')
        if not isinstance(path, str) or not path or Path(path).is_absolute() or '..' in Path(path).parts or path in seen or not isinstance(sha, str) or not re.fullmatch('[a-f0-9]{64}', sha):
            raise ValueError('invalid or duplicate evidence path/hash')
        seen.add(path)


def evidence_delta(before, after, *, allow_cross_tree=False):
    _validate_envelope(before); _validate_envelope(after)
    reasons = []
    for key in ('adapter', 'adapter_version', 'collection_policy'):
        if before.get(key) != after.get(key):
            reasons.append(key + ' differs; recollect equivalent scope')
    same_repository = before.get('repository_identity') and before.get('repository_identity') == after.get('repository_identity')
    if before['root'] != after['root'] and not same_repository and not allow_cross_tree:
        reasons.append('different roots require repository_identity or explicit allow_cross_tree')
    if reasons:
        return {'status': 'unknown', 'reason': '; '.join(reasons), 'coverage': [before.get('coverage'), after.get('coverage')]}
    a = {r['path']: r['sha256'] for r in before['observed_files']}
    b = {r['path']: r['sha256'] for r in after['observed_files']}
    return {'status': 'compared-in-observed-scope', 'added': sorted(b.keys() - a.keys()), 'removed_or_unread': sorted(a.keys() - b.keys()), 'changed': sorted(k for k in a.keys() & b.keys() if a[k] != b[k]), 'coverage': [before.get('coverage'), after.get('coverage')], 'cross_tree': before['root'] != after['root'], 'scope': 'observed files only; unread is not deleted'}


def fitness(p, scan):
    require_project(p); _validate_envelope(scan)
    results = []
    for rule in p.get('fitness_rules', []):
        if rule.get('kind') != 'forbid_import':
            results.append({'id': rule['id'], 'status': 'unknown', 'reason': 'unsupported rule kind'}); continue
        prefix, target = rule.get('source_prefix'), rule.get('target_prefix')
        if not isinstance(prefix, str) or not isinstance(target, str) or not target:
            raise ValueError('fitness source_prefix/target_prefix required')
        scope = [r for r in scan['observed_files'] if r['path'].startswith(prefix)]
        # Match import edges only; package/CI associations cannot prove a code import.
        bad = [e for e in scan.get('dependency_edges', []) if isinstance(e, dict) and e.get('kind') == 'imports' and isinstance(e.get('path'), str) and e['path'].startswith(prefix) and isinstance(e.get('target'), str) and e['target'].lstrip('.').startswith(target)]
        unevaluated = [r['path'] for r in scope if r.get('adapter') not in {'python-ast', 'js-static-tokens'} or r.get('extraction') not in {'parsed', 'tokenized'} or r.get('evidence_provenance') != 'fresh extraction']
        omitted = [o for o in scan.get('omissions', []) if isinstance(o.get('path'), str) and (o['path'].startswith(prefix) or prefix.startswith(o['path'].rstrip('/') + '/'))]
        unresolved_relative = any(edge.get('relative_level', 0) for edge in scan.get('dependency_edges', []) if edge.get('kind') == 'imports' and isinstance(edge.get('path'), str) and edge['path'].startswith(prefix))
        uncertain = not scope or unevaluated or omitted or unresolved_relative or not scan.get('enumeration_complete') or scan.get('stop_reasons')
        reason = 'supported fresh static import scope evaluated' if not uncertain else 'scope unsupported, unread, partial, failed or cached; rerun without cache and inspect omissions'
        results.append({'id': rule['id'], 'status': 'violation' if bad else 'unknown' if uncertain else 'satisfied-in-scope', 'counterexamples': bad, 'evaluated_files': [r['path'] for r in scope if r['path'] not in unevaluated], 'unevaluated_files': unevaluated, 'coverage': scan.get('coverage'), 'reason': reason, 'note': 'Declared static import evidence only; cached findings are attributed candidates, not authenticated truth. No global/runtime compliance inferred.'})
    return {'rules': results, 'source_fingerprint': scan.get('source_fingerprint'), 'project_hash': digest(p)}
