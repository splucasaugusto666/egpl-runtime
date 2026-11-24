import hashlib
import unittest
from dataclasses import replace
from egpl.core import Contract, FixtureAdapter, run, optimize, digest
from egpl.verifiers import verify


class TypedGateTests(unittest.TestCase):
    def contract(self, kind='json_equal', expected='{"answer":42}'):
        return Contract('test', expected, 3, verifier=kind)

    def test_json_object_order(self):
        self.assertTrue(verify('json_equal', '{"a":1,"b":2}', '{ "b":2, "a":1 }'))

    def test_json_types_distinct(self):
        for candidate in ('true', '1.0', '"1"'):
            self.assertFalse(verify('json_equal', '1', candidate))

    def test_json_duplicate_key(self):
        self.assertFalse(verify('json_equal', '{"a":1}', '{"a":0,"a":1}'))

    def test_json_invalid_constants(self):
        for candidate in ('NaN', 'Infinity', '1e9999'):
            self.assertFalse(verify('json_equal', '1', candidate))

    def test_json_nested_limit(self):
        self.assertFalse(verify('json_equal', '1', '[' * 2000 + '1' + ']' * 2000))

    def test_range_boundaries(self):
        c = self.contract('integer_range', '{"min":-5,"max":7}')
        for value in ('-5', '7', '0'):
            self.assertEqual(run(c, FixtureAdapter([value]))['status'], 'verified')
        for value in ('-6', '8', 'true', '1.0', '01', '+1', '1\n', '1'*100):
            self.assertNotEqual(run(c, FixtureAdapter([value]))['status'], 'verified')

    def test_sha256(self):
        c = self.contract('sha256', hashlib.sha256(b'abc').hexdigest())
        self.assertEqual(run(c, FixtureAdapter(['wrong', 'abc']))['status'], 'verified')

    def test_invalid_configuration(self):
        for kind, expected in [('eval','x'),('json_equal','{"a":1,"a":2}'),
                               ('integer_range','{"min":true,"max":5}'),
                               ('integer_range','{"min":5,"max":4}'),('sha256','123')]:
            with self.assertRaises(ValueError):
                self.contract(kind, expected)

    def test_resume_typed_gate(self):
        c = self.contract()
        cp = run(c, FixtureAdapter(['{}','{"answer":42}']), step_limit=1)
        self.assertEqual(run(c, FixtureAdapter(['{}','{"answer":42}']), cp)['status'], 'verified')

    def test_verifier_immutable(self):
        c = self.contract()
        with self.assertRaises(ValueError):
            optimize(c, [replace(c, verifier='exact')], [{}])

    def test_wrong_verifier_checkpoint(self):
        c = self.contract()
        cp = run(c, FixtureAdapter(['{}']), step_limit=1)
        with self.assertRaises(ValueError):
            run(replace(c, verifier='exact'), FixtureAdapter([]), cp)

    def test_checkpoint_boolean_type_tamper(self):
        c = self.contract()
        cp = run(c, FixtureAdapter(['{}']), step_limit=1)
        cp['trace'][0]['passed'] = 0
        with self.assertRaises(ValueError):
            run(c, FixtureAdapter([]), cp)

    def test_checkpoint_malformed(self):
        with self.assertRaises(ValueError):
            run(self.contract(), FixtureAdapter([]), [])

    def test_oversized_and_invalid_unicode(self):
        c = self.contract()
        for value in ('x' * 65537, '\ud800', 'é' * 40000):
            self.assertEqual(run(c, FixtureAdapter([value]))['status'], 'blocked')

    def test_legacy_exact_id(self):
        c = Contract('task', 'OK', 2)
        self.assertEqual(c.contract_id, digest({'objective':'task','expected':'OK','max_attempts':2,'strategy':c.strategy}))

if __name__ == '__main__':
    unittest.main()
