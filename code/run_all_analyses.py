#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = PROJECT_ROOT / "code"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Overwrite the canonical norming and main-experiment outputs, "
            "including the additive TRY mixed-effects model."
        )
    )
    parser.add_argument(
        "--rscript",
        default=os.environ.get("RSCRIPT", "Rscript"),
        help="Rscript executable name or path (default: RSCRIPT or Rscript).",
    )
    parser.add_argument(
        "--skip-r",
        action="store_true",
        help="Regenerate Python outputs without fitting the TRY mixed-effects model.",
    )
    return parser.parse_args()

def run(command: list[str]) -> None:
    print("\n+", " ".join(command), flush=True)
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)

def resolve_executable(value: str) -> str:
    explicit_path = Path(value).expanduser()
    if explicit_path.is_file():
        return str(explicit_path.resolve())
    resolved = shutil.which(value)
    if resolved:
        return resolved
    raise FileNotFoundError(
        f"Cannot find Rscript executable {value!r}. "
        "Install R/add Rscript to PATH, pass --rscript PATH, or use --skip-r."
    )

def main() -> None:
    args = parse_args()
    python = sys.executable

    run([python, str(CODE_DIR / "analyze_norming.py")])
    run([python, str(CODE_DIR / "analyze_main_combined.py")])

    if not args.skip_r:
        run(
            [
                resolve_executable(args.rscript), "--vanilla",
                str(PROJECT_ROOT / "results" / "try_question_order" / "analysis.R"),
            ]
        )
        run([python, str(CODE_DIR / "validate_analysis_outputs.py")])
        run([python, str(CODE_DIR / "generate_results_summary.py")])

    print("\nAnalyses completed successfully.")

if __name__ == "__main__":
    main()
