from __future__ import annotations

import argparse

from main_analysis_utils import (
    add_common_args,
    load_records,
    print_outputs,
    write_analysis_outputs,
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run optional single-item main-experiment screening and summaries. "
            "Use analyze_main_combined.py for the canonical analysis."
        )
    )
    add_common_args(parser)
    parser.add_argument(
        "--prefix",
        default="main_photo",
        help="Prefix for output CSV file names.",
    )
    parser.add_argument(
        "--item",
        default="photo",
        choices=["photo", "package"],
        help="Main experiment item to analyze.",
    )
    parser.add_argument(
        "--target-per-condition",
        type=int,
        default=15,
        help="Target clean N per local condition.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    records = load_records(args.data_dir)
    outputs = write_analysis_outputs(
        records=records,
        output_dir=args.output_dir,
        prefix=args.prefix,
        expected_item=args.item,
        target_per_condition=args.target_per_condition,
    )
    print_outputs(outputs)

if __name__ == "__main__":
    main()
