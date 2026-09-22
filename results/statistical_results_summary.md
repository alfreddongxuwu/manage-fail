# Statistical results summary

The main experiment contains **961** cleaned participant observations. All ratings and effect estimates use the 0-1 scale.

## Canonical inferential model

    try ~ utterance + prior + qud + rating_order + (1 | item)

One linear mixed-effects model is fitted by REML using lmerTest/lme4. try maps to try_rating_01 and utterance maps to utterance_id. Reference levels are managed, low prior, TRY? QUD and TRY-first rating order. Item has package and photo levels and contributes a random intercept.

Prior, QUD and rating order have common additive effects across all eight utterances.  Rating order compares completion-first (P?|TRY?|NAT) with TRY-first (TRY?|P?|NAT). Coefficients and planned contrasts use two-sided Wald-type t-tests with Satterthwaite degrees of freedom. Overall terms use Type II F-tests with Satterthwaite denominator degrees of freedom. **All p-values are unadjusted.** Group contrasts weight their utterances equally; the reported 95% intervals are pointwise t intervals.

## Fit diagnostics

| n | Fixed rank | Item variance | Item SD | Residual SD | ICC | Singular |
| --- | --- | --- | --- | --- | --- | --- |
| 961 | 11/11 | 0.00043053 | 0.020749 | 0.294868 | 0.004927 | FALSE |

Optimizer: nloptwrap; exit code: 0. Fit warnings: 0. The two item levels provide limited information about the random-intercept variance.

## Overall fixed effects

| Term | NumDF | DenDF | F | p |
| --- | --- | --- | --- | --- |
| utterance | 7 | 949.013 | 70.2116 | 1.025e-81 |
| prior | 1 | 949.015 | 176.7452 | 4.143e-37 |
| qud | 1 | 949.004 | 0.4117 | 0.52128 |
| rating_order | 1 | 949.251 | 0.0361 | 0.84944 |

## Contextual effects

| Contrast | Direction | Estimate | SE | t | df | p | 95% CI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| prior_effect | high - low | 0.2530 | 0.0190 | 13.295 | 949.015 | 4.143e-37 | [0.2156, 0.2903] |
| qud_effect | P? - TRY? | 0.0122 | 0.0191 | 0.642 | 949.004 | 0.52128 | [-0.0252, 0.0497] |
| rating_order_effect | completion-first - TRY-first | -0.0036 | 0.0191 | -0.190 | 949.251 | 0.84944 | [-0.0411, 0.0338] |
| prior_minus_qud_effect | (high - low prior) - (P? - TRY? QUD) | 0.2407 | 0.0272 | 8.858 | 949.002 | 3.936e-18 | [0.1874, 0.2941] |

## Implicative boosts

| Contrast | Direction | Estimate | SE | t | df | p | 95% CI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| implicative_boost_all_four_vs_did_and_didnt | mean(managed, didnt_manage, failed, didnt_fail) - mean(did, didnt) | 0.0539 | 0.0233 | 2.317 | 949.026 | 0.02070 | [0.0083, 0.0996] |
| managed_and_didnt_fail_minus_did | mean(managed, didnt_fail) - did | 0.0147 | 0.0328 | 0.450 | 949.003 | 0.65316 | [-0.0496, 0.0791] |
| didnt_manage_and_failed_minus_didnt | mean(didnt_manage, failed) - didnt | 0.0931 | 0.0330 | 2.819 | 949.029 | 0.00491 | [0.0283, 0.1579] |
| managed_minus_did | managed - did | 0.0482 | 0.0379 | 1.271 | 949.000 | 0.20414 | [-0.0262, 0.1226] |
| didnt_fail_minus_did | didnt_fail - did | -0.0187 | 0.0379 | -0.493 | 949.010 | 0.62199 | [-0.0931, 0.0557] |
| didnt_manage_minus_didnt | didnt_manage - didnt | 0.1109 | 0.0381 | 2.912 | 949.037 | 0.00368 | [0.0361, 0.1856] |
| failed_minus_didnt | failed - didnt | 0.0753 | 0.0381 | 1.978 | 949.010 | 0.04819 | [0.0006, 0.1500] |

## Outcome contrasts

