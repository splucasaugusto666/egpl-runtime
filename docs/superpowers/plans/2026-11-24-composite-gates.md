# Composite evidence gates and CI integration implementation plan

Goal: verify multiple independent conditions on one structured candidate; distribute a composite GitHub Action. Preserve old contract IDs and evidence records. Use bounded, flat conjunctions of 1–32 named rules, RFC 6901 pointers, existing primitive predicates, strict JSON parsing; no executable criteria or nested composite rules. Keep expected values host-owned. Provide individual boolean evidence, replay checks, and immutable optimizer constraints. No claims of general correctness, proof of execution, or live model results.

1. Add tests and observe failure on existing runtime.
2. Implement composite rule validation and deterministic evaluation; integrate evidence records and schema.
3. Add reusable action (Python 3.10+ on PATH, no shell interpolation of inputs) and CI tests for acceptance/rejection.
4. Document trust boundary and example; run full Python matrix; merge after verification and publish experimental release. Sequential implementation, no independent reviewer available.
