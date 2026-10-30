"""Opt-in local editing/check adapter. Host policy, not project text, grants effects.

This is a cooperating local runner, not an OS/network sandbox. Policy files must be
selected by the caller from trusted host configuration. No remote provider is used.
"""
from __future__ import annotations
import datetime
import fnmatch
import os
import re
import subprocess
import uuid
from pathlib import Path, PurePosixPath
from safe_io import guard, read_bytes, read_json, atomic_write, digest, dumps, project_lock
from project_model import VERSION
from validation_engine import bounded_process
from integration_contracts import validate_tool_result

TOOL_ID = 'studio.local'
OPERATIONS = ('capabilities', 'inspect', 'propose_change', 'apply_change', 'run_checks', 'recover', 'reconcile')
EXCLUDE = {'.git', '__pycache__', 'node_modules', '.venv', '.studio-operations'}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


_HASH_SCHEMA = {'type': 'string', 'pattern': '^[a-f0-9]{64}$'}
_OPERATION_SCHEMA = {'type': 'string', 'pattern': '^[A-Za-z0-9_-]{2,100}$'}
_CHANGE_SCHEMA = {'type': 'object', 'required': ['path', 'content'], 'additionalProperties': False,
                  'properties': {'path': {'type': 'string', 'minLength': 1},
                                 'content': {'type': ['string', 'null'], 'maxLength': 1000000}}}
_PLAN_CHANGE_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['path', 'content', 'before_hash', 'after_hash'],
    'properties': {**_CHANGE_SCHEMA['properties'],
                   'before_hash': {'type': ['string', 'null'], 'pattern': '^[a-f0-9]{64}$'},
                   'after_hash': {'type': ['string', 'null'], 'pattern': '^[a-f0-9]{64}$'}},
}
_PLAN_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['schema_version', 'root', 'input_source_hash', 'changes', 'plan_hash'],
    'properties': {'schema_version': {'type': 'integer', 'const': 1},
                   'root': {'type': 'string', 'minLength': 1},
                   'input_source_hash': _HASH_SCHEMA, 'plan_hash': _HASH_SCHEMA,
                   'changes': {'type': 'array', 'minItems': 1, 'maxItems': 100, 'items': _PLAN_CHANGE_SCHEMA},
                   'status': {'const': 'proposed; no files changed'}},
}
_REQUEST_FIELDS = {
    'capabilities': ({}, []), 'inspect': ({}, []),
    'propose_change': ({'changes': {'type': 'array', 'minItems': 1, 'maxItems': 100, 'items': _CHANGE_SCHEMA},
                        'expected_source_hash': _HASH_SCHEMA}, ['changes']),
    'apply_change': ({'plan': _PLAN_SCHEMA,
                      'operation_id': _OPERATION_SCHEMA}, ['plan']),
    'run_checks': ({'names': {'type': 'array', 'minItems': 1, 'maxItems': 100, 'uniqueItems': True, 'items': {'type': 'string', 'minLength': 1}},
                    'expected_source_hash': _HASH_SCHEMA, 'operation_id': _OPERATION_SCHEMA}, ['names', 'expected_source_hash']),
    'recover': ({'operation_id': _OPERATION_SCHEMA}, ['operation_id']),
    'reconcile': ({'receipt': {'type': 'object'}, 'expected_operation': _OPERATION_SCHEMA,
                   'expected_source_hash': _HASH_SCHEMA,
                   'required_checks': {'type': 'array', 'items': {'type': 'string'}}},
                  ['receipt', 'expected_operation', 'expected_source_hash', 'required_checks']),
}


def request_schema(operation):
    properties, required = _REQUEST_FIELDS[operation]
    return {'type': 'object', 'additionalProperties': False, 'properties': properties, 'required': required}


