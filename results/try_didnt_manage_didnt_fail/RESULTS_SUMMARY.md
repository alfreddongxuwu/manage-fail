# TRY subset results: didn't manage + didn't fail

Model: try ~ utterance + prior + qud + rating_order + (1 | item)

N = 241 ; response scale: 0-1.
Subset of 961 source observations: didnt_manage: 121; didnt_fail: 120.
All included observations for these two utterances are retained; no additional exclusions.
Reference levels: didn't manage, low prior, TRY? QUD, TRY-first.
REML estimation using lmerTest/lme4. Item has package and photo levels.
Prior, QUD and rating-order effects are common additive effects across the two selected utterances.
Rating order compares completion-first (P?|TRY?|NAT) with TRY-first (TRY?|P?|NAT).
Naturalness is always last. The model contains main effects only.
Coefficients and planned contrasts use two-sided Wald-type t-tests with Satterthwaite df.
Overall terms use Type II F-tests with Satterthwaite denominator df. All p-values are unadjusted.
There are no interactions; separate contextual slopes for each utterance are not estimated or tested. The 95% CIs use the same t distribution.

## Fit

- Singular fit at tolerance 1e-4: FALSE
- Fixed design rank: 5 of 5
- Optimizer code: 0
- Fit warnings: 0
- Convergence messages: none
- Item variance: 0.00099107; SD: 0.031481; ICC: 0.009377.
- The two item levels provide limited information about the random-intercept variance.

## Overall fixed effects

| Term | NumDF | DenDF | F | p |
|---|---:|---:|---:|---:|
| utterance | 1 | 235.004 | 56.3060 | 1.273e-12 |
| prior | 1 | 235.001 | 41.3901 | 6.918e-10 |
| qud | 1 | 235.013 | 0.6670 | 0.41492 |
| rating_order | 1 | 235.676 | 0.3393 | 0.56079 |

## Prior and QUD effects

| Analysis | Estimate | SE | df | t | p | 95% CI |
|---|---:|---:|---:|---:|---:|---|
| prior_effect | 0.268512 | 0.041736 | 235.001 | 6.434 | 6.918e-10 | [0.186286, 0.350737] |
| qud_effect | 0.034746 | 0.042543 | 235.013 | 0.817 | 0.41492 | [-0.049069, 0.118560] |

The contextual coefficients are shared across the two selected utterances under the additive model.
This supplementary subset analysis leaves the canonical full-sample analysis unchanged.

Reproduce with Rscript --vanilla results/try_didnt_manage_didnt_fail/analysis.R; requires lme4, lmerTest and dplyr.
