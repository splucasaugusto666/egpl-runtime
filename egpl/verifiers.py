"""Pure deterministic predicates. Candidate text is data, never code."""
import hashlib
import json
import re

PRIMITIVES = ('exact', 'json_equal', 'integer_range', 'sha256')
KINDS = PRIMITIVES + ('all',)
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
    if kind == 'all':
        parse_rules(expected)
    elif kind == 'json_equal':
        canonical_json(expected)
    elif kind == 'integer_range':
        range_bounds(expected)
    elif kind == 'sha256' and not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise ValueError('expected lowercase SHA-256 hex digest')


def verify(kind, expected, candidate):
    """Return a predicate result; malformed or oversized candidates fail closed."""
    try:
        raw = bounded_text(candidate)
        if kind == 'all':
            return all(check['passed'] for check in evaluate_all(expected, candidate))
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


def parse_rules(expected):
    """Validate a flat, nonempty conjunction of bounded primitive predicates."""
    rules = json.loads(canonical_json(expected))
    if not isinstance(rules, list) or not 1 <= len(rules) <= 32:
        raise ValueError('all requires 1–32 rules')
    ids = set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {'id', 'path', 'verifier', 'expected'}:
            raise ValueError('rule requires id, path, verifier and expected')
        name, path, kind, value = (rule[k] for k in ('id', 'path', 'verifier', 'expected'))
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}', name) or name in ids:
            raise ValueError('invalid or duplicate rule id')
        ids.add(name)
        if not isinstance(path, str) or len(path) > 512 or (path and not path.startswith('/')) or re.search(r'~(?![01])', path):
            raise ValueError('invalid JSON pointer')
        if kind not in PRIMITIVES:
            raise ValueError('only primitive verifiers allowed in all')
        validate(kind, value)
    return rules


def pointer_value(obj, path):
    """RFC 6901 JSON pointer; no URI fragments, append operations or code."""
    if path == '':
        return obj
    for part in path[1:].split('/'):
        token = part.replace('~1', '/').replace('~0', '~')
        if isinstance(obj, dict):
            obj = obj[token]
        elif isinstance(obj, list):
            # Candidate size bounds the actual array length; reject huge indices.
            if not re.fullmatch(r'0|[1-9][0-9]{0,8}', token):
                raise KeyError('invalid array index')
            obj = obj[int(token)]
        else:
            raise KeyError('cannot traverse scalar')
    return obj


def evaluate_all(expected, candidate):
    """Return per-rule booleans, never expected values or extracted contents."""
    rules = parse_rules(expected)
    try:
        obj = json.loads(canonical_json(candidate))
    except (ValueError, RecursionError, OverflowError):
        return [{'id': r['id'], 'passed': False} for r in rules]
    results = []
    for rule in rules:
        passed = False
        kind = rule['verifier']
        try:
            value = pointer_value(obj, rule['path'])
            if kind in ('exact', 'sha256'):
                if not isinstance(value, str):
                    raise ValueError('string required')
                text = value
            elif kind == 'integer_range':
                if type(value) is not int:
                    raise ValueError('integer required')
                text = str(value)
            else:
                text = json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':'))
            passed = verify(kind, rule['expected'], text)
        except (LookupError, ValueError, RecursionError, OverflowError):
            pass
        results.append({'id': rule['id'], 'passed': passed})
    return results
