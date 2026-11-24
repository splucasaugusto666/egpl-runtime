# Composite evidence gates

Use `verifier: "all"` to require 1–32 named primitive checks on a single JSON candidate. The outer contract's `expected` is a JSON-encoded array of rule objects; this preserves the v0.1–v0.3 string contract format. Every rule has exactly four fields:

```json
[
  {
    "id": "status",
    "path": "/status",
    "verifier": "exact",
    "expected": "ok"
  },
  {
    "id": "count",
    "path": "/count",
    "verifier": "integer_range",
    "expected": "{\"min\":2,\"max\":5}"
  },
  {
    "id": "labels",
    "path": "/labels",
    "verifier": "json_equal",
    "expected": "[\"a\",\"b\"]"
  }
]
```

Each path is a JSON pointer ([RFC 6901](https://www.rfc-editor.org/rfc/rfc6901)). Empty path selects the entire document; ~1 escapes /, ~0 escapes ~. Array indices must be canonical decimal indices. Missing paths fail, even if another rule passes. Exact and hash checks require a JSON string; integer range requires an actual integer (no bool, float, or numeric string); JSON equality accepts any JSON value and preserves array order. No nested composite rules or executable expressions. IDs must be unique ASCII identifiers of 1–64 characters; paths max 512 characters. All configuration and candidate text remains subject to the 64 KiB UTF-8 limit; large canonical representations can fail closed. Existing JSON binary64 limitations apply. Nonfinite JSON, duplicate keys and malformed inputs fail closed. The verifier is a local predicate, not proof that an external action occurred.

```bash
egpl check examples/composite-contract.json examples/composite-candidate.json
egpl run examples/composite-contract.json examples/composite-fixtures.json
```

The first fixture fails the count rule; the second passes all rules. Evidence lists rule IDs and booleans in contract order, without revealing extracted values or expected criteria. Contract hashes bind the complete rule list, so optimization cannot remove or weaken it. Replay reproduces each boolean. Existing primitive evidence format is unchanged. Checkpoints are still unauthenticated; standalone check does not enforce cumulative retry budgets.

## GitHub Actions

In an existing workflow with a checked-out project and Python 3.10+ on PATH:

```yaml
- uses: splucasaugusto666/egpl-runtime@v0.4.0
  with:
    contract: path/to/trusted-contract.json
    candidate: path/to/candidate.json
```

Pin a reviewed commit SHA in security-sensitive workflows. The action invokes the CLI directly from its own directory in isolated Python mode; no package install or API key is needed. Input paths are passed as quoted environment variables, not interpolated as executable shell code. Exit 0 passes; nonzero fails. Linux/bash tested in the project CI. This is a reusable action, not a verified Marketplace listing.

Trust the workflow, contract and runner. Store acceptance criteria outside untrusted generated content; do not let an untrusted PR modify the contract or gate. Never execute untrusted PR code in a privileged workflow (including pull_request_target). Use read-only permissions and nonsecret inputs. The action reads caller-specified paths, so do not grant access to sensitive files or treat this as a filesystem sandbox. It logs hashes and outcomes only, which can still reveal information about low-entropy secrets.
