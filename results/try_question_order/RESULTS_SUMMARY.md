# TRY mixed-effects results with question order

Model: try ~ utterance + prior + qud + rating_order + (1 | item)

N = 961 ; response scale: 0-1.
REML estimation using lmerTest/lme4. Item has package and photo levels.
Prior, QUD and rating-order effects are common additive effects across all eight utterances.
Rating order compares completion-first (P?|TRY?|NAT) with TRY-first (TRY?|P?|NAT).
Naturalness is always last. The model contains main effects only.
Coefficients and planned contrasts use two-sided Wald-type t-tests with Satterthwaite df.
Overall terms use Type II F-tests with Satterthwaite denominator df. All p-values are unadjusted.
Group contrasts average utterances equally. Their 95% CIs use the same t distribution.

## Fit

- Singular fit at tolerance 1e-4: FALSE
- Fixed design rank: 11 of 11
- Optimizer code: 0
- Convergence messages: none
- Item variance: 0.00043053; SD: 0.020749; ICC: 0.004927.
- The two item levels provide limited information about the random-intercept variance.

## Overall fixed effects

| Term | NumDF | DenDF | F | p |
|---|---:|---:|---:|---:|
| utterance | 7 | 949.013 | 70.2116 | 1.025e-81 |
| prior | 1 | 949.015 | 176.7452 | 4.143e-37 |
| qud | 1 | 949.004 | 0.4117 | 0.52128 |
| rating_order | 1 | 949.251 | 0.0361 | 0.84944 |

## Planned contrasts

| Analysis | Estimate | SE | df | t | p | 95% CI |
|---|---:|---:|---:|---:|---:|---|
| prior_effect | 0.252979 | 0.019029 | 949.015 | 13.295 | 4.143e-37 | [0.215636, 0.290323] |
| qud_effect | 0.012239 | 0.019076 | 949.004 | 0.642 | 0.52128 | [-0.025196, 0.049674] |
| rating_order_effect | -0.003625 | 0.019089 | 949.251 | -0.190 | 0.84944 | [-0.041087, 0.033838] |
| prior_minus_qud_effect | 0.240740 | 0.027177 | 949.002 | 8.858 | 3.936e-18 | [0.187406, 0.294074] |
| implicative_boost_all_four_vs_did_and_didnt | 0.053910 | 0.023265 | 949.026 | 2.317 | 0.02070 | [0.008254, 0.099566] |
| managed_minus_did | 0.048174 | 0.037911 | 949.000 | 1.271 | 0.20414 | [-0.026225, 0.122573] |
| didnt_fail_minus_did | -0.018698 | 0.037912 | 949.010 | -0.493 | 0.62199 | [-0.093099, 0.055703] |
| didnt_manage_minus_didnt | 0.110853 | 0.038071 | 949.037 | 2.912 | 0.00368 | [0.036140, 0.185566] |
| failed_minus_didnt | 0.075310 | 0.038069 | 949.010 | 1.978 | 0.04819 | [0.000600, 0.150019] |
| managed_and_didnt_fail_minus_did | 0.014738 | 0.032787 | 949.003 | 0.450 | 0.65316 | [-0.049605, 0.079081] |
| didnt_manage_and_failed_minus_didnt | 0.093081 | 0.033015 | 949.029 | 2.819 | 0.00491 | [0.028291, 0.157872] |
| positive_outcome_grouped | 0.364211 | 0.026864 | 949.004 | 13.557 | 2.100e-38 | [0.311490, 0.416931] |
| managed_minus_didnt_manage | 0.379875 | 0.037989 | 949.003 | 10.000 | 1.886e-22 | [0.305323, 0.454427] |
| didnt_fail_minus_failed | 0.348546 | 0.037994 | 949.020 | 9.174 | 2.775e-19 | [0.273985, 0.423108] |

The contextual coefficients apply to all utterances under the additive model.
Naturalness and completion are summarized descriptively in the main results directory.

Reproduce with Rscript --vanilla results/try_question_order/analysis.R; requires lme4 and lmerTest.
