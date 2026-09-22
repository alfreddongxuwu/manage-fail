#!/usr/bin/env python3

from __future__ import annotations
import csv
from pathlib import Path
import focused_descriptive_stats as main
import norming_analysis_utils as norming

ROOT = Path(__file__).resolve().parents[1]

def read_clean(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for key, value in row.items():
            if key.endswith(("_rating_01", "_rt_ms")):
                row[key] = float(value) if value else None
    return rows

def main_run():
    output = ROOT / "results/results_main"
    clean = read_clean(output / "main_combined_clean.csv")
    paths = main.write_focused_descriptive_outputs(clean, output, "main_combined")
    output = ROOT / "results/results_norming"
    clean = read_clean(output / "norming_clean.csv")
    specs = (
        ("summary_long", norming.build_summary_long, norming.summary_long_fieldnames()),
        ("condition_summary", norming.build_condition_summary, norming.condition_summary_fieldnames()),
        ("question_order_prior_summary", norming.build_question_order_prior_summary,
         norming.question_order_prior_summary_fieldnames()),
        ("rt_summary", norming.build_rt_summary,
         ["rt_field", "n", "mean_ms", "sd_ms", "se_ms"]),
    )
    for suffix, builder, fields in specs:
        path = output / f"norming_{suffix}.csv"
        norming.write_csv(path, builder(clean), fields)
        paths["norming_" + suffix] = path
    for key, path in paths.items():
        print(f"{key}: {path.relative_to(ROOT)}")

if __name__ == "__main__":
    main_run()
