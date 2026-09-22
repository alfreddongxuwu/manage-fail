#!/usr/bin/env python3

from __future__ import annotations

import csv
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "results" / "results_main"
INFERENTIAL = ROOT / "results" / "try_question_order"
EXPECTED_FILES = {
    "try_planned_contrasts.csv", "model_coefficients.csv", "model_term_tests.csv",
    "model_fit_statistics.csv", "model_variance_components.csv", "contrast_weights.csv",
    "model_diagnostic_plots.png", "model.rds", "full_model_summary.txt",
    "RESULTS_SUMMARY.md", "session_info.txt", "analysis.R", "README.md",
    "rating_order_counts.csv", "validation.txt",
}
MODEL_NAME = "try_additive_random_item_question_order"
MODEL_FORMULA = "try ~ utterance + prior + qud + rating_order + (1 | item)"
EXPECTED_ANALYSES = {
    "prior_effect", "qud_effect", "prior_minus_qud_effect", "rating_order_effect",
    "implicative_boost_all_four_vs_did_and_didnt",
    "managed_minus_did", "didnt_fail_minus_did",
    "didnt_manage_minus_didnt", "failed_minus_didnt",
    "managed_and_didnt_fail_minus_did", "didnt_manage_and_failed_minus_didnt",
    "positive_outcome_grouped", "managed_minus_didnt_manage", "didnt_fail_minus_failed",
}
CONTRAST_COLUMNS = {
    "model", "family", "analysis", "direction", "estimate", "se", "df", "t",
    "p", "ci95_low", "ci95_high", "significant_05",
}

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)

