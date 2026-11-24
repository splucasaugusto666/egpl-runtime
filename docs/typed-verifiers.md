# Typed evidence gates

Select an optional `verifier` field in a JSON contract. Defaults to `exact`, preserving the v0.1 identity format for exact contracts within the new size limit.

| Kind | Expected (string) | Predicate |
| --- | --- | --- |
| exact | target text | exact Unicode equality |
| json_equal | valid JSON text | canonical JSON string equality (key order and whitespace ignored; bool/int/float distinguished) |
| integer_range | JSON object with min/max integers | ASCII decimal integer within inclusive bounds, up to ±10^18 |
| sha256 | lowercase 64-character digest | SHA-256 of candidate UTF-8 bytes |

JSON duplicate keys, nonfinite values, excessively nested inputs and unsupported verifiers fail closed. Text is limited to 64 KiB of UTF-8 bytes; the JSON Schema length limit is a preliminary character check, not a full validator. Python JSON float parsing uses binary64; use exact or string-encoded numbers for precision-sensitive tasks. The hash predicate checks equality to a supplied digest, not origin, identity or authenticity.

The verifier and expected value are immutable under optimization. The compiler does not send the expected value. Configure the objective with the required output shape. A valid checkpoint is replayed against the original predicate; forged or truncated history is still possible without authenticated storage. Oversized/invalid-Unicode candidates produce BLOCKED without entering the trace. Ordinary predicate failures consume attempts.

```bash
egpl run examples/typed-contract.json examples/typed-fixtures.json
```

This example uses simulated proposals. No LLM efficacy or general security guarantee is claimed.
