import argparse
import json
from pathlib import Path
from dataclasses import asdict
from .core import Contract, FixtureAdapter, compile_prompt, run, optimize, evidence
from .verifiers import MAX_BYTES, bounded_text
import sys


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    p = argparse.ArgumentParser(prog='egpl')
    sub = p.add_subparsers(dest='command', required=True)
    for name in ('validate', 'compile', 'run', 'resume', 'evaluate', 'optimize', 'inspect'):
        s = sub.add_parser(name)
        s.add_argument('contract')
        if name in ('run', 'resume'):
            s.add_argument('fixtures')
            s.add_argument('--steps', type=int)
            s.add_argument('--output')
        if name in ('resume', 'evaluate', 'inspect'):
            s.add_argument('checkpoint')
        if name == 'optimize':
            s.add_argument('candidates')
            s.add_argument('dev_cases')
    check = sub.add_parser('check', help='verify a UTF-8 candidate file without an LLM')
    check.add_argument('contract')
    check.add_argument('candidate')
    model = sub.add_parser('run-ollama', help='opt in to a local Ollama server')
    model.add_argument('contract')
    model.add_argument('--model', required=True)
    model.add_argument('--port', type=int, default=11434)
    model.add_argument('--timeout', type=float, default=30)
    model.add_argument('--max-tokens', type=int, default=256)
    sub.add_parser('benchmark')
    a = p.parse_args()
    if a.command in ('check', 'run-ollama'):
        try:
            c = Contract(**load(a.contract))
            if a.command == 'check':
                with Path(a.candidate).open('rb') as f:
                    candidate = f.read(MAX_BYTES + 1).decode('utf-8')
                bounded_text(candidate)
                result = evidence(c, candidate, 0)
                # Do not echo candidate contents in CI logs.
                result.pop('candidate')
                print(json.dumps(result, indent=2))
                return 0 if result['passed'] else 1
            from .adapters import OllamaAdapter
            adapter = OllamaAdapter(a.model, port=a.port, timeout=a.timeout, max_tokens=a.max_tokens)
            result = run(c, adapter)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0 if result['status'] == 'verified' else (2 if result['status'] == 'blocked' else 1)
        except (OSError, ValueError, TypeError, RecursionError) as exc:
            # Do not print potentially sensitive candidate or contract contents.
            print('Invalid input or unavailable resource: ' + type(exc).__name__, file=sys.stderr)
            return 2
    if a.command == 'benchmark':
        from .benchmark import benchmark
        result = benchmark()
    else:
        c = Contract(**load(a.contract))
        if a.command == 'validate':
            result = {'valid': True, 'contract_id': c.contract_id, 'invariant_id': c.invariant_id}
        elif a.command == 'compile':
            result = json.loads(compile_prompt(c))
        elif a.command in ('run', 'resume'):
            result = run(c, FixtureAdapter(load(a.fixtures)), load(a.checkpoint) if a.command == 'resume' else None, step_limit=a.steps)
            if a.output:
                Path(a.output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        elif a.command == 'optimize':
            result = optimize(c, [Contract(**x) for x in load(a.candidates)], load(a.dev_cases))
        else:
            result = run(c, FixtureAdapter([]), load(a.checkpoint), step_limit=0)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    raise SystemExit(main())