| Contrast | Direction | Estimate | SE | t | df | p | 95% CI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| positive_outcome_grouped | mean(managed, didnt_fail) - mean(didnt_manage, failed) | 0.3642 | 0.0269 | 13.557 | 949.004 | 2.100e-38 | [0.3115, 0.4169] |
| managed_minus_didnt_manage | managed - didnt_manage | 0.3799 | 0.0380 | 10.000 | 949.003 | 1.886e-22 | [0.3053, 0.4544] |
| didnt_fail_minus_failed | didnt_fail - failed | 0.3485 | 0.0380 | 9.174 | 949.020 | 2.775e-19 | [0.2740, 0.4231] |

## Fixed effect coefficients

| Term | Estimate | SE | df | t | p |
| --- | --- | --- | --- | --- | --- |
| (Intercept) | 0.6078 | 0.0351 | 15.986 | 17.341 | 8.656e-12 |
| utterancedidnt_manage | -0.3799 | 0.0380 | 949.003 | -10.000 | 1.886e-22 |
| utterancefailed | -0.4154 | 0.0380 | 949.002 | -10.934 | 2.715e-26 |
| utterancedidnt_fail | -0.0669 | 0.0381 | 949.010 | -1.757 | 0.07930 |
| utterancedid | -0.0482 | 0.0379 | 949.000 | -1.271 | 0.20414 |
| utterancedidnt | -0.4907 | 0.0381 | 949.021 | -12.863 | 5.073e-35 |
| utterancetried | -0.0904 | 0.0381 | 949.000 | -2.375 | 0.01774 |
| utterancedidnt_try | -0.5552 | 0.0382 | 949.011 | -14.521 | 2.699e-43 |
| priorhigh | 0.2530 | 0.0190 | 949.015 | 13.295 | 4.143e-37 |
| qudP? | 0.0122 | 0.0191 | 949.004 | 0.642 | 0.52128 |
| rating_orderP?\|TRY?\|NAT | -0.0036 | 0.0191 | 949.251 | -0.190 | 0.84944 |

## Descriptive TRY and completion ratings

Descriptive means give equal weight to the item x prior x QUD x utterance design conditions represented in each summary. Question order is pooled within each cell except in summaries explicitly conditioned on order. Counts remain participant counts. SD is the condition-weighted mixture SD, including within-cell sample variance and between-cell mean differences. SE is sqrt(sum(s_cell^2/n_cell)/K^2), where K is the number of cells. Intermediate quantities retain full precision; tables round only displayed values.

| Utterance | n | TRY mean | TRY SD | Completion mean | Completion SD |
| --- | --- | --- | --- | --- | --- |
| managed | 120 | 0.7386 | 0.3046 | 0.7338 | 0.3280 |
| didnt_manage | 121 | 0.3589 | 0.3388 | 0.1189 | 0.2107 |
| failed | 121 | 0.3234 | 0.3273 | 0.1346 | 0.2205 |
| didnt_fail | 120 | 0.6691 | 0.3776 | 0.7064 | 0.3726 |
| did | 122 | 0.6902 | 0.3404 | 0.7107 | 0.3368 |
| didnt | 119 | 0.2491 | 0.3046 | 0.1686 | 0.2589 |
| tried | 120 | 0.6483 | 0.3755 | 0.3504 | 0.3360 |
| didnt_try | 118 | 0.1844 | 0.2406 | 0.1422 | 0.2114 |

## Descriptive naturalness ratings

| Utterance | n | Mean | SD | SE |
| --- | --- | --- | --- | --- |
| managed | 120 | 0.6075 | 0.3201 | 0.0278 |
| didnt_manage | 121 | 0.5267 | 0.3186 | 0.0284 |
| failed | 121 | 0.3651 | 0.3078 | 0.0268 |
| didnt_fail | 120 | 0.2302 | 0.2900 | 0.0260 |
| did | 122 | 0.6297 | 0.3264 | 0.0270 |
| didnt | 119 | 0.6700 | 0.2681 | 0.0236 |
| tried | 120 | 0.5535 | 0.2999 | 0.0269 |
| didnt_try | 118 | 0.5892 | 0.3279 | 0.0283 |

Naturalness, completion and within-utterance contextual summaries are descriptive. Their CSV outputs remain in results/results_main. Within-utterance descriptive differences should be distinguished from the shared contextual effects imposed by the additive model.

## Reproduce

    python code/run_all_analyses.py --rscript /path/to/Rscript

The fitted object, model diagnostics, full-precision results, contrast weights and session information are in results/try_question_order.
