# Model-Adaptive Interaction Engineering — research preview

## Hypothesis and implementation

Select a strategy from controlled, paired development observations instead of assuming every model responds equally. The selector re-scores raw final text against trusted study criteria; it requires identical variant sets across a dimension, at least five distinct case IDs, all paired trials observed, and a descriptive pass-rate gain of at least 0.10 versus plain. These thresholds are engineering defaults, not statistical significance. Distinct IDs do not guarantee independent tasks. Tie-break by gain, then total input characters, then name. Character count is only a size proxy, not tokens, latency, energy or cost. Fallback is plain if evidence is insufficient or no variant qualifies.

Freeze the selected variant and evaluate it on a separate study, optionally a different model. Exact case-ID and prompt overlaps are rejected, but semantic duplicates, shared training data and leakage cannot be ruled out. Record model version, settings, fresh sessions, and pre-register the task split externally. Report all missingness; do not tune on held-out results. A positive development effect and negative held-out effect are both valid outcomes.

```bash
egpl study-select dev.json dev-trials.json dev-responses.json --model MODEL_A --mode manual --dimension format
egpl study-transfer dev.json dev-trials.json dev-responses.json test.json test-trials.json test-responses.json --model MODEL_A --target-model MODEL_B --mode manual --dimension format
python examples/adaptive-demo.py
```

The demo uses scripted responses, deliberately reverses the effect on the target, and demonstrates why adaptation should not be assumed to generalize. No external model tested. Profiles and response hashes are not authenticated; model labels are operator declarations.

## Base prompt library

Six portable advisory prompts: plain, structured, research, engineering, evidence and calibration. See [prompts](../prompts/README.md). Render with `egpl prompt-render research examples/prompt-task.json`. The actual rendered intervention must be registered in the study; a matching variant label does not prove a template caused an effect. Generated prompt text is not a security boundary. The runtime verifier remains independent. No automatic modification of acceptance criteria, provider settings or private reasoning.

## Research program

1. Behavioral fingerprinting: measure per-dimension pass rates, missingness and paired sensitivity under fixed settings.
2. Adaptive synthesis: compare preregistered candidate strategies with equal call budgets; freeze selection before held-out scoring.
3. Cross-model transfer: test source-selected strategies on other models and compare against target-specific selection and plain baseline.
4. Context sensitivity: vary placement, order, irrelevant text and length separately; track exact intervention text.
5. Efficiency: record provider-reported token counts, measured latency and local energy where available; do not substitute character counts for real costs.
6. Mechanistic interpretability: for legally accessible open-weight models only, design activation and intervention experiments with matched controls, reproducible checkpoints and layer-level observations. Behavioral results alone do not establish internal mechanisms. This line is a research proposal, not an implemented interpretability tool.

Primary outcome: held-out verified success under equal attempt budgets. Secondary outcomes: missingness, token usage, latency, failure modes and uncertainty. Use multiple tasks and models, cluster by task, preregister comparisons and report negative results. Compare with existing prompt optimizers and behavioral evaluations before claiming novelty. No claim of consciousness or access to private chain-of-thought.
