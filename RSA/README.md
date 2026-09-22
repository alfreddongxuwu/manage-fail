# RSA models

M-outcome and M-attempt are the two baseline models; M-causal is the main model. M-QUD and M-backoff extend M-causal. Module paths and CSV column names retain their existing identifiers for compatibility.

All models use `alpha = 1`, with no parameter fitting. Norming priors and naturalness costs are read from `results/`; summaries use equal design-condition weights.

| Model | Run module | Description |
|---|---|---|
| M-outcome | `RSA.model_comparison.run_m0` | Outcome-only semantics, four TRY/outcome worlds |
| M-attempt | `RSA.model_comparison.run_m1` | Direct lexical TRY, four worlds |
| M-causal | `RSA.m2.run` | Causal prerequisite, ten worlds |
| M-QUD | `RSA.m2_deterministic_qud.run` | M-causal with observed deterministic QUD |
| M-backoff | `RSA.m2_backoff.run` | M-causal with KL backoff to the contextual TRY prior |

Run from the repository root after the descriptive analysis:

```sh
python -m RSA.model_comparison.run_m0
python -m RSA.model_comparison.run_m1
python -m RSA.m2.run
python -m RSA.m2_deterministic_qud.run
python -m RSA.m2_backoff.run
python -m unittest discover -s RSA/model_comparison/tests
```

Predictions and comparisons are written to each model's `outputs/` directory.
