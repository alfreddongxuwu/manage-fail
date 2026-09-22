#!/usr/bin/env python3

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from condition_averaging import MAIN_CONDITIONS, summarize_conditions
MAIN = ROOT / "results" / "results_main"
INFERENTIAL = ROOT / "results" / "try_question_order"
OUTPUT = ROOT / "results" / "statistical_results_summary.md"
UTTERANCES = ("managed", "didnt_manage", "failed", "didnt_fail",
              "did", "didnt", "tried", "didnt_try")
GROUPS = (
    ("Contextual effects", ("prior_effect", "qud_effect", "rating_order_effect", "prior_minus_qud_effect")),
    ("Implicative boosts", (
        "implicative_boost_all_four_vs_did_and_didnt",
        "managed_and_didnt_fail_minus_did", "didnt_manage_and_failed_minus_didnt",
        "managed_minus_did", "didnt_fail_minus_did",
        "didnt_manage_minus_didnt", "failed_minus_didnt")),
    ("Outcome contrasts", (
        "positive_outcome_grouped", "managed_minus_didnt_manage", "didnt_fail_minus_failed")),
)

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def fmt(value: str | float, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"

def fmt_p(value: str | float) -> str:
    p = float(value)
    return f"{p:.3e}" if p < .001 else f"{p:.5f}"

def table(headers: list[str], rows: list[list[str]]) -> str:
    def clean(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(map(clean, headers)) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(map(clean, row)) + " |" for row in rows],
    ])

def main() -> None:
    clean = read_csv(MAIN / "main_combined_clean.csv")
    descriptive = read_csv(MAIN / "main_combined_try_mean_by_utterance.csv")
    contrasts = read_csv(INFERENTIAL / "try_planned_contrasts.csv")
    index = {r["analysis"]: r for r in contrasts}
    fit = read_csv(INFERENTIAL / "model_fit_statistics.csv")[0]
    terms = read_csv(INFERENTIAL / "model_term_tests.csv")
    coefs = read_csv(INFERENTIAL / "model_coefficients.csv")
    parts = [
        "# Statistical results summary", "",
        f"The main experiment contains **{len(clean)}** cleaned participant observations. "
        "All ratings and effect estimates use the 0-1 scale.",
        "",
        "## Canonical inferential model", "",
        "    try ~ utterance + prior + qud + rating_order + (1 | item)", "",
        "One linear mixed-effects model is fitted by REML using lmerTest/lme4. "
        "try maps to try_rating_01 and utterance maps to utterance_id. "
        "Reference levels are managed, low prior, TRY? QUD and TRY-first rating order. "
        "Item has package and photo levels and contributes a random intercept.",
        "",
        "Prior, QUD and rating order have common additive effects across all eight utterances.  "
        "Rating order compares completion-first (P?|TRY?|NAT) with TRY-first (TRY?|P?|NAT). "
        "Coefficients and planned contrasts use two-sided Wald-type t-tests with "
        "Satterthwaite degrees of freedom. Overall terms use Type II F-tests with "
        "Satterthwaite denominator degrees of freedom. **All p-values are unadjusted.** "
        "Group contrasts weight their utterances equally; the reported 95% intervals "
        "are pointwise t intervals.",
        "",
        "## Fit diagnostics", "",
        table(["n", "Fixed rank", "Item variance", "Item SD", "Residual SD", "ICC", "Singular"],
              [[fit["n"], f'{fit["fixed_rank"]}/{fit["fixed_columns"]}',
                fmt(fit["item_variance"], 8), fmt(fit["item_sd"], 6),
                fmt(fit["residual_sd"], 6), fmt(fit["icc"], 6), fit["singular"]]]),
        "",
        f'Optimizer: {fit["optimizer"]}; exit code: {fit["optimizer_code"]}. '
        f'Fit warnings: {fit["warning_count"]}. '
        "The two item levels provide limited information about the random-intercept variance.",
        "",
        "## Overall fixed effects", "",
        table(["Term", "NumDF", "DenDF", "F", "p"],
              [[r["term"], r["num_df"], fmt(r["den_df"], 3), fmt(r["F"]),
                fmt_p(r["p"])] for r in terms]),
        "",
    ]
    for heading, analyses in GROUPS:
        parts += [f"## {heading}", "",
            table(["Contrast", "Direction", "Estimate", "SE", "t", "df", "p", "95% CI"],
                [[name, index[name]["direction"], fmt(index[name]["estimate"]),
                  fmt(index[name]["se"]), fmt(index[name]["t"], 3),
                  fmt(index[name]["df"], 3), fmt_p(index[name]["p"]),
                  f'[{fmt(index[name]["ci95_low"])}, {fmt(index[name]["ci95_high"])}]']
                 for name in analyses]), ""]
    parts += [
        "## Fixed effect coefficients", "",
        table(["Term", "Estimate", "SE", "df", "t", "p"],
              [[r["term"], fmt(r["estimate"]), fmt(r["se"]), fmt(r["df"], 3),
                fmt(r["t"], 3), fmt_p(r["p"])] for r in coefs]), "",
        "## Descriptive TRY and completion ratings", "",
        "Descriptive means give equal weight to the item x prior x QUD x utterance "
        "design conditions represented in each summary. Question order is pooled "
        "within each cell except in summaries explicitly conditioned on order. "
        "Counts remain participant counts. SD is the condition-weighted mixture "
        "SD, including within-cell sample variance and between-cell mean differences. "
        "SE is sqrt(sum(s_cell^2/n_cell)/K^2), where K is the number of cells. "
        "Intermediate quantities retain full precision; tables round only displayed values.", "",
        table(["Utterance", "n", "TRY mean", "TRY SD", "Completion mean", "Completion SD"],
              [[r["utterance_id"], r["n"], fmt(r["try_mean"]), fmt(r["try_sd"]),
                fmt(r["completion_mean"]), fmt(r["completion_sd"])] for r in descriptive]), "",
        "## Descriptive naturalness ratings", "",
    ]
    nat_rows = []
    for u in UTTERANCES:
        stats = summarize_conditions([r for r in clean if r["utterance_id"] == u],
                                     "naturalness_rating_01", MAIN_CONDITIONS)
        nat_rows.append([u, str(stats["n"]), fmt(stats["mean"]),
                         fmt(stats["sd"]), fmt(stats["se"])])
    parts += [table(["Utterance", "n", "Mean", "SD", "SE"], nat_rows), "",
        "Naturalness, completion and within-utterance contextual summaries "
        "are descriptive. Their CSV outputs remain in results/results_main. "
        "Within-utterance descriptive differences should be distinguished from the "
        "shared contextual effects imposed by the additive model.", "",
        "## Reproduce", "",
        "    python code/run_all_analyses.py --rscript /path/to/Rscript", "",
        "The fitted object, model diagnostics, full-precision results, contrast weights "
        "and session information are in results/try_question_order.", ""]
    OUTPUT.write_text("\n".join(parts), encoding="utf-8")

if __name__ == "__main__":
    main()
