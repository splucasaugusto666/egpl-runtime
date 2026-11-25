"""Reproducible black-box experiments, not claims about internal cognition."""
import random
import re
from .core import digest
from .verifiers import bounded_text, validate, verify

MAX_TRIALS = 400
MODES = ('manual', 'fixture', 'caller-transport', 'ollama')


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}', value):
        raise ValueError('invalid identifier')
    return value


def _study(study):
    if not isinstance(study, dict) or set(study) != {'version', 'cases'} or type(study['version']) is not int or study['version'] != 1:
        raise ValueError('unsupported study schema')
    cases = study['cases']
    if not isinstance(cases, list) or not 1 <= len(cases) <= 100:
        raise ValueError('invalid case count')
    ids = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {'id','dimension','expected','verifier','variants'}:
            raise ValueError('invalid case fields')
        name = _identifier(case['id'])
        if name in ids:
            raise ValueError('duplicate case')
        ids.add(name)
        _identifier(case['dimension'])
        bounded_text(case['expected'])
        validate(case['verifier'], case['expected'])
        variants = case['variants']
        if not isinstance(variants, dict) or 'plain' not in variants or not 2 <= len(variants) <= 8:
            raise ValueError('each case requires plain and at least one intervention')
        for label, prompt in variants.items():
            _identifier(label)
            if not bounded_text(prompt).strip():
                raise ValueError('empty prompt')
    return cases


def study_id(study):
    _study(study)
    return digest(study)


def prepare(study, *, repeats=1, seed=0):
    cases = _study(study)
    if type(repeats) is not int or not 1 <= repeats <= 20:
        raise ValueError('invalid repeats')
    if type(seed) is not int or not 0 <= seed <= 2**32-1:
        raise ValueError('invalid seed')
    if sum(len(c['variants']) for c in cases)*repeats > MAX_TRIALS:
        raise ValueError('study exceeds trial budget')
    trials = []
    for case in sorted(cases, key=lambda c:c['id']):
        for variant, prompt in sorted(case['variants'].items()):
            for repeat in range(repeats):
                trial_id = digest([case['id'], variant, repeat])
                trials.append({'id':trial_id,'case':case['id'],'variant':variant,
                               'repeat':repeat,'prompt':prompt})
    random.Random(seed).shuffle(trials)
    return {'version':1,'study_id':study_id(study),'repeats':repeats,'seed':seed,'trials':trials}


def score(study, manifest, outputs, *, model, mode):
    """Score final text only. Missing trials never become successful or observed."""
    if not isinstance(manifest, dict):
        raise ValueError('invalid manifest')
    try:
        expected_manifest = prepare(study, repeats=manifest['repeats'], seed=manifest['seed'])
    except KeyError as exc:
        raise ValueError('invalid manifest') from exc
    if digest(manifest) != digest(expected_manifest):
        raise ValueError('manifest does not reproduce')
    if not isinstance(outputs, dict) or not set(outputs) <= {t['id'] for t in manifest['trials']}:
        raise ValueError('unknown trial or invalid responses')
    if mode not in MODES or not bounded_text(model).strip():
        raise ValueError('invalid model or provenance mode')
    cases = {c['id']:c for c in _study(study)}
    counts = {'planned':len(manifest['trials']), 'observed':0,'passed':0,'missing':0}
    rows = []
    groups = {}
    observed = {}
    for trial in manifest['trials']:
        case = cases[trial['case']]
        tid = trial['id']
        row = {k:trial[k] for k in ('id','case','variant','repeat')}
        row['dimension'] = case['dimension']
        group = groups.setdefault((case['dimension'],trial['variant']), {'planned':0,'observed':0,'passed':0,'missing':0})
        group['planned'] += 1
        if tid not in outputs:
            row.update(status='missing',passed=None,response_sha256=None)
            counts['missing'] += 1
            group['missing'] += 1
        else:
            response = outputs[tid]
            bounded_text(response)
            passed = verify(case['verifier'],case['expected'],response)
            row.update(status='observed',passed=passed,response_sha256=digest(response))
            counts['observed'] += 1
            counts['passed'] += int(passed)
            group['observed'] += 1
            group['passed'] += int(passed)
            observed[(trial['case'],trial['variant'],trial['repeat'])] = passed
        rows.append(row)
    paired = {}
    for trial in manifest['trials']:
        if trial['variant'] == 'plain':
            continue
        out = paired.setdefault(trial['variant'], {'both_observed':0,'both_pass':0,'plain_only':0,'variant_only':0,'both_fail':0})
        a = (trial['case'],'plain',trial['repeat'])
        b = (trial['case'],trial['variant'],trial['repeat'])
        if a not in observed or b not in observed:
            continue
        x,y = observed[a],observed[b]
        out['both_observed'] += 1
        out['both_pass' if x and y else 'plain_only' if x else 'variant_only' if y else 'both_fail'] += 1
    return {'version':1,'study_id':manifest['study_id'],'manifest_id':digest(manifest),
            'model':model,'mode':mode,'counts':counts,'paired':paired,
            'dimensions':[dict(dimension=d,variant=v,**g) for (d,v),g in sorted(groups.items())],
            'trials':rows}


def collect(manifest, adapter):
    """Explicit caller-owned execution. Never retries a failed trial or guesses output."""
    trials = manifest.get('trials') if isinstance(manifest,dict) else None
    if not isinstance(trials,list) or not 1 <= len(trials) <= MAX_TRIALS:
        raise ValueError('invalid trial manifest')
    outputs = {}
    seen = set()
    for index,trial in enumerate(trials):
        if not isinstance(trial,dict) or not isinstance(trial.get('id'),str) or trial['id'] in seen:
            raise ValueError('duplicate or invalid trial')
        seen.add(trial['id'])
        bounded_text(trial['prompt'])
    for index,trial in enumerate(trials):
        try:
            response = adapter(trial['prompt'],'',index)
            bounded_text(response)
        except (StopIteration,ValueError):
            continue
        outputs[trial['id']] = response
    return outputs
