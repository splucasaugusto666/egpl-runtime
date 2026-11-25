import unittest
from egpl.behavior import prepare, score, study_id
from egpl.protocols import request_body, response_text, WireAdapter

def study():
    return {'version':1,'cases':[
        {'id':'arith','dimension':'format','expected':'4','verifier':'exact','variants':{'plain':'Return only 2+2.','structured':'Task: 2+2. Output: integer only.'}},
        {'id':'unknown','dimension':'uncertainty','expected':'UNKNOWN','verifier':'exact','variants':{'plain':'No evidence. If unknown return UNKNOWN.','structured':'Evidence: absent. Output UNKNOWN if unknown.'}}
    ]}

class BehaviorTests(unittest.TestCase):
    def test_prepare_blinds_and_repeats(self):
        manifest=prepare(study(), repeats=2, seed=7)
        self.assertEqual(len(manifest['trials']),8)
        self.assertEqual(manifest,prepare(study(),repeats=2,seed=7))
        self.assertEqual(manifest['study_id'],study_id(study()))
        for t in manifest['trials']:
            self.assertEqual(set(t),{'id','case','variant','repeat','prompt'})
        self.assertNotIn('expected',manifest['trials'][0])
    def test_score_matched_and_missing(self):
        m=prepare(study(),repeats=1,seed=0)
        outputs={}
        for t in m['trials']:
            if t['case']=='arith':
                outputs[t['id']]='4' if t['variant']=='plain' else '5'
            elif t['variant']=='plain':
                outputs[t['id']]='UNKNOWN'
        p=score(study(),m,outputs,model='example',mode='manual')
        self.assertEqual(p['counts'],{'planned':4,'observed':3,'passed':2,'missing':1})
        self.assertEqual(p['paired']['structured'],{'both_observed':1,'both_pass':0,'plain_only':1,'variant_only':0,'both_fail':0})
        self.assertNotIn('response',p['trials'][0])
    def test_manifest_tamper_and_extra_response(self):
        m=prepare(study())
        with self.assertRaises(ValueError): score(study(),m,{'unknown':'4'},model='m',mode='manual')
        m['trials'][0]['prompt']='changed'
        with self.assertRaises(ValueError): score(study(),m,{},model='m',mode='manual')
    def test_invalid_study(self):
        for mutate in (lambda s:s['cases'].append(s['cases'][0]),lambda s:s['cases'][0]['variants'].pop('plain'),lambda s:s['cases'][0].update(verifier='bad')):
            s=study();mutate(s)
            with self.assertRaises(ValueError): prepare(s)
    def test_mode_and_limits(self):
        for r in (0,True,21):
            with self.assertRaises(ValueError): prepare(study(),repeats=r)
        m=prepare(study())
        with self.assertRaises(ValueError): score(study(),m,{},model='m',mode='invented')
        with self.assertRaises(ValueError): score(study(),m,{m['trials'][0]['id']:123},model='m',mode='manual')

class WireTests(unittest.TestCase):
    def test_payload_formats(self):
        self.assertEqual(request_body('openai-chat','m','p',32)['max_completion_tokens'],32)
        self.assertEqual(request_body('openai-compatible','m','p',32)['max_tokens'],32)
        self.assertEqual(request_body('anthropic','m','p',32)['messages'][0]['content'],'p')
        self.assertEqual(request_body('gemini','m','p',32)['generationConfig']['maxOutputTokens'],32)
        self.assertEqual(request_body('ollama','m','p',32)['options']['num_predict'],32)
    def test_final_text_only(self):
        self.assertEqual(response_text('openai-chat',{'choices':[{'message':{'content':'ok','reasoning_content':'hidden'},'finish_reason':'stop'}]}),'ok')
        self.assertEqual(response_text('anthropic',{'content':[{'type':'thinking','thinking':'secret'},{'type':'text','text':'ok'}],'stop_reason':'end_turn'}),'ok')
        self.assertEqual(response_text('gemini',{'candidates':[{'content':{'parts':[{'thought':True,'text':'secret'},{'text':'ok'}]},'finishReason':'STOP'}]}),'ok')
        self.assertEqual(response_text('ollama',{'response':'ok','done':True,'thinking':'secret'}),'ok')
    def test_fail_closed(self):
        for proto, payload in [('openai-chat',{'choices':[{'message':{'content':'ok'},'finish_reason':'length'}]}),('anthropic',{'content':[{'type':'text','text':'ok'}],'stop_reason':'tool_use'}),('gemini',{'candidates':[{'finishReason':'SAFETY','content':{'parts':[{'text':'ok'}]}}]}),('ollama',{'response':'ok','done':False})]:
            with self.assertRaises(ValueError): response_text(proto,payload)
    def test_injected_transport(self):
        calls=[]
        def transport(protocol,model,body):
            calls.append((protocol,model,body))
            return {'choices':[{'message':{'content':'OK'},'finish_reason':'stop'}]}
        a=WireAdapter('openai-compatible','model',transport,max_tokens=16)
        self.assertEqual(a('objective','feedback',0),'OK')
        self.assertEqual(calls[0][2]['messages'][0]['content'],'objective\nfeedback')
        self.assertEqual(calls[0][2]['max_tokens'],16)
    def test_invalid_protocol_and_budget(self):
        for p,n in [('bad',32),('ollama',True),('gemini',0)]:
            with self.assertRaises(ValueError): request_body(p,'m','p',n)

if __name__=='__main__': unittest.main()
