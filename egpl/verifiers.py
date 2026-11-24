"""Pure deterministic predicates. Candidate text is data, never code."""
import hashlib
import json
import re

KINDS = ('exact', 'json_equal', 'integer_range', 'sha256')
MAX_BYTES = 65536


def bounded_text(text):
    if not isinstance(text, str):
        raise ValueError('expected text')
    if len(text) > MAX_BYTES:
        raise ValueError('text too large')
    try:
        raw = text.encode('utf-8')
    except UnicodeError as exc:
        raise ValueError('invalid UTF-8 text') from exc
    if len(raw) > MAX_BYTES:
        raise ValueError('text too large')
    return raw


def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate JSON key')
        obj[key] = value
    return obj


def bad_constant(value):
    raise ValueError('nonfinite JSON number')


def canonical_json(text):
    bounded_text(text)
    try:
        obj = json.loads(text, object_pairs_hook=unique_pairs, parse_constant=bad_constant)
        # Canonical representation distinguishes true from 1, and 1 from 1.0.
        return json.dumps(obj, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':'))
    except (ValueError, RecursionError, OverflowError) as exc:
        raise ValueError('invalid JSON') from exc


def range_bounds(expected):
    bounded_text(expected)
    try:
        obj = json.loads(expected, object_pairs_hook=unique_pairs, parse_constant=bad_constant)
        if not isinstance(obj, dict) or set(obj) != {'min', 'max'}:
            raise ValueError('range requires min and max')
        lo, hi = obj['min'], obj['max']
        if type(lo) is not int or type(hi) is not int or not -10**18 <= lo <= hi <= 10**18:
            raise ValueError('invalid integer bounds')
        return lo, hi
    except (ValueError, RecursionError) as exc:
        raise ValueError('invalid integer range') from exc


def validate(kind, expected):
    if kind not in KINDS:
        raise ValueError('unsupported verifier')
    bounded_text(expected)
    if kind == 'json_equal':
        canonical_json(expected)
    elif kind == 'integer_range':
        range_bounds(expected)
    elif kind == 'sha256' and not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise ValueError('expected lowercase SHA-256 hex digest')


def verify(kind, expected, candidate):
    """Return a predicate result; malformed or oversized candidates fail closed."""
    try:
        raw = bounded_text(candidate)
        if kind == 'exact':
            return candidate == expected
        if kind == 'json_equal':
            return canonical_json(candidate) == canonical_json(expected)
        if kind == 'integer_range':
            if not re.fullmatch(r'-?(?:0|[1-9][0-9]{0,18})', candidate):
                return False
            lo, hi = range_bounds(expected)
            return lo <= int(candidate) <= hi
        if kind == 'sha256':
            return hashlib.sha256(raw).hexdigest() == expected
    except (ValueError, RecursionError, OverflowError):
        return False
    raise ValueError('unsupported verifier')
