# EGPL Runtime — Project Prompt Genesis

**Evidence-Gated Prompt Loops · Research preview v0.1.0**

An experimental Python reference runtime that distinguishes a model's proposed answer from a verifier-authorized completion. No paid API, dependencies at runtime, or executable model-generated code. This is not a claim of a new scientific paradigm or a leaderboard victory.

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

## Initial experiment

See [results](benchmarks/results.json), [test log](benchmarks/test-log.txt), [specification](specification/protocol.md), and [research proposal](research/research-preview.md). The eight handcrafted fault cases compare a one-shot acceptance rule against gated retries. This is a mechanism demonstration, not a fair LLM performance comparison. The exact-match verifier knows the expected answer and the baseline does not; retries also cost extra attempts.

## Scope and safety

Fixture adapter only; no network, LLM provider integration, general-purpose tools, cryptographic provenance, sandbox, or independent reviewer. Do not use with secrets. A caller-provided adapter is trusted executable Python and must be reviewed. The runtime does not constrain adapter wall time or token expenditure. Hashes identify content, not authorship or authenticity. A checkpoint can be forged by someone who knows a valid candidate; replay validates the predicate, not history. See [SECURITY.md](SECURITY.md).

License: MIT. Contributions and negative results welcome.
