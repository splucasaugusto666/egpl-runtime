# Behavioral Intelligence Research

The lab studies observable input/output behavior, not consciousness or hidden reasoning. Its candidate contribution is coupling controlled behavioral evidence with executable prompt contracts; novelty and efficacy remain unproven.

## Run a model-independent study

```bash
egpl study-prepare examples/behavior-study.json --repeats 2 --seed 17 > trials.json
```

Send each trial's prompt to a fresh session with the same model/version/settings. Do not send the study answer key or other trials. Save final public text as a JSON mapping from trial id to string. Omit unavailable trials; never guess. The manifest has trial IDs, case/variant labels, repeats and prompt text but no separate expected-answer field. Some tasks explicitly encode output constraints or necessary facts. The manifest hash binds the study but is not a secrecy mechanism; do not use confidential answers.

```bash
egpl study-score examples/behavior-study.json trials.json responses.json --model "provider/model-version" --mode manual > profile.json
```

The profile reports planned, observed, passed and missing counts. Paired comparisons use only matched observed plain/intervention trials, including discordant outcomes. A missing result is not a success or a measured failure. Profiles omit raw response text but contain hashes (not anonymity or provenance). Mode and model are caller declarations, not authenticated identity. Five toy cases are a development demonstration, not a representative benchmark. The variants are interventions, not all guaranteed semantic equivalents.

Optional local run (explicit opt-in, installed Ollama model required):

```bash
egpl study-ollama examples/behavior-study.json trials.json --model YOUR_LOCAL_MODEL --max-tokens 128 > collected.json
```

This makes at most one call per trial, no automatic retry, up to 400 trials per manifest. Local server behavior, model configuration and hardware costs are the operator's responsibility. Output contains raw final responses; do not use sensitive input. A transport failure is missing, not measured model incompetence. The adapter does not enforce hard total time or actual token spend.

## Universal bridge

Any text-capable model can participate manually. Programmatic interoperability uses a caller-owned authorized transport with five codecs: OpenAI Chat Completions, compatible Chat Completions, Anthropic Messages, Gemini generateContent, and Ollama generate. Wire-format tests are not live provider tests. Gemini model name belongs in the caller's URL; credentials, authentication, URL selection, quotas, model availability and provider-specific compatibility are caller responsibilities. No cloud HTTP client, API key collection, provider routing or paid requests are performed by EGPL's wire codec.

```python
from egpl.protocols import WireAdapter
from egpl.behavior import prepare, collect, score
# Supply your own authorized transport(protocol, model, request_body) -> response_dict.
# It must enforce endpoints, timeouts, response-size limits, and any budget.
# adapter = WireAdapter("anthropic", "YOUR_MODEL", transport, max_tokens=128)
# manifest = prepare(study, repeats=2, seed=17)
# profile = score(study, manifest, collect(manifest, adapter), model="YOUR_MODEL", mode="caller-transport")
```

Final text only is extracted; private reasoning fields are ignored, tool calls are not executed. Refusals, truncated output and unsupported finish codes in these codecs are blocked. Not every model or endpoint supports these parameters. Providers with different protocols can implement a callable adapter. No universal live compatibility claim.

## Research method

Hypotheses: model-specific sensitivity to formatting, irrelevant information and data/instruction boundaries is measurable; selecting a strategy from held-out behavior may improve success per attempt compared with a fixed strategy. Refutation: gains disappear across held-out tasks or cost more than the improvement warrants. Use fixed model versions and settings, matched trial budgets, randomized order, independent sessions, development/test separation and uncertainty estimates. Report all missingness and negative results. For deployment, maintain immutable acceptance criteria and a fallback strategy. Do not tune on the final evaluation set. Behavior is not a proof of internal cognitive mechanism.

Related precedents: [CheckList](https://aclanthology.org/2020.acl-main.442/), [IFEval](https://arxiv.org/abs/2311.07911), [HELM](https://arxiv.org/abs/2211.09110), [prompt formatting sensitivity](https://arxiv.org/abs/2310.11324), [Structured Prompting Enables More Robust, Holistic Evaluation of Language Models](https://arxiv.org/abs/2511.20836). These already study behavior or sensitivity; EGPL must be evaluated against them and existing optimization systems before asserting originality.

Interface references: [OpenAI](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create), [Anthropic](https://platform.claude.com/docs/en/api/messages/create), [Gemini](https://ai.google.dev/api/generate-content), [Ollama compatibility](https://ollama.com/blog/openai-compatibility). No external model performance measurements have been made for this release.