def formula(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

def main() -> None:
    found = {p.name for p in INFERENTIAL.iterdir() if p.is_file()}
    require(found == EXPECTED_FILES,
            f"Unexpected inferential file set: missing={EXPECTED_FILES-found}, extra={found-EXPECTED_FILES}")
    for name in EXPECTED_FILES:
        require((INFERENTIAL / name).stat().st_size > 0, f"Empty output: {name}")
    main_rows = read_csv(MAIN / "main_combined_clean.csv")
    norming_rows = read_csv(ROOT / "results/results_norming/norming_clean.csv")
    require(bool(main_rows) and bool(norming_rows), "Empty clean data.")
    require(len({r["participant_uuid"] for r in main_rows}) == len(main_rows),
            "Duplicate main-experiment participants.")
    for label, rows in (("main", main_rows), ("norming", norming_rows)):
        for field in ("try_rating_01", "completion_rating_01"):
            require(field in rows[0], f"Missing {label} normalized column {field}")
        for field in (k for k in rows[0] if k.endswith("_rating_01")):
            for row in rows:
                if row[field] == "":
                    continue
                v = float(row[field])
                require(math.isfinite(v) and 0 <= v <= 1, f"Invalid {label}.{field}: {v}")
                raw = field.removesuffix("_01")
                require(math.isclose(v, float(row[raw]) / 100, abs_tol=1e-12),
                        f"Inconsistent scale: {label}.{field}")

    fits = read_csv(INFERENTIAL / "model_fit_statistics.csv")
    require(len(fits) == 1, "Exactly one inferential model is required.")
    fit = fits[0]
    require(fit["model_name"] == MODEL_NAME and formula(fit["formula"]) == MODEL_FORMULA,
            "Unexpected inferential model.")
    require(int(fit["n"]) == len(main_rows), "Model sample differs from clean data.")
    require(fit["REML"] == "TRUE", "Expected REML estimation.")
    require(int(fit["item_levels"]) == 2 and int(fit["fixed_columns"]) == 11
            and int(fit["fixed_rank"]) == 11, "Unexpected model design.")
    require(fit["optimizer_code"] == "0" and fit["convergence_messages"] == "",
            "Model has convergence problems.")

    order_counts = read_csv(INFERENTIAL / "rating_order_counts.csv")
    expected_counts = {(q, o): sum(r["qud"] == q and r["rating_order"] == o for r in main_rows)
                       for q in ("TRY?", "P?") for o in ("TRY?|P?|NAT", "P?|TRY?|NAT")}
    require(len(order_counts) == 4 and
            {(r["qud"], r["rating_order"]): int(r["Freq"]) for r in order_counts} == expected_counts,
            "Question-order counts differ from the clean data.")
    require(sum(expected_counts.values()) == len(main_rows) and all(expected_counts.values()),
            "Invalid or empty question-order conditions.")

    coefs = read_csv(INFERENTIAL / "model_coefficients.csv")
    require(len(coefs) == 11 and len({r["term"] for r in coefs}) == 11,
            "Expected eleven fixed-effect coefficients.")
    require(all(r["model_name"] == MODEL_NAME for r in coefs), "Unexpected coefficient model.")
    terms = read_csv(INFERENTIAL / "model_term_tests.csv")
    require(len(terms) == 4 and {r["term"] for r in terms} == {"utterance", "prior", "qud", "rating_order"},
            "Expected the four overall fixed-effect tests.")
    contrasts = read_csv(INFERENTIAL / "try_planned_contrasts.csv")
    require(len(contrasts) == 14 and {r["analysis"] for r in contrasts} == EXPECTED_ANALYSES,
            "Unexpected planned contrast set.")
    require(set(contrasts[0]) == CONTRAST_COLUMNS, "Unexpected contrast columns.")
    require(all(formula(r["model"]) == MODEL_FORMULA for r in contrasts),
            "Contrasts must come from the canonical model.")
    for row in coefs + contrasts:
        numeric = {k: float(row[k]) for k in ("estimate", "se", "df", "t", "p", "ci95_low", "ci95_high")}
        require(all(math.isfinite(v) for v in numeric.values()), "Non-finite test output.")
        require(numeric["se"] > 0 and numeric["df"] > 0 and 0 <= numeric["p"] <= 1,
                "Invalid test output.")
        require(math.isclose(numeric["t"], numeric["estimate"]/numeric["se"], abs_tol=1e-10),
                "Estimate, SE and t are inconsistent.")
        require(math.isclose((numeric["ci95_low"] + numeric["ci95_high"])/2,
                             numeric["estimate"], abs_tol=1e-10), "Asymmetric t interval.")
    for row in contrasts:
        require((row["significant_05"] == "TRUE") == (float(row["p"]) < .05),
                "Incorrect significance flag.")
    index = {r["analysis"]: r for r in contrasts}
    coef_index = {r["term"]: r for r in coefs}
    term_index = {r["term"]: r for r in terms}
    for name, coefficient in (("prior", "priorhigh"), ("qud", "qudP?"), ("rating_order", "rating_orderP?|TRY?|NAT")):
        c = index[f"{name}_effect"]
        b = coef_index[coefficient]
        f = term_index[name]
        require(math.isclose(float(c["estimate"]), float(b["estimate"]), abs_tol=1e-12),
                "Shared contextual effect differs from its coefficient.")
        require(math.isclose(float(f["F"]), float(b["t"])**2, rel_tol=1e-10),
                "Single-df F and t tests disagree.")
        require(math.isclose(float(c["p"]), float(b["p"]), rel_tol=1e-8, abs_tol=1e-14),
                "Contextual p-values disagree.")
    weights = read_csv(INFERENTIAL / "contrast_weights.csv")
    require(len(weights) == 14 and {r["analysis"] for r in weights} == EXPECTED_ANALYSES,
            "Unexpected contrast weight set.")
    require((INFERENTIAL / "model_diagnostic_plots.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n",
            "Invalid diagnostic PNG.")
    print(f"norming_clean_rows={len(norming_rows)}")
    print(f"main_clean_rows={len(main_rows)}")
    print("inferential_models=1")
    print(f"canonical_model={MODEL_FORMULA}")
    print("planned_contrasts=14; p_values=unadjusted; item=random_intercept")
    print(f"singular_fit={fit['singular']}")
    print("All canonical output checks passed.")

if __name__ == "__main__":
    main()
