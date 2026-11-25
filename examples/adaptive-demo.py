"""Synthetic demonstration; never a model benchmark."""
import json
from egpl.behavior import prepare
from egpl.adaptive import evaluate_transfer

def make_study(prefix):
    return {'version':1,'cases':[{'id':f'{prefix}{i}','dimension':'format',
            'expected':str(i),'verifier':'exact',
            'variants':{'plain':f'{prefix}: output {i} only.',
                        'structured':f'{prefix}: TASK output {i}; FORMAT integer only.'}}
            for i in range(5)]}

def observed(study,manifest,winning):
    expected={c['id']:c['expected'] for c in study['cases']}
    return {t['id']:expected[t['case']] if t['variant']==winning else 'wrong'
            for t in manifest['trials']}

dev,test=make_study('dev'),make_study('heldout')
dm,tm=prepare(dev,repeats=2,seed=7),prepare(test,repeats=2,seed=8)
# Deliberately reverse the effect on held-out fixtures to show failed transfer.
report=evaluate_transfer(dev,dm,observed(dev,dm,'structured'),test,tm,observed(test,tm,'plain'),
                         model='synthetic-A',mode='fixture',dimension='format',target_model='synthetic-B')
print(json.dumps(report,indent=2))
