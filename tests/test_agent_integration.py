import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from egpl.core import Contract


class AgentIntegrationTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'egpl.cli', *args],
                              capture_output=True, text=True, timeout=10)

    def test_check_exit_codes_and_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            contract = root / 'contract.json'
            contract.write_text('{"objective":"say OK","expected":"OK","max_attempts":2}')
            candidate = root / 'candidate.txt'
            candidate.write_text('WRONG')
            rejected = self.cli('check', str(contract), str(candidate))
            self.assertEqual(rejected.returncode, 1, rejected.stderr)
            self.assertFalse(json.loads(rejected.stdout)['passed'])
            candidate.write_text('OK')
            accepted = self.cli('check', str(contract), str(candidate))
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertTrue(json.loads(accepted.stdout)['passed'])
            candidate.unlink()
            self.assertEqual(self.cli('check', str(contract), str(candidate)).returncode, 2)

    def test_loopback_model_retry_and_no_expected_leak(self):
        from egpl.adapters import OllamaAdapter
        from egpl.core import run
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append(body)
                self.assert_path = self.path
                reply = json.dumps({'response': 'wrong' if len(requests) == 1 else 'SECRET_42'}).encode()
                self.send_response(200)
                self.send_header('Content-Length', str(len(reply)))
                self.end_headers()
                self.wfile.write(reply)
            def log_message(self, *args): pass
        with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                adapter = OllamaAdapter('fixture-model', port=server.server_port, timeout=2, max_tokens=32)
                result = run(Contract('return the fixture target', 'SECRET_42', 2), adapter)
            finally:
                server.shutdown()
                thread.join()
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(len(requests), 2)
        self.assertNotIn('SECRET_42', json.dumps(requests))
        self.assertIn('Previous candidate failed', requests[1]['prompt'])
        self.assertEqual(requests[0]['options']['num_predict'], 32)
        self.assertIs(requests[0]['stream'], False)

    def test_adapter_invalid_configuration(self):
        from egpl.adapters import OllamaAdapter
        for opts in ({'port':0},{'timeout':0},{'max_tokens':0},{'port':True}):
            with self.assertRaises(ValueError):
                OllamaAdapter('test', **opts)
        with self.assertRaises(ValueError):
            OllamaAdapter('')

    def test_model_transport_failure_is_blocked(self):
        from egpl.adapters import OllamaAdapter
        from egpl.core import run
        # Bound but non-listening socket: connection refusal without choosing an arbitrary port.
        import socket
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            result = run(Contract('task','OK',2), OllamaAdapter('test', port=sock.getsockname()[1], timeout=1))
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['attempts'], 0)

if __name__ == '__main__':
    unittest.main()
