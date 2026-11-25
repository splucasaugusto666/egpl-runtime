# EGPL Runtime — Project Prompt Genesis

**Evidence-Gated Prompt Loops · Research preview v0.5.0**

An experimental Python reference runtime that distinguishes a model's proposed answer from a verifier-authorized completion. No mandatory paid API, runtime dependencies, or executable model-generated code. This is not a claim of a new scientific paradigm or a leaderboard victory.

```text
Contract -> compile -> candidate -> trusted predicate -> evidence
                           ^                             |
                           +--- retry if budget remains --+
                                     or stop / checkpoint
```

## Quickstart

Python 3.10+. From this directory (installation is optional):

```bash
python -m unittest discover -s tests -v
python -m egpl.cli validate examples/contract.json
python -m egpl.cli compile examples/contract.json
python -m egpl.cli run examples/contract.json examples/fixtures.json --steps 1 --output checkpoint.json
python -m egpl.cli resume examples/contract.json examples/fixtures.json checkpoint.json
python -m egpl.cli evaluate examples/contract.json checkpoint.json
python -m egpl.cli benchmark
```

To install: `python -m pip install .` (may need build tooling). The installed entry point is `egpl`. `inspect` and `evaluate` replay checkpoint predicates, not external action provenance. `optimize CONTRACT CANDIDATES DEV_CASES` selects a strategy from user-provided fixture outcomes, with invariant checks; see `examples/`.

The first fixture claims success but fails the exact-match predicate; the second candidate passes. `verified` refers **only** to that predicate, not general correctness or proof of real-world execution.

## Typed evidence gates

Choose exact text, canonical JSON equality, an inclusive integer range or SHA-256 content matching. See [typed verifiers](docs/typed-verifiers.md) for constraints and examples. Verifier configuration is part of the immutable contract.

```bash
egpl run examples/typed-contract.json examples/typed-fixtures.json
```

## Multi-criterion evidence gates

Require several independent checks on a structured candidate, with per-rule pass/fail evidence and immutable acceptance criteria. Use JSON pointers to target fields. See [composite gates](docs/composite-gates.md).

```bash
egpl check examples/composite-contract.json examples/composite-candidate.json
```

Integrate EGPL directly in GitHub Actions:

```yaml
- uses: splucasaugusto666/egpl-runtime@v0.4.0
  with:
    contract: path/to/trusted-contract.json
    candidate: path/to/candidate.json
```

Requires Python 3.10+ and a trusted workflow/contract; pin a reviewed commit SHA for sensitive workflows.

## Use with your existing AI agent

**Don't trust "done". Check it.**

```bash
egpl check examples/agent-contract.json examples/agent-candidate.txt
```

Exit 0 means the predicate passed; 1 means it failed; 2 means invalid input or unavailable resources. Import the portable [verification skill](skills/egpl-verify/SKILL.md) into a supported agent host, or call the CLI directly from CI. Optional [local Ollama adapter](docs/agent-integration.md) lets a user-selected local model propose candidates. No cloud credentials required for the local workflow.

## Behavioral Intelligence Research

Study the model, not just the prompt. Compare matched interventions under controlled conditions and keep expected answers separate from exported trials.

```bash
egpl study-prepare examples/behavior-study.json --repeats 2 --seed 17 > trials.json
egpl study-score examples/behavior-study.json trials.json responses.json --model YOUR_MODEL --mode manual
```

Any text-capable chat can participate manually. Five programmatic wire codecs cover OpenAI Chat Completions, compatible Chat Completions, Anthropic Messages, Gemini generateContent and Ollama generate, using caller-owned transport. The optional local Ollama workflow is also available. See [behavioral lab](docs/behavior-lab.md). Protocol fixtures are not live provider compatibility or evidence of model cognition.

## Initial experiment

See [results](benchmarks/results.json), [test log](benchmarks/test-log.txt), [specification](specification/protocol.md), and [research proposal](research/research-preview.md). The eight handcrafted fault cases compare a one-shot acceptance rule against gated retries. This is a mechanism demonstration, not a fair LLM performance comparison. The exact-match verifier knows the expected answer and the baseline does not; retries also cost extra attempts.

## Scope and safety

Fixture adapter and optional loopback Ollama HTTP adapter (protocol tested against a fake local server, no actual model evaluation). No general-purpose tools, cryptographic provenance, sandbox, or independent reviewer. Do not use with secrets. A caller-provided adapter is trusted executable Python and must be reviewed. The runtime does not constrain adapter wall time or token expenditure. Hashes identify content, not authorship or authenticity. A checkpoint can be forged by someone who knows a valid candidate; replay validates the predicate, not history. See [SECURITY.md](SECURITY.md).

License: MIT. Contributions and negative results welcome.
