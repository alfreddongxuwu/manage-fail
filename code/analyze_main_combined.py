from __future__ import annotations

import argparse
from pathlib import Path

import focused_descriptive_stats as descriptives
import main_analysis_utils as utils

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge photo and package main-experiment JSON files and write "
            "combined CSV summaries."
        )
    )
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--photo-data-dir",
        type=Path,
        default=root / "data" / "main" / "main_photo",
        help="Directory containing main photo participant-level JSON files.",
    )
    parser.add_argument(
        "--package-data-dir",
        type=Path,
        default=root / "data" / "main" / "main_package",
        help="Directory containing main package participant-level JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "results" / "results_main",
        help="Directory where combined CSV outputs will be written.",
    )
    parser.add_argument(
        "--prefix",
        default="main_combined",
        help="Prefix for output CSV file names.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    records = [
        *utils.load_records(args.photo_data_dir),
        *utils.load_records(args.package_data_dir),
    ]
    screened = utils.add_screening_and_analysis_columns_by_item(records)
    clean = utils.analysis_records(screened)
    analysis_excluded = [
        row for row in screened if row.get("analysis_status") == "exclude"
    ]

    outputs = {
        "clean_r_input": args.output_dir / f"{args.prefix}_clean.csv",
        "analysis_excluded": args.output_dir
        / f"{args.prefix}_analysis_excluded.csv",
        "screening_counts": args.output_dir
        / f"{args.prefix}_screening_counts.csv",
    }
    utils.write_csv(outputs["clean_r_input"], clean)
    utils.write_csv(outputs["analysis_excluded"], analysis_excluded)
    utils.write_csv(
        outputs["screening_counts"],
        utils.build_screening_counts(screened),
        ["category", "value", "n"],
    )

    outputs.update(
        descriptives.write_focused_descriptive_outputs(
            clean,
            args.output_dir,
            args.prefix,
        )
    )
    descriptives.remove_stale_prefixed_csvs(
        args.output_dir,
        args.prefix,
        list(outputs.values()),
    )
    utils.print_outputs(outputs)

if __name__ == "__main__":
    main()
