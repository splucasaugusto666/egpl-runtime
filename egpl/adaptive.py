"""Conservative exploratory adaptation using replayed, paired observations."""
from .behavior import score, _study
from .core import digest

MIN_CASES = 5
MIN_DELTA = 0.10


def _compare(study, manifest, outputs, *, model, mode, dimension, variant):
    profile = score(study, manifest, outputs, model=model, mode=mode)
    cases = [c for c in _study(study) if c['dimension'] == dimension]
    rows = {(r['case'],r['variant'],r['repeat']):r for r in profile['trials']}
    trials = {(r['case'],r['variant'],r['repeat']):r for r in manifest['trials']}
    pairs = []
    base_chars = variant_chars = 0
    for c in cases:
        if variant not in c['variants']:
            continue
        for i in range(manifest['repeats']):
            a,b = (c['id'],'plain',i),(c['id'],variant,i)
            if rows[a]['status'] == rows[b]['status'] == 'observed':
                pairs.append((c['id'],rows[a]['passed'],rows[b]['passed']))
                base_chars += len(trials[a]['prompt'])
                variant_chars += len(trials[b]['prompt'])
    n = len(pairs)
    plain_pass = sum(x[1] for x in pairs)
    variant_pass = sum(x[2] for x in pairs)
    return {'matched_cases':len({x[0] for x in pairs}), 'paired_trials':n,
            'planned_pairs':len(cases)*manifest['repeats'],
            'plain_pass':plain_pass, 'variant_pass':variant_pass,
            'plain_only':sum(x[1] and not x[2] for x in pairs),
            'variant_only':sum(x[2] and not x[1] for x in pairs),
            'delta':(variant_pass-plain_pass)/n if n else None,
            'plain_input_chars':base_chars, 'variant_input_chars':variant_chars}


def select_strategy(study, manifest, outputs, *, model, mode, dimension):
    """Choose only from complete balanced development trials; never claims efficacy."""
    profile = score(study,manifest,outputs,model=model,mode=mode)
    cases = [c for c in _study(study) if c['dimension']==dimension]
    if not cases:
        raise ValueError('unknown study dimension')
    variants = set().union(*(set(c['variants']) for c in cases))
    balanced = all(set(c['variants'])==variants for c in cases)
    comparisons = {v:_compare(study,manifest,outputs,model=model,mode=mode,dimension=dimension,variant=v)
                   for v in sorted(variants-{'plain'})}
    eligible = []
    for v,r in comparisons.items():
        if balanced and r['matched_cases']>=MIN_CASES and r['paired_trials']==r['planned_pairs'] and r['delta'] is not None and r['delta']>=MIN_DELTA:
            eligible.append(v)
    selected = min(eligible,key=lambda v:(-comparisons[v]['delta'],comparisons[v]['variant_input_chars'],v)) if eligible else 'plain'
    return {'version':1,'status':'exploratory','study_id':profile['study_id'],
            'manifest_id':profile['manifest_id'],'observations_id':digest(outputs),
            'model':model,'mode':mode,'dimension':dimension,'selected':selected,
            'reason':'paired development gain' if eligible else 'insufficient or no positive matched evidence',
            'balanced':balanced,'min_cases':MIN_CASES,'min_delta':MIN_DELTA,'comparisons':comparisons}


def evaluate_transfer(dev, dev_manifest, dev_outputs, test, test_manifest, test_outputs,
                      *, model, mode, dimension, target_model=None, target_mode=None):
    """Freeze a development selection before inspecting disjoint target observations."""
    dc,tc = _study(dev),_study(test)
    if {c['id'] for c in dc}&{c['id'] for c in tc}:
        raise ValueError('development and held-out case IDs overlap')
    if {p for c in dc for p in c['variants'].values()}&{p for c in tc for p in c['variants'].values()}:
        raise ValueError('development and held-out prompts overlap')
    if not any(c['dimension']==dimension for c in tc):
        raise ValueError('held-out dimension missing')
    selection = select_strategy(dev,dev_manifest,dev_outputs,model=model,mode=mode,dimension=dimension)
    target_model = model if target_model is None else target_model
    target_mode = mode if target_mode is None else target_mode
    target = score(test,test_manifest,test_outputs,model=target_model,mode=target_mode)
    heldout = _compare(test,test_manifest,test_outputs,model=target_model,mode=target_mode,dimension=dimension,variant=selection['selected'])
    complete = heldout['paired_trials']==heldout['planned_pairs'] and heldout['matched_cases']>=MIN_CASES
    return {'version':1,'status':'heldout-descriptive' if complete else 'insufficient-heldout-evidence',
            'selected':selection['selected'],'source_model':model,'target_model':target_model,
            'source_mode':mode,'target_mode':target_mode,'selection':selection,
            'heldout_study_id':target['study_id'],'heldout_manifest_id':target['manifest_id'],
            'heldout_observations_id':digest(test_outputs),'heldout':heldout}
