# Manage / fail

Experimental materials, de-identified data, statistical analyses and RSA models.

- `data/`: 100 norming records, 483 photo records, 484 package records and 240 photo pilot records. The pilot is excluded from the main analysis.
- `code/`: screening, descriptive statistics and figure scripts.
- `results/`: analysis tables and R mixed-model scripts.
- `RSA/`: M0, M1, M2, Mqud and Mbackoff, with fixed alpha = 1.
- `experiments/`: norming and main-experiment demos.
- `materials/`: consent, demographic questions and stimuli.
- `figures/`: experiment examples and analysis figures.

Participant, study and session identifiers have been replaced with random surrogate codes. Filenames are sequential record labels. Repeated identifiers retain the same code across files. The mapping and original identifiers are excluded. Demographics, responses, response times and experimental conditions are retained; these data are pseudonymized, not fully anonymous.

## Analysis

From the repository root (Python 3.10+; R with lme4 and lmerTest):

```sh
python -m pip install -r RSA/model_comparison/requirements.txt
python code/run_all_analyses.py
```

Use `--skip-r` for screening and descriptives only, or `--rscript /path/to/Rscript` to select R.
Descriptive means weight design conditions equally: item x prior for norming and item x prior x QUD x utterance for the main experiment. Participants are averaged within cells first. Ratings are reported on the 0-1 scale; original 0-100 ratings are retained.

The main mixed model is `try ~ utterance + prior + qud + rating_order + (1 | item)`, estimated by REML. Fixed effects and planned contrasts use Satterthwaite tests; p-values are unadjusted. The `try_didnt_manage_didnt_fail` directory contains the supplementary subset analysis; run its `analysis.R` after the main analysis and RSA models.

See [RSA/README.md](RSA/README.md) for model commands and [code/figures/README.md](code/figures/README.md) for figures.

## Experiment demos

```sh
cd experiments/main-experiment  # or experiments/norming
pnpm install --frozen-lockfile
pnpm dev
```

Requires Node.js 22 and pnpm 11.0.7. Both demos retain the experiment flow, upload no responses, and redirect to the Prolific homepage on completion. Prolific URL parameters do not enable collection.

After GitHub Pages deployment, the entry points are:

- [Norming](https://alfreddongxuwu.github.io/manage-fail/norming/)
- [Photo](https://alfreddongxuwu.github.io/manage-fail/main-experiment/photo/)
- [Package](https://alfreddongxuwu.github.io/manage-fail/main-experiment/package/)

Append `?condition=0` to select a condition (0-3 for norming; 0-31 within each main item). The workflow builds both demos. Deployment is disabled unless GitHub Pages is configured and the repository variable `ENABLE_PAGES` is set to `true`.
