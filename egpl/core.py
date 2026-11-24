"""Reference runtime: untrusted proposals, trusted local predicates, bounded retries."""
from dataclasses import dataclass, asdict
import hashlib
import json
from typing import Callable


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class Contract:
    objective: str
    expected: str
    max_attempts: int
    strategy: str = 'Try a candidate and revise it using verifier feedback.'

    def __post_init__(self):
        if not isinstance(self.objective, str) or not self.objective.strip():
            raise ValueError('objective must be nonempty text')
        if not isinstance(self.expected, str) or not self.expected:
            raise ValueError('expected must be nonempty text')
        if type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 100:
            raise ValueError('max_attempts must be an integer from 1 to 100')
        if not isinstance(self.strategy, str) or not self.strategy.strip():
            raise ValueError('strategy must be nonempty text')

    @property
    def invariant_id(self):
        return digest({k: v for k, v in asdict(self).items() if k != 'strategy'})

    @property
    def contract_id(self):
        return digest(asdict(self))


def compile_prompt(contract):
    # The trusted expected value is not provided to the proposer.
    return json.dumps({'objective': contract.objective, 'strategy': contract.strategy,
                       'response_format': {'candidate': 'string'},
                       'rule': 'Only the external verifier can authorize completion.'}, ensure_ascii=False)


class FixtureAdapter:
    """Deterministic, untrusted candidate source; not an LLM."""
    def __init__(self, candidates):
        if not isinstance(candidates, list) or any(not isinstance(x, str) for x in candidates):
            raise ValueError('fixtures must be a list of strings')
        self.candidates = tuple(candidates)

    def __call__(self, prompt, feedback, attempt):
        if attempt >= len(self.candidates):
            raise StopIteration
        return self.candidates[attempt]


def evidence(contract, candidate, attempt):
    # Exact equality is intentionally narrow. Never execute candidate text.
    return {'attempt': attempt, 'origin': 'trusted-local-exact-match-v1',
            'candidate': candidate, 'candidate_sha256': digest(candidate),
            'contract_id': contract.contract_id, 'passed': candidate == contract.expected}


def run(contract: Contract, propose: Callable, checkpoint=None, *, step_limit=None):
    if step_limit is not None and (type(step_limit) is not int or step_limit < 0):
        raise ValueError('invalid step limit')
    trace = []
    if checkpoint is not None:
        if checkpoint.get('contract_id') != contract.contract_id or not isinstance(checkpoint.get('trace'), list):
            raise ValueError('checkpoint contract mismatch or malformed trace')
        for i, entry in enumerate(checkpoint['trace']):
            if i >= contract.max_attempts or not isinstance(entry, dict) or not isinstance(entry.get('candidate'), str):
                raise ValueError('invalid checkpoint entry')
            if trace and trace[-1]['passed']:
                raise ValueError('trace continues after success')
            if entry != evidence(contract, entry['candidate'], i):
                raise ValueError('checkpoint evidence does not reproduce')
            trace.append(entry)
    def result(status):
        return {'contract_id': contract.contract_id, 'status': status,
                'attempts': len(trace), 'trace': trace}
    if trace and trace[-1]['passed']:
        return result('verified')
    remaining = contract.max_attempts - len(trace)
    limit = remaining if step_limit is None else min(remaining, step_limit)
    for _ in range(limit):
        try:
            candidate = propose(compile_prompt(contract), 'Previous candidate failed.' if trace else '', len(trace))
        except StopIteration:
            return result('blocked')
        if not isinstance(candidate, str):
            return result('blocked')
        trace.append(evidence(contract, candidate, len(trace)))
        if trace[-1]['passed']:
            return result('verified')
    return result('exhausted' if len(trace) == contract.max_attempts else 'paused')


def optimize(base, candidates, dev_cases):
    """Select a strategy only; evaluate every candidate on identical fixtures.

    Cases map strategy -> candidate sequence. No learned model or test-set tuning.
    """
    if not dev_cases:
        raise ValueError('development cases required')
    pool = [base, *candidates]
    if any(c.invariant_id != base.invariant_id for c in pool):
        raise ValueError('optimizer cannot change invariants')
    scores = []
    for c in pool:
        outcomes = [run(c, FixtureAdapter(case.get(c.strategy, []))) for case in dev_cases]
        scores.append((sum(r['status'] == 'verified' for r in outcomes), -sum(r['attempts'] for r in outcomes)))
    winner = max(range(len(pool)), key=lambda i: scores[i])
    return {'contract': asdict(pool[winner]), 'scores': scores, 'selected_index': winner, 'mode': 'synthetic-dev-fixtures'}
