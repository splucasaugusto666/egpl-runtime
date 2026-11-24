"""Opt-in loopback Ollama adapter; no network access outside 127.0.0.1."""
import http.client
import json
import math
from .verifiers import bounded_text

MAX_RESPONSE_BYTES = 1024 * 1024


class OllamaAdapter:
    """Nonstreaming /api/generate client.

    Socket timeout and requested output-token limit are not a hard wall-clock
    or provider-independent token budget. The local server is trusted.
    """
    def __init__(self, model, *, port=11434, timeout=30, max_tokens=256):
        bounded_text(model)
        if not model.strip() or len(model) > 256:
            raise ValueError('invalid model name')
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError('invalid loopback port')
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 300:
            raise ValueError('invalid socket timeout')
        if type(max_tokens) is not int or not 1 <= max_tokens <= 8192:
            raise ValueError('invalid requested token limit')
        self.model = model
        self.port = port
        self.timeout = timeout
        self.max_tokens = max_tokens

    def __call__(self, prompt, feedback, attempt):
        body = json.dumps({'model': self.model, 'prompt': prompt + '\n' + feedback,
                           'stream': False, 'options': {'num_predict': self.max_tokens}}).encode('utf-8')
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=self.timeout)
        try:
            connection.request('POST', '/api/generate', body=body,
                               headers={'Content-Type': 'application/json'})
            with connection.getresponse() as response:
                if response.status != 200:
                    raise StopIteration
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise StopIteration
                data = json.loads(raw)
                if not isinstance(data, dict) or not isinstance(data.get('response'), str):
                    raise StopIteration
                candidate = data['response']
                bounded_text(candidate)
                return candidate
        except (OSError, http.client.HTTPException, ValueError, RecursionError) as exc:
            raise StopIteration from exc
        finally:
            connection.close()