def _check_shape(schema, value, path='request', depth=0):
    """Check our fixed request-schema subset without optional dependencies.

    This is deliberately not a general JSON Schema engine. The optional engine
    below independently checks the same emitted schemas when installed.
    """
    if depth > 64:
        raise ValueError('adapter request nesting limit exceeded')
    types = schema.get('type')
    if isinstance(types, str):
        types = [types]
    predicates = {'object': lambda x: isinstance(x, dict), 'array': lambda x: isinstance(x, list),
                  'string': lambda x: isinstance(x, str), 'null': lambda x: x is None,
                  'integer': lambda x: type(x) is int}
    if types and not any(predicates[t](value) for t in types):
        raise ValueError(path + ': invalid value type')
    if 'const' in schema and (value != schema['const'] or type(value) is not type(schema['const'])):
        raise ValueError(path + ': unsupported value/version')
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise ValueError(path + ': string field names required')
        properties = schema.get('properties', {})
        if set(schema.get('required', [])) - set(value):
            raise ValueError(path + ': required fields missing')
        if schema.get('additionalProperties') is False and set(value) - set(properties):
            raise ValueError(path + ': unknown fields')
        for key, child in value.items():
            if key in properties:
                _check_shape(properties[key], child, path + '/' + key, depth + 1)
    elif isinstance(value, list):
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', 10000):
            raise ValueError(path + ': array size outside bounds')
        if schema.get('uniqueItems') and any(item in value[:i] for i, item in enumerate(value)):
            raise ValueError(path + ': duplicate array items')
        for child in value:
            _check_shape(schema.get('items', {}), child, path + '/item', depth + 1)
    elif isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', 1000000):
            raise ValueError(path + ': string length outside bounds')
        if schema.get('pattern') and not re.fullmatch(schema['pattern'], value):
            raise ValueError(path + ': invalid identifier/hash')


def validate_request(operation, request):
    if not isinstance(operation, str) or operation not in OPERATIONS or not isinstance(request, dict):
        raise ValueError('known adapter operation and request object required')
    schema = request_schema(operation)
    _check_shape(schema, request)
    try:
        from jsonschema import Draft202012Validator
        if next(Draft202012Validator(schema).iter_errors(request), None) is not None:
            raise ValueError('adapter request violates operation input schema')
    except ImportError:
        pass
    return request


def capabilities():
    return {'schema_version': 1, 'tool_id': TOOL_ID, 'tool_version': VERSION,
            'capabilities': [{'operation_id': name, 'description': name.replace('_', ' '),
                              'permission_class': 'write' if name in {'apply_change', 'run_checks'} else 'read',
                              'input_schema': request_schema(name), 'output_schema': {'type': 'object'},
                              'idempotent': name != 'run_checks', 'timeout_seconds': 120}
                             for name in OPERATIONS]}


def inspect(root, *, max_files=2000, max_bytes=20_000_000):
    root = guard(root)
    if not root.is_dir():
        raise ValueError('selected workspace must be a directory')
    files = {}
    total = 0
    def enumeration_error(error):
        raise error
    for base, dirs, names in os.walk(root, followlinks=False, onerror=enumeration_error):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE)
        for d in dirs:
            guard(Path(base) / d, root)
        for name in sorted(names):
            p = guard(Path(base) / name, root)
            data = read_bytes(p)
            total += len(data)
            if len(files) >= max_files or total > max_bytes:
                raise ValueError('source inspection budget exceeded; no complete identity available')
            files[p.relative_to(root).as_posix()] = digest(data)
    try:
        proc = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', 'HEAD'],
                              capture_output=True, text=True, timeout=5)
        commit = proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        commit = None
    identity = {'schema_version': 1, 'root': str(root), 'commit': commit, 'files': files,
                'exclusions': sorted(EXCLUDE)}
    return {**identity, 'source_hash': digest(identity), 'bytes_read': total,
            'scope': 'complete regular-file identity within declared exclusions; symlinks/special files refused'}


