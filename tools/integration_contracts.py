"""Validation for capability manifests and evidence-bearing tool receipts.

This module validates data contracts only. It does not discover, authorize, invoke,
or sandbox external tools. Host permissions remain authoritative.
"""
from __future__ import annotations
import datetime
import re

STATUSES = {"passed", "failed", "blocked", "timed_out", "skipped", "partial", "unknown"}
PERMISSIONS = {"read", "write", "deploy", "production_data"}
_HASH = re.compile(r"^[a-f0-9]{64}$")
_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{1,127}$")


def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def validate_capability_manifest(value):
    issues = []
    if not isinstance(value, dict):
        return ["capability manifest must be an object"]
    if value.get("schema_version") != 1:
        issues.append("schema_version must be 1")
    for field in ("tool_id", "tool_version"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            issues.append(f"{field} must be a nonempty string")
    if isinstance(value.get("tool_id"), str) and not _ID.fullmatch(value["tool_id"]):
        issues.append("tool_id must be a stable lowercase identifier")
    capabilities = value.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        return issues + ["capabilities must be a nonempty array"]
    seen = set()
    for index, capability in enumerate(capabilities):
        loc = f"capabilities/{index}"
        if not isinstance(capability, dict):
            issues.append(f"{loc} must be an object")
            continue
        operation = capability.get("operation_id")
        if not isinstance(operation, str) or not _ID.fullmatch(operation):
            issues.append(f"{loc}/operation_id must be a stable lowercase identifier")
        elif operation in seen:
            issues.append(f"duplicate capability operation_id: {operation}")
        else:
            seen.add(operation)
        if not isinstance(capability.get("description"), str) or not capability["description"].strip():
            issues.append(f"{loc}/description must be nonempty")
        if capability.get("permission_class") not in PERMISSIONS:
            issues.append(f"{loc}/permission_class must be one of {sorted(PERMISSIONS)}")
        for field in ("input_schema", "output_schema"):
            if not isinstance(capability.get(field), dict):
                issues.append(f"{loc}/{field} must be a JSON Schema object")
        if type(capability.get("idempotent")) is not bool:
            issues.append(f"{loc}/idempotent must be boolean")
        timeout = capability.get("timeout_seconds")
        if type(timeout) not in (int, float) or not 0 < timeout <= 3600:
            issues.append(f"{loc}/timeout_seconds must be greater than 0 and at most 3600")
    return issues


def validate_tool_result(value, expected_operation=None, expected_input_hash=None):
    issues = []
    if not isinstance(value, dict):
        return ["tool result must be an object"]
    required = ("operation_id", "tool_id", "tool_version", "capability", "permission_class",
                "input_source_hash", "input_schema_version", "started_at", "completed_at",
                "status", "checks_run", "checks_not_run", "warnings", "errors", "limitations")
    for field in required:
        if field not in value:
            issues.append(f"missing required field: {field}")
    for field in ("operation_id", "tool_id", "tool_version", "capability"):
        if field in value and (not isinstance(value[field], str) or not value[field].strip()):
            issues.append(f"{field} must be a nonempty string")
    if value.get("permission_class") not in PERMISSIONS:
        issues.append("permission_class is invalid")
    if value.get("status") not in STATUSES:
        issues.append("status is invalid")
    if type(value.get("input_schema_version")) is not int or value.get("input_schema_version", 0) < 1:
        issues.append("input_schema_version must be a positive integer")
    if not isinstance(value.get("input_source_hash"), str) or not _HASH.fullmatch(value.get("input_source_hash", "")):
        issues.append("input_source_hash must be a lowercase SHA-256 hex digest")
    if expected_input_hash is not None and value.get("input_source_hash") != expected_input_hash:
        issues.append("input_source_hash does not match expected source identity")
    if expected_operation is not None and value.get("operation_id") != expected_operation:
        issues.append("operation_id does not match expected operation")
    started, completed = _timestamp(value.get("started_at")), _timestamp(value.get("completed_at"))
    if started is None:
        issues.append("started_at must be an ISO-8601 timestamp with timezone")
    if completed is None:
        issues.append("completed_at must be an ISO-8601 timestamp with timezone")
    if started is not None and completed is not None and completed < started:
        issues.append("completed_at must not precede started_at")
    if value.get("status") == "passed":
        if not isinstance(value.get("output_hash"), str) or not _HASH.fullmatch(value.get("output_hash", "")):
            issues.append("passed tool result requires output_hash as SHA-256 identity")
    elif value.get("output_hash") is not None and (not isinstance(value.get("output_hash"), str) or not _HASH.fullmatch(value["output_hash"])):
        issues.append("output_hash, when present, must be a lowercase SHA-256 hex digest")
    for field in ("checks_run", "checks_not_run", "warnings", "errors", "limitations"):
        items = value.get(field)
        if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
            issues.append(f"{field} must be an array of strings")
    if value.get("status") == "passed" and value.get("permission_class") in {"write", "deploy", "production_data"}:
        if not isinstance(value.get("authorization_reference"), str) or not value["authorization_reference"].strip():
            issues.append("authorization_reference is required for a passed consequential operation")
    return issues


def validate_verification_receipt(value, expected_source_hash=None):
    return validate_tool_result(value, expected_input_hash=expected_source_hash)
