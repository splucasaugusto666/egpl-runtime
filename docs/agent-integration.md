# Integrate with existing agents

EGPL is a small acceptance gate, not a replacement for agent harnesses. Any shell-capable workflow can call the CLI:

```sh
python -m pip install .
egpl check examples/agent-contract.json examples/agent-candidate.txt
```

Exit 0 = predicate passed, 1 = failed, 2 = invalid input or unavailable resource. The check is a single invocation and does not maintain a cumulative attempt budget. The calling agent must enforce its own total budget. Output contains the predicate identity, contract hash and candidate hash, not the text itself. Hashes do not establish provenance; do not process secrets.

A portable [Agent Skill](../skills/egpl-verify/SKILL.md) describes the workflow. Copy the skill folder into a supported host's skills directory following that host's documentation. No claim that every host has been tested.

## Optional local Ollama runtime

Install Ollama separately, start a trusted local server and download a model you are authorized to use. Select the installed model name explicitly:

```sh
egpl run-ollama examples/agent-contract.json --model YOUR_INSTALLED_MODEL --max-tokens 64
```

The adapter only connects to 127.0.0.1, sends nonstreaming POST requests to /api/generate, requests an output-token cap, bounds the response size and uses a socket timeout. It does not follow redirects or use proxy settings. A transport error returns BLOCKED; it does not claim completion. It sends the contract's objective and strategy, so do not put secrets there. Results include candidate text. A socket timeout is not a hard total-time limit, and num_predict is a request to the model server, not independently enforced accounting. No automatic downloads or paid cloud requests. The user is responsible for the local model and any server-side behavior.

The HTTP interface is covered by tests against a deterministic loopback HTTP server, not a live Ollama model. Real-model quality and compatibility remain experimental.
