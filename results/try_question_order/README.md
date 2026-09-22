# TRY mixed model

Run `Rscript --vanilla results/try_question_order/analysis.R` from the repository root. Requires lme4 and lmerTest.

`try ~ utterance + prior + qud + rating_order + (1 | item)`, fitted with REML.
