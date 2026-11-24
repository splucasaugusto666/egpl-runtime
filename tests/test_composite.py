"""Acceptance tests for host-owned, multi-criterion JSON gates."""
import json
import hashlib
import unittest
from dataclasses import replace
from egpl.core import Contract, FixtureAdapter, run, optimize, evidence

def rule(name, path, verifier, expected):
    return dict(id=name, path=path, verifier=verifier, expected=expected)

def contract(rules):
    return Contract('Produce a structured record', json.dumps(rules), 3, verifier='all')

class CompositeGateTests(unittest.TestCase):
    def setUp(self):
        self.rules = [rule('status','/status','exact','ok'),
                      rule('count','/count','integer_range','{"min":2,"max":5}'),
                      rule('labels','/labels','json_equal','["a","b"]')]
        self.c = contract(self.rules)

    def test_all_checks_required(self):
        result = run(self.c, FixtureAdapter(['{"status":"ok","count":99,"labels":["a","b"]}',
                                             '{"status":"ok","count":3,"labels":["a","b"]}']))
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['attempts'], 2)
        self.assertEqual(result['trace'][0]['checks'], [
            {'id':'status','passed':True}, {'id':'count','passed':False},
            {'id':'labels','passed':True}])
        self.assertTrue(all(x['passed'] for x in result['trace'][1]['checks']))

    def test_missing_field_and_type_mismatch(self):
        for candidate in ('{"status":"ok","labels":["a","b"]}',
                          '{"status":"ok","count":"3","labels":["a","b"]}',
                          '{"status":"ok","count":true,"labels":["a","b"]}',
                          '{"status":"ok","count":3.0,"labels":["a","b"]}'):
            self.assertFalse(evidence(self.c, candidate, 0)['passed'])

    def test_json_pointer_escape_and_array(self):
        c = contract([rule('value','/a~1b/~0key/0','exact','yes')])
        self.assertTrue(evidence(c, '{"a/b":{"~key":["yes"]}}', 0)['passed'])
        for ptr in ('/a~1b/~0key/01','/a~1b/~0key/-','/a~1b/~0key/9'):
            c = contract([rule('value',ptr,'exact','yes')])
            self.assertFalse(evidence(c, '{"a/b":{"~key":["yes"]}}', 0)['passed'])

    def test_root_and_digest(self):
        root = contract([rule('root','','json_equal','{"x":1}')])
        self.assertTrue(evidence(root, '{"x":1}', 0)['passed'])
        h = hashlib.sha256(b'abc').hexdigest()
        c = contract([rule('hash','/content','sha256',h)])
        self.assertTrue(evidence(c, '{"content":"abc"}', 0)['passed'])
        self.assertFalse(evidence(c, '{"content":"ABC"}', 0)['passed'])

    def test_malformed_candidate_fails_closed(self):
        for candidate in ('not JSON','{"status":"bad","status":"ok","count":3,"labels":["a","b"]}',
                          '{"status":"ok","count":NaN,"labels":["a","b"]}',
                          '['*2000+'0'+']'*2000):
            record = evidence(self.c, candidate, 0)
            self.assertFalse(record['passed'])
            self.assertEqual([x['passed'] for x in record['checks']], [False]*3)

    def test_invalid_rules_rejected(self):
        good = self.rules[0]
        for rules in ([], [good]*33, [good,good], [dict(good,id='bad id')],
                      [dict(good,path='missing-slash')], [dict(good,path='/bad~2')],
                      [dict(good,verifier='all')], [dict(good,expected=4)],
                      [dict(good,extra=True)], [dict(good,verifier='integer_range',expected='bad')]):
            with self.subTest(rules=rules), self.assertRaises(ValueError):
                contract(rules)

    def test_checkpoint_replay_and_tamper(self):
        proposals = ['{}','{"status":"ok","count":3,"labels":["a","b"]}']
        cp = run(self.c, FixtureAdapter(proposals), step_limit=1)
        self.assertEqual(run(self.c, FixtureAdapter(proposals), cp)['status'], 'verified')
        cp['trace'][0]['checks'][0]['passed'] = True
        with self.assertRaises(ValueError):
            run(self.c, FixtureAdapter(proposals), cp)

    def test_optimizer_cannot_remove_rule(self):
        changed = replace(self.c, expected=json.dumps(self.rules[:1]))
        with self.assertRaises(ValueError):
            optimize(self.c, [changed], [{}])

if __name__ == '__main__':
    unittest.main()
