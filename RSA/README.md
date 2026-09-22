# RSA models

All models use `alpha = 1`, with no parameter fitting. Norming priors and naturalness costs are read from `results/`; summaries use equal design-condition weights.

| Model | Description |
|---|---|
| M0 | Outcome-only semantics, four TRY/outcome worlds |
| M1 | Direct lexical TRY, four worlds |
| M2 | Causal prerequisite, ten worlds |
| Mqud | M2 with observed deterministic QUD |
| Mbackoff | M2 with KL backoff to the contextual TRY prior |

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
