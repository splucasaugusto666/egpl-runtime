# Behavioral research lab

Goal: model-independent black-box behavioral studies with blinded trial export, paired comparison, missing-data accounting and protocol codecs. Preserve v0.4 contracts. Implement tests first, then deterministic manifests, scoring and wire adapters. Do not send network requests or ask for internal reasoning; transport is supplied by the caller, existing loopback adapter remains optional. Manual chat supports any model capable of text output. Test five wire formats with local fixtures; do not claim live provider compatibility. Publish only after CI.