def _path(root, name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('nonempty POSIX relative path required')
    rel = PurePosixPath(name)
    if rel.is_absolute() or any(x in EXCLUDE | {'..', '.'} for x in rel.parts) or rel.as_posix() != name:
        raise ValueError('unsafe or noncanonical workspace path')
    return guard(Path(root) / name, root)


def _policy(root, policy, *, effect):
    if not isinstance(policy, dict) or type(policy.get('schema_version')) is not int or policy['schema_version'] != 1:
        raise ValueError('explicit host policy version 1 required')
    if policy.get('root') != str(guard(root)):
        raise ValueError('host policy is for a different workspace')
    ref = policy.get('authorization_reference')
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError('host authorization reference required for attempted effects')
    if policy.get('expires_at') is not None:
        try:
            if not isinstance(policy['expires_at'], str):
                raise ValueError('timestamp string required')
            expiry = datetime.datetime.fromisoformat(policy['expires_at'].replace('Z', '+00:00'))
            if expiry.tzinfo is None or expiry <= datetime.datetime.now(datetime.timezone.utc):
                raise ValueError('expired authorization')
        except (TypeError, ValueError):
            raise ValueError('valid future timezone-qualified authorization expiry required')
    if policy.get('allow_' + effect) is not True:
        raise ValueError('host policy does not authorize ' + effect)
    return ref


def propose_change(root, changes, expected_source_hash=None):
    request = {'changes': changes}
    if expected_source_hash is not None:
        request['expected_source_hash'] = expected_source_hash
    validate_request('propose_change', request)
    source = inspect(root)
    if expected_source_hash is not None and source['source_hash'] != expected_source_hash:
        raise ValueError('source conflict before proposal')
    if not isinstance(changes, list) or not 1 <= len(changes) <= 100:
        raise ValueError('1–100 bounded file changes required')
    output = []
    seen = set()
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError('change object required')
        name = change.get('path')
        p = _path(root, name)
        if name in seen:
            raise ValueError('duplicate change path')
        seen.add(name)
        content = change.get('content')
        if content is not None and (not isinstance(content, str) or len(content.encode()) > 1_000_000):
            raise ValueError('UTF-8 content up to 1 MB, or null for deletion, required')
        if not p.exists() and content is None:
            raise ValueError('cannot delete absent path')
        output.append({'path': name, 'before_hash': source['files'].get(name), 'content': content,
                       'after_hash': digest(content.encode()) if content is not None else None})
    plan = {'schema_version': 1, 'root': str(guard(root)), 'input_source_hash': source['source_hash'],
            'changes': output}
    result = {**plan, 'plan_hash': digest(plan), 'status': 'proposed; no files changed'}
    if len(dumps(result).encode()) > 5 * 1024 * 1024:
        raise ValueError('proposed plan exceeds 5 MiB transport budget')
    return result


def _state_root(root, state_root=None):
    root = guard(root)
    path = guard(state_root) if state_root else root.parent / ('.studio-operations-' + digest(str(root))[:16])
    if path == root or root in path.parents:
        raise ValueError('operation records must be outside source workspace')
    path.mkdir(parents=True, exist_ok=True)
    return path


def _operation_path(state_root, operation_id):
    if not isinstance(operation_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{2,100}', operation_id):
        raise ValueError('bounded safe operation id required')
    return guard(state_root / (operation_id + '.json'), state_root)


def _receipt(operation_id, capability, start, before, after, status, *, authorization=None,
             checks=(), checks_not_run=(), errors=(), effects=(), details=None):
    details = details or {}
    receipt = {'operation_id': operation_id, 'tool_id': TOOL_ID, 'tool_version': VERSION,
               'capability': capability, 'permission_class': 'write' if capability in {'apply_change', 'run_checks'} else 'read',
               'input_source_hash': before, 'input_schema_version': 1, 'started_at': start,
               'completed_at': _now(), 'status': status, 'output_hash': digest(details),
               'output_source_hash': after, 'checks_run': list(checks), 'checks_not_run': list(checks_not_run),
               'warnings': [], 'errors': list(errors), 'limitations': ['Local cooperating adapter; host must enforce filesystem/network permissions.'],
               'observed_effects': list(effects), 'details': details}
    if after is None:
        receipt.pop('output_source_hash', None)
    if authorization:
        receipt['authorization_reference'] = authorization
    return receipt


def apply_change(root, plan, policy, *, operation_id=None, state_root=None):
    _check_shape(_PLAN_SCHEMA, plan, 'plan')
    if len(dumps(plan).encode()) > 5 * 1024 * 1024:
        raise ValueError('plan exceeds 5 MiB transport budget')
    authorization = _policy(root, policy, effect='write')
    if not isinstance(plan, dict) or plan.get('root') != str(guard(root)):
        raise ValueError('plan workspace mismatch')
    payload = {k: plan[k] for k in ('schema_version', 'root', 'input_source_hash', 'changes')}
    if plan.get('plan_hash') != digest(payload):
        raise ValueError('plan identity mismatch')
    if policy.get('approved_plan_hash') is not None and policy['approved_plan_hash'] != plan['plan_hash']:
        raise ValueError('plan is not the host-approved diff')
    allowed = policy.get('allowed_paths')
    if not isinstance(allowed, list) or not allowed or any(not isinstance(x, str) for x in allowed):
        raise ValueError('explicit allowed_paths required')
    seen = set()
    for change in plan['changes']:
        _path(root, change['path'])
        if change['path'] in seen:
            raise ValueError('duplicate change path')
        seen.add(change['path'])
        if not any(fnmatch.fnmatchcase(change['path'], pat) for pat in allowed):
            raise ValueError('path outside authorized effects')
        content = change['content']
        if content is not None and len(content.encode()) > 1_000_000:
            raise ValueError('UTF-8 content exceeds 1 MB file budget')
        if change['after_hash'] != (digest(content.encode()) if content is not None else None):
            raise ValueError('content identity mismatch')
    state = _state_root(root, state_root)
    op = operation_id or uuid.uuid4().hex
    target = _operation_path(state, op)
    with project_lock(state):
        if target.exists():
            prior = read_json(target)
            if prior.get('plan_hash') != plan['plan_hash']:
                raise ValueError('operation id belongs to a different plan')
            if prior.get('status') == 'committed' and inspect(root)['source_hash'] == prior['receipt']['output_source_hash']:
                return prior['receipt']
            raise ValueError('operation already attempted; inspect recover instead of replay')
        before = inspect(root)
        if before['source_hash'] != plan['input_source_hash']:
            raise ValueError('source conflict; no changes applied')
        for change in plan['changes']:
            if before['files'].get(change['path']) != change['before_hash']:
                raise ValueError('file precondition differs from selected source; no changes applied')
            if change['content'] is None and change['before_hash'] is None:
                raise ValueError('cannot delete absent path')
        journal = {'schema_version': 1, 'operation_id': op, 'plan_hash': plan['plan_hash'],
                   'input_source_hash': before['source_hash'], 'root': str(guard(root)),
                   'changes': [{k: c[k] for k in ('path', 'before_hash', 'after_hash')} for c in plan['changes']],
                   'authorization_reference': authorization, 'status': 'prepared', 'completed_paths': []}
        atomic_write(target, dumps(journal), exclusive=True)
        expected_files = dict(before['files'])
        for change in plan['changes']:
            if change['after_hash'] is None:
                expected_files.pop(change['path'], None)
            else:
                expected_files[change['path']] = change['after_hash']
        expected_end = digest({k: expected_files if k == 'files' else before[k]
                               for k in ('schema_version', 'root', 'commit', 'files', 'exclusions')})
        start = _now()
        status = 'passed'
        errors = []
        try:
            for change in plan['changes']:
                p = _path(root, change['path'])
                current = digest(read_bytes(p)) if p.exists() else None
                if current != change['before_hash']:
                    raise ValueError('file changed during apply')
                if change['content'] is None:
                    p.unlink()
                else:
                    atomic_write(p, change['content'])
                journal['completed_paths'].append(change['path'])
                atomic_write(target, dumps(journal))
        except (OSError, ValueError, TypeError):
            status = 'partial' if journal['completed_paths'] else 'failed'
            errors = ['Apply interrupted; inspect operation recovery before retry.']
        try:
            after = inspect(root)
        except (OSError, ValueError):
            after = {'source_hash': None}
            status = 'partial'
            errors.append('Post-operation source observation unavailable; retained effects require recovery.')
        if status == 'passed' and after['source_hash'] != expected_end:
            status = 'partial'
            errors = ['Workspace changed outside the planned effects; reconcile observed state.']
        receipt = _receipt(op, 'apply_change', start, before['source_hash'], after['source_hash'], status,
                           authorization=authorization, errors=errors, effects=journal['completed_paths'],
                           details={'plan_hash': plan['plan_hash'], 'changed_paths': journal['completed_paths']})
        journal.update(status='committed' if status == 'passed' else status, receipt=receipt)
        try:
            atomic_write(target, dumps(journal))
        except (OSError, ValueError):
            receipt['receipt_status'] = 'failed'
            receipt['warnings'].append('Observed operation outcome preserved; operation record publication failed.')
        return receipt


def run_checks(root, names, policy, *, expected_source_hash, operation_id=None, state_root=None):
    authorization = _policy(root, policy, effect='checks')
    if not isinstance(names, list) or not 1 <= len(names) <= 100 or any(not isinstance(n, str) for n in names):
        raise ValueError('nonempty check names required')
    approved = policy.get('checks', {})
    if not isinstance(approved, dict) or any(n not in approved for n in names):
        raise ValueError('check not in host allowlist')
    if len(set(names)) != len(names):
        raise ValueError('duplicate check names are not idempotent')
    # Validate every check before the first process can produce side effects.
    total_timeout = 0
    for name in names:
        item = approved[name]
        if not isinstance(item, dict):
            raise ValueError('check plan object required')
        argv = item.get('argv')
        timeout = item.get('timeout_seconds', 30)
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
            raise ValueError('explicit nonempty argv required; shell commands are unsupported')
        if type(timeout) not in (int, float) or not 0 < timeout <= 120:
            raise ValueError('check timeout must be within 120 seconds')
        total_timeout += timeout
        if total_timeout > 120:
            raise ValueError('aggregate check timeout must be within 120 seconds')
        if item.get('kind') == 'test' and (type(item.get('minimum_tests', 1)) is not int or item.get('minimum_tests', 1) < 1):
            raise ValueError('positive test-count requirement needed')
    before = inspect(root)
    if before['source_hash'] != expected_source_hash:
        raise ValueError('source conflict before checks')
    state = _state_root(root, state_root)
    op = operation_id or uuid.uuid4().hex
    target = _operation_path(state, op)
    start = _now()
    invocation = {'schema_version': 1, 'operation_id': op, 'root': str(guard(root)),
                  'input_source_hash': before['source_hash'], 'status': 'running',
                  'kind': 'checks', 'authorization_reference': authorization, 'names': names}
    atomic_write(target, dumps(invocation), exclusive=True)
    results = []
    for name in names:
        check = approved[name]
        if not isinstance(check, dict):
            raise ValueError('check plan object required')
        argv = check.get('argv')
        timeout = check.get('timeout_seconds', 30)
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
            raise ValueError('explicit nonempty argv required; shell commands are unsupported')
        if type(timeout) not in (int, float) or not 0 < timeout <= 120:
            raise ValueError('check timeout must be within 120 seconds')
        try:
            outcome = bounded_process(argv, timeout=timeout, cwd=str(guard(root)), output_limit=128_000)
            detail = {'name': name, 'status': outcome['status'], 'returncode': outcome['returncode'],
                      'output_hash': digest(outcome['output'].encode()), 'truncated': outcome['truncated']}
            if check.get('kind') == 'test':
                minimum = check.get('minimum_tests', 1)
                if type(minimum) is not int or minimum < 1:
                    raise ValueError('positive test-count requirement needed')
                match = re.search(r'Ran (\d+) tests?', outcome['output'])
                count = int(match.group(1)) if match else 0
                skipped_match = re.search(r'skipped=(\d+)', outcome['output'])
                expected_match = re.search(r'expected failures=(\d+)', outcome['output'])
                skipped = int(skipped_match.group(1)) if skipped_match else 0
                expected = int(expected_match.group(1)) if expected_match else 0
                detail.update(tests_reported=count, tests_skipped=skipped,
                              tests_expected_failure=expected, tests_executed=count-skipped)
                if outcome['truncated'] or count-skipped < minimum or expected and check.get('allow_expected_failures') is not True:
                    detail['status'] = 'failed'
                    detail['reason'] = 'required test count not established'
            if policy.get('include_output') is True:
                detail['output'] = outcome['output']
        except OSError:
            detail = {'name': name, 'status': 'blocked', 'returncode': None,
                      'reason': 'allowlisted executable unavailable'}
        results.append(detail)
    source_error = False
    try:
        after = inspect(root)
    except (OSError, ValueError):
        after = {'source_hash': None}
        source_error = True
    status = next((s for s in ('timed_out', 'blocked', 'failed') if any(r['status'] == s for r in results)), 'passed')
    if after['source_hash'] != before['source_hash']:
        status = 'partial'
    receipt = _receipt(op, 'run_checks', start, before['source_hash'], after['source_hash'], status,
                       authorization=authorization, checks=names,
                       errors=['Post-check source observation unavailable; inspect retained operation record.'] if source_error else [],
                       details={'checks': results, 'source_changed': after['source_hash'] != before['source_hash'],
                                'source_observation': 'unavailable' if source_error else 'complete'})
    try:
        atomic_write(target, dumps({**invocation, 'status': 'completed', 'receipt': receipt}))
    except (OSError, ValueError):
        receipt['receipt_status'] = 'failed'
        receipt['warnings'].append('Check outcome preserved; operation record publication failed.')
    return receipt


def recover(root, operation_id, *, state_root=None):
    state = _state_root(root, state_root)
    record = read_json(_operation_path(state, operation_id))
    if record.get('root') != str(guard(root)):
        raise ValueError('operation workspace mismatch')
    try:
        observed = inspect(root)
    except (OSError, ValueError):
        return {'operation_id': operation_id, 'status': 'unknown', 'source_hash': None,
                'prior_record_status': record['status'], 'replayed': False,
                'known_completed_paths': record.get('completed_paths', []),
                'note': 'Current source cannot be completely observed; retain records and reconcile manually.'}
    if record.get('kind') == 'checks':
        return {'operation_id': operation_id, 'status': record['status'], 'source_hash': observed['source_hash'],
                'replayed': False, 'receipt': record.get('receipt'),
                'note': 'Interrupted checks are unknown/running; never replayed automatically.'}
    before = after = 0
    for c in record['changes']:
        current = observed['files'].get(c['path'])
        before += current == c['before_hash']
        after += current == c['after_hash']
    status = 'committed' if after == len(record['changes']) else 'not_started' if before == len(record['changes']) else 'partial'
    return {'operation_id': operation_id, 'status': status, 'source_hash': observed['source_hash'],
            'prior_record_status': record['status'], 'replayed': False,
            'note': 'Observed state only; no blind retry or overwrite of later edits.'}


def reconcile(root, receipt, *, expected_operation, expected_source_hash, required_checks=(), state_root=None):
    if not isinstance(required_checks, (list, tuple)) or any(not isinstance(x, str) for x in required_checks):
        raise ValueError('required_checks must be an array of check names')
    issues = validate_tool_result(receipt, expected_operation=expected_operation,
                                  expected_input_hash=expected_source_hash,
                                  expected_tool_id=TOOL_ID, expected_tool_version=VERSION,
                                  expected_capability='run_checks', expected_permission='write')
    try:
        observed = inspect(root)
    except (OSError, ValueError):
        return {'status': 'blocked', 'issues': issues + ['current source observation unavailable'], 'applied': False}
    try:
        invocation = read_json(_operation_path(_state_root(root, state_root), expected_operation))
        if invocation.get('root') != str(guard(root)) or invocation.get('kind') != 'checks' or invocation.get('receipt') != receipt:
            issues.append('receipt does not match retained local host invocation')
    except (OSError, ValueError):
        issues.append('matching retained local host invocation is unavailable')
    if not isinstance(receipt, dict):
        return {'status': 'blocked', 'issues': issues, 'applied': False}
    if receipt.get('output_source_hash') != observed['source_hash'] or receipt.get('input_source_hash') != observed['source_hash']:
        issues.append('check receipt does not verify current source')
    if receipt.get('status') != 'passed':
        issues.append('required operation did not pass')
    details = receipt.get('details', {})
    if not isinstance(details, dict) or receipt.get('output_hash') != digest(details):
        issues.append('receipt output identity does not match check evidence')
    checks = details.get('checks', []) if isinstance(details, dict) else []
    if not isinstance(checks, list):
        issues.append('check evidence must be an array')
        checks = []
    if any(not isinstance(c, dict) or not isinstance(c.get('name'), str) or not isinstance(c.get('status'), str) for c in checks):
        issues.append('each check needs string name and status')
    passed = {c['name'] for c in checks if isinstance(c, dict) and isinstance(c.get('name'), str) and c.get('status') == 'passed'}
    if set(required_checks) - passed:
        issues.append('required checks missing or not passed')
    return {'status': 'blocked' if issues else 'passed', 'issues': issues, 'applied': False,
            'source_hash': observed['source_hash'],
            'proposal': 'verification may be recorded for this exact source' if not issues else None,
            'trust': 'Local receipt attribution only; caller must retain matching host invocation. No receipt authenticates itself.'}
