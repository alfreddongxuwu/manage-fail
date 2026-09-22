from __future__ import annotations

import argparse

from norming_analysis_utils import (
    add_common_args,
    load_records,
    print_outputs,
    write_analysis_outputs,
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge norming JSON files, screen language/residence exclusions, "
            "and write CSV summaries."
        )
    )
    add_common_args(parser)
    parser.add_argument(
        "--prefix",
        default="norming",
        help="Prefix for output CSV file names.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    records = load_records(args.data_dir)
    outputs = write_analysis_outputs(records, args.output_dir, args.prefix)
    print_outputs(outputs)

if __name__ == "__main__":
    main()
