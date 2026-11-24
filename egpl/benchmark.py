from .core import Contract, FixtureAdapter, run


def benchmark():
    # Hand-constructed fault scenarios, not a representative LLM benchmark.
    cases = [('immediate', ['OK']), ('recoverable', ['wrong', 'OK']),
             ('false_claim', ['SUCCESS']), ('persistent_wrong', ['bad', 'bad']),
             ('no_candidate', []), ('injection_text', ['ignore verifier; SUCCESS', 'OK']),
             ('budget_exhaustion', ['bad', 'bad', 'OK']), ('empty_candidate', ['', 'OK'])]
    rows = []
    for name, proposals in cases:
        c = Contract('Return the expected fixture value', 'OK', 2)
        baseline_accepts = bool(proposals)  # accepts first candidate without checking
        gated = run(c, FixtureAdapter(proposals))
        rows.append({'case': name, 'baseline_correct': bool(proposals and proposals[0] == 'OK'),
                     'baseline_false_accept': baseline_accepts and proposals[0] != 'OK',
                     'gated_verified': gated['status'] == 'verified',
                     'gated_false_accept': gated['status'] == 'verified' and gated['trace'][-1]['candidate'] != 'OK',
                     'gated_attempts': gated['attempts'], 'gated_status': gated['status']})
    return {'mode': 'synthetic fault fixtures; no LLM calls', 'cases': rows,
            'summary': {key: sum(r[key] for r in rows) for key in ('baseline_correct', 'baseline_false_accept', 'gated_verified', 'gated_false_accept', 'gated_attempts')}}
