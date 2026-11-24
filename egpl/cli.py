import argparse
import json
from pathlib import Path
from dataclasses import asdict
from .core import Contract, FixtureAdapter, compile_prompt, run, optimize


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
    sub.add_parser('benchmark')
    a = p.parse_args()
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
    main()
