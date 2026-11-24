# EGPL v0.1 draft protocol

Contract C = (objective, expected, max_attempts, strategy). The first three fields are immutable under optimization. The trusted host owns the expected value and budget; the candidate producer receives only the objective and strategy. A caller may include the expected value in the objective inadvertently; this is not a confidentiality guarantee.

For attempt i < B, the proposer returns a string x. The host evaluates V(C,x) := (x == expected). The evidence record binds x, i and C by deterministic SHA-256 identifiers. Only V=true can authorize VERIFIED. Otherwise retry or terminate as EXHAUSTED when the attempt budget is consumed. Missing/invalid candidate produces BLOCKED; a caller step limit produces PAUSED. A verified checkpoint is terminal. All previous records are replayed and compared on resume, including their order and predicate results. There are no effects to replay in this prototype.

Safety invariant (under the trusted-host assumption): VERIFIED implies at least one recorded candidate equals expected. Boundedness: at most B recorded attempts; wall-clock duration is not bounded. The adapter's StopIteration and invalid types are handled; arbitrary adapter exceptions propagate. An attacker with access to the verifier or contract can defeat the assumption. Checkpoint hashes are not signatures.

The outer loop compares strategies on development fixtures, maximizing verified cases then minimizing attempts, with stable tie-breaking. It rejects invariant changes before evaluation. This is a discrete selection mechanism, not actual LLM optimization.

## Prompt-only mode (advisory)

State the goal and invariants, propose a candidate, request external evidence, compare it with the acceptance predicate, retry within the budget. Report VERIFIED only after the host returns a valid result. A chat prompt cannot enforce this protocol by itself.
