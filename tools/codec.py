"""Pure canonical JSON encoding and strict parsing; no filesystem effects."""
import hashlib
import json
import math


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def digest(value):
    raw = value if isinstance(value, bytes) else dumps(value).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON mapping key')
        result[key] = value
    return result


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError('nonfinite JSON number')
    return value


def strict_json_loads(text):
    """Reject duplicate keys and nonfinite values rather than silently normalizing."""
    def reject_constant(_):
        raise ValueError('nonfinite JSON number')
    return json.loads(text, object_pairs_hook=_unique_object,
                      parse_float=_finite_float, parse_constant=reject_constant)
