"""Validate versioned capability/receipt data; records never grant tool authority."""
from __future__ import annotations
import datetime
import json
import math
import re
from pathlib import Path

STATUSES = {'passed', 'failed', 'blocked', 'timed_out', 'skipped', 'partial', 'unknown', 'tool_error', 'not_run_due_to_budget'}
PERMISSIONS = {'read', 'write', 'deploy', 'production_data'}
_HASH = re.compile(r'^[a-f0-9]{64}$')
_ID = re.compile(r'^[a-z0-9][a-z0-9._-]{1,127}$')


def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def _member(value, choices):
    return isinstance(value, str) and value in choices


def _schema_issues(value, filename):
    """Optional full schema parity; core checks below remain dependency-free."""
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        return []
    schema = json.loads((Path(__file__).resolve().parents[1] / 'schemas' / filename).read_text())
    return ['schema/' + '/'.join(map(str, e.path)) + ': ' + e.validator + ' constraint failed'
            for e in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value)]


def _metaschema(schema):
    if not isinstance(schema, dict):
        return False
    try:
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(schema)
    except ImportError:
        # A conservative structural subset when the optional engine is absent.
        if 'type' in schema and not isinstance(schema['type'], (str, list)):
            return False
    except Exception:
        return False
    return True


def validate_capability_manifest(value):
    if not isinstance(value, dict):
        return ['capability manifest must be an object']
    issues = _schema_issues(value, 'tool-capability-v1.schema.json')
    if type(value.get('schema_version')) is not int or value['schema_version'] != 1:
        issues.append('schema_version must be 1')
    for field in ('tool_id', 'tool_version'):
        if not isinstance(value.get(field), str) or not value[field].strip():
            issues.append(field + ' must be a nonempty string')
    if isinstance(value.get('tool_id'), str) and not _ID.fullmatch(value['tool_id']):
        issues.append('tool_id must be a stable lowercase identifier')
    capabilities = value.get('capabilities')
    if not isinstance(capabilities, list) or not 1 <= len(capabilities) <= 100:
        return issues + ['capabilities must be a nonempty bounded array']
    seen = set()
    for i, c in enumerate(capabilities):
        loc = f'capabilities/{i}'
        if not isinstance(c, dict):
            issues.append(loc + ' must be an object')
            continue
        operation = c.get('operation_id')
        if not isinstance(operation, str) or not _ID.fullmatch(operation):
            issues.append(loc + '/operation_id must be a stable lowercase identifier')
        elif operation in seen:
            issues.append('duplicate capability operation_id: ' + operation)
        else:
            seen.add(operation)
        if not isinstance(c.get('description'), str) or not c['description'].strip():
            issues.append(loc + '/description must be nonempty')
        if not _member(c.get('permission_class'), PERMISSIONS):
            issues.append(loc + '/permission_class is invalid')
        for field in ('input_schema', 'output_schema'):
            if not _metaschema(c.get(field)):
                issues.append(loc + '/' + field + ' must be a valid JSON Schema object')
        if type(c.get('idempotent')) is not bool:
            issues.append(loc + '/idempotent must be boolean')
        timeout = c.get('timeout_seconds')
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 3600:
            issues.append(loc + '/timeout_seconds must be greater than 0 and at most 3600')
    return issues


def validate_tool_result(value, expected_operation=None, expected_input_hash=None, *,
                         expected_tool_id=None, expected_tool_version=None,
                         expected_capability=None, expected_permission=None):
    if not isinstance(value, dict):
        return ['tool result must be an object']
    issues = _schema_issues(value, 'verification-receipt-v1.schema.json')
    required = ('operation_id', 'tool_id', 'tool_version', 'capability', 'permission_class',
                'input_source_hash', 'input_schema_version', 'started_at', 'completed_at',
                'status', 'checks_run', 'checks_not_run', 'warnings', 'errors', 'limitations')
    issues += ['missing required field: ' + f for f in required if f not in value]
    for field in ('operation_id', 'tool_id', 'tool_version', 'capability'):
        if not isinstance(value.get(field), str) or not value[field].strip():
            issues.append(field + ' must be a nonempty string')
    if not _member(value.get('permission_class'), PERMISSIONS):
        issues.append('permission_class is invalid')
    if not _member(value.get('status'), STATUSES):
        issues.append('status is invalid')
    if type(value.get('input_schema_version')) is not int or value.get('input_schema_version', 0) < 1:
        issues.append('input_schema_version must be a positive integer')
    if not isinstance(value.get('input_source_hash'), str) or not _HASH.fullmatch(value['input_source_hash']):
        issues.append('input_source_hash must be a lowercase SHA-256 hex digest')
    for field, expected in (('operation_id', expected_operation), ('input_source_hash', expected_input_hash),
                            ('tool_id', expected_tool_id), ('tool_version', expected_tool_version),
                            ('capability', expected_capability), ('permission_class', expected_permission)):
        if expected is not None and value.get(field) != expected:
            issues.append(field + ' does not match expected request identity')
    started, completed = _timestamp(value.get('started_at')), _timestamp(value.get('completed_at'))
    if started is None:
        issues.append('started_at must be an ISO-8601 timestamp with timezone')
    if completed is None:
        issues.append('completed_at must be an ISO-8601 timestamp with timezone')
    if started is not None and completed is not None and completed < started:
        issues.append('completed_at must not precede started_at')
    if value.get('status') == 'passed' or value.get('output_hash') is not None:
        if not isinstance(value.get('output_hash'), str) or not _HASH.fullmatch(value['output_hash']):
            issues.append('passed tool result requires output_hash as SHA-256 identity')
    for field in ('checks_run', 'checks_not_run', 'warnings', 'errors', 'limitations', 'artifact_refs', 'observed_effects'):
        if field not in required and field not in value:
            continue
        items = value.get(field)
        if not isinstance(items, list) or len(items) > 10000 or any(not isinstance(x, str) for x in items):
            issues.append(field + ' must be a bounded array of strings')
    if _member(value.get('permission_class'), {'write', 'deploy', 'production_data'}):
        if not isinstance(value.get('authorization_reference'), str) or not value['authorization_reference'].strip():
            issues.append('authorization_reference is required for an attempted consequential operation')
    if value.get('status') == 'passed' and (value.get('errors') or value.get('checks_not_run')):
        issues.append('passed result cannot contain errors or unrun required checks')
    return issues


def validate_verification_receipt(value, expected_source_hash=None):
    return validate_tool_result(value, expected_input_hash=expected_source_hash)
