from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from condition_averaging import NORMING_CONDITIONS, summarize_conditions

KNOWN_FIELDS = [
    "source_file",
    "participant_uuid",
    "study_version",
    "collection_mode",
    "prolific_pid",
    "prolific_study_id",
    "prolific_session_id",
    "assignment_source",
    "condition_id",
    "item",
    "prior",
    "consent_given",
    "consent_rt_ms",
    "instructions_rt_ms",
    "rating_rt_ms",
    "completion_rating",
    "completion_rating_01",
    "try_rating",
    "try_rating_01",
    "question_order",
    "demographics_rt_ms",
    "age",
    "gender",
    "education",
    "native_language",
    "country",
]

ENGLISH_NATIVE_LANGUAGE_VALUES = {"english-only", "english-and-other"}
ENGLISH_COUNTRY_VALUES = {
    "united-states",
    "united-kingdom",
    "canada",
    "australia",
    "new-zealand",
}

def default_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "norming"

def default_output_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "results" / "results_norming"

def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir(),
        help="Directory containing participant-level JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
        help="Directory where CSV outputs will be written.",
    )

def load_records(data_dir: Path) -> list[dict]:
    paths = sorted(data_dir.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"No JSON files found in {data_dir}")

    records = []
    for path in paths:
        with path.open("r", encoding="utf-8") as file:
            record = json.load(file)

        if not isinstance(record, dict):
            raise ValueError(f"{path} does not contain one JSON object")

        record = dict(record)
        record["source_file"] = path.name
        record["source_path"] = str(path)
        normalize_record(record)
        records.append(record)

    return records

def normalize_record(record: dict) -> None:
    if isinstance(record.get("question_order"), list):
        record["question_order"] = "|".join(str(value) for value in record["question_order"])

    for field in [
        "condition_id",
        "age",
        "consent_rt_ms",
        "instructions_rt_ms",
        "rating_rt_ms",
        "completion_rating",
        "try_rating",
        "demographics_rt_ms",
    ]:
        record[field] = numeric_or_none(record.get(field))

    for field in ("try_rating", "completion_rating"):
        value = record.get(field)
        record[f"{field}_01"] = None if value is None else value / 100

def numeric_or_none(value):
    if value is None or value == "":
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    if number.is_integer():
        return int(number)
    return number

def screening_reasons(record: dict) -> list[str]:
    reasons = []
    native_language = record.get("native_language")
    country = record.get("country")

    if native_language in (None, "", "prefer-not-to-say"):
        reasons.append("native_language_prefer_not_to_say_or_missing")
    elif native_language not in ENGLISH_NATIVE_LANGUAGE_VALUES:
        reasons.append("native_language_not_english")

    if country in (None, "", "prefer-not-to-say"):
        reasons.append("country_prefer_not_to_say_or_missing")
    elif country not in ENGLISH_COUNTRY_VALUES:
        reasons.append("country_not_english_country")

    return reasons

def add_screening_columns(records: list[dict]) -> list[dict]:
    screened = []
    for record in records:
        row = dict(record)
        reasons = screening_reasons(row)
        row["screening_status"] = "exclude" if reasons else "include"
        row["screening_reasons"] = ";".join(reasons)
        screened.append(row)
    return screened

def analysis_records(records: list[dict]) -> list[dict]:
    valid = []
    for record in records:
        if record.get("screening_status") != "include":
            continue
        if record.get("consent_given") is not True:
            continue
        if record.get("try_rating") is None or record.get("completion_rating") is None:
            continue
        valid.append(record)
    return valid

def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = infer_fieldnames(rows)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def infer_fieldnames(rows: list[dict]) -> list[str]:
    seen = set()
    for row in rows:
        seen.update(row.keys())

    ordered = [field for field in KNOWN_FIELDS if field in seen]
    ordered.extend(sorted(seen - set(ordered) - {"source_path"}))
    return ordered

def summarize_values(values: list[float | int]) -> dict:
    clean_values = [float(value) for value in values if value is not None]
    n = len(clean_values)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "se": None}
    if n == 1:
        return {"n": 1, "mean": mean(clean_values), "sd": None, "se": None}

    sd = stdev(clean_values)
    return {"n": n, "mean": mean(clean_values), "sd": sd, "se": sd / math.sqrt(n)}

def rounded(value):
    return "" if value is None else round(value, 4)

def summarize_measure(records: list[dict], measure: str) -> dict:

    if measure in ("try_rating", "completion_rating"):
        key = measure + "_01"
    elif measure == "try_minus_completion":
        key = lambda row: (row["try_rating_01"] - row["completion_rating_01"]
                           if row.get("try_rating_01") is not None and
                           row.get("completion_rating_01") is not None else None)
    elif measure == "participant_mean_rating":
        key = lambda row: ((row["try_rating_01"] + row["completion_rating_01"]) / 2
                           if row.get("try_rating_01") is not None and
                           row.get("completion_rating_01") is not None else None)
    else:
        raise ValueError(f"Unknown measure: {measure}")
    return summarize_conditions(records, key, NORMING_CONDITIONS)

def measure_values(records: list[dict], measure: str) -> list[float]:
    if measure == "try_rating":
        return [record["try_rating_01"] for record in records]
    if measure == "completion_rating":
        return [record["completion_rating_01"] for record in records]
    if measure == "try_minus_completion":
        return [
            record["try_rating_01"] - record["completion_rating_01"]
            for record in records
            if record.get("try_rating_01") is not None
            and record.get("completion_rating_01") is not None
        ]
    if measure == "participant_mean_rating":
        return [
            (record["try_rating_01"] + record["completion_rating_01"]) / 2
            for record in records
            if record.get("try_rating_01") is not None
            and record.get("completion_rating_01") is not None
        ]
    raise ValueError(f"Unknown measure: {measure}")

def summary_row(section: str, records: list[dict], measure: str, **labels) -> dict:
    stats = summarize_measure(records, measure)
    return {
        "section": section,
        "item": labels.get("item", "all"),
        "prior": labels.get("prior", "all"),
        "condition_id": labels.get("condition_id", ""),
        "measure": measure,
        "n": stats["n"],
        "mean": rounded(stats["mean"]),
        "sd": rounded(stats["sd"]),
        "se": rounded(stats["se"]),
    }

def grouped(records: list[dict], keys: tuple[str, ...]) -> dict[tuple, list[dict]]:
    groups = defaultdict(list)
    for record in records:
        groups[tuple(record.get(key) for key in keys)].append(record)
    return dict(groups)

def build_summary_long(records: list[dict]) -> list[dict]:
    rows = []
    measures = [
        "try_rating",
        "completion_rating",
        "try_minus_completion",
        "participant_mean_rating",
    ]

    for item, group_records in sorted(grouped(records, ("item",)).items()):
        for measure in measures:
            rows.append(
                summary_row(
                    "scenario_overall",
                    group_records,
                    measure,
                    item=item[0],
                )
            )

    for (item, prior), group_records in sorted(grouped(records, ("item", "prior")).items()):
        for measure in measures:
            rows.append(
                summary_row(
                    "scenario_by_prior",
                    group_records,
                    measure,
                    item=item,
                    prior=prior,
                )
            )

    for (prior,), group_records in sorted(grouped(records, ("prior",)).items()):
        for measure in measures:
            rows.append(
                summary_row(
                    "overall_by_prior",
                    group_records,
                    measure,
                    prior=prior,
                )
            )

    for (condition_id, item, prior), group_records in sorted(
        grouped(records, ("condition_id", "item", "prior")).items()
    ):
        for measure in measures:
            rows.append(
                summary_row(
                    "condition",
                    group_records,
                    measure,
                    condition_id=condition_id,
                    item=item,
                    prior=prior,
                )
            )

    for measure in measures:
        rows.append(summary_row("grand_total", records, measure))

    return rows

def build_condition_summary(records: list[dict]) -> list[dict]:
    rows = []
    for (condition_id, item, prior), group_records in sorted(
        grouped(records, ("condition_id", "item", "prior")).items()
    ):
        row = {
            "condition_id": condition_id,
            "item": item,
            "prior": prior,
            "n": len(group_records),
        }
        for label, measure in [
            ("try", "try_rating"),
            ("completion", "completion_rating"),
            ("try_minus_completion", "try_minus_completion"),
            ("participant_mean", "participant_mean_rating"),
        ]:
            stats = summarize_measure(group_records, measure)
            row[f"{label}_mean"] = rounded(stats["mean"])
            row[f"{label}_sd"] = rounded(stats["sd"])
            row[f"{label}_se"] = rounded(stats["se"])
        rows.append(row)
    return rows

def build_question_order_prior_summary(records: list[dict]) -> list[dict]:
    rows = []

    for (question_order, prior), group_records in sorted(
        grouped(records, ("question_order", "prior")).items()
    ):
        row = {
            "section": "overall_by_question_order_and_prior",
            "question_order": question_order_label(question_order),
            "question_order_raw": question_order,
            "condition_id": "",
            "item": "all",
            "prior": prior,
            "n": len(group_records),
        }
        add_wide_measure_stats(row, group_records)
        rows.append(row)

    for (question_order, condition_id, item, prior), group_records in sorted(
        grouped(records, ("question_order", "condition_id", "item", "prior")).items()
    ):
        row = {
            "section": "condition_by_question_order",
            "question_order": question_order_label(question_order),
            "question_order_raw": question_order,
            "condition_id": condition_id,
            "item": item,
            "prior": prior,
            "n": len(group_records),
        }
        add_wide_measure_stats(row, group_records)
        rows.append(row)

    return rows

def add_wide_measure_stats(row: dict, records: list[dict]) -> None:
    for label, measure in [
        ("try", "try_rating"),
        ("completion", "completion_rating"),
        ("try_minus_completion", "try_minus_completion"),
        ("participant_mean", "participant_mean_rating"),
    ]:
        stats = summarize_measure(records, measure)
        row[f"{label}_mean"] = rounded(stats["mean"])
        row[f"{label}_sd"] = rounded(stats["sd"])
        row[f"{label}_se"] = rounded(stats["se"])

def question_order_label(question_order: str) -> str:
    labels = {
        "try|completion": "try-do",
        "completion|try": "do-try",
    }
    return labels.get(question_order, question_order or "missing")

def build_screening_counts(records: list[dict]) -> list[dict]:
    reason_counts = Counter()
    status_counts = Counter(record.get("screening_status") for record in records)

    for record in records:
        reasons = record.get("screening_reasons", "")
        if reasons:
            reason_counts.update(reasons.split(";"))

    rows = [
        {"category": "status", "value": status, "n": count}
        for status, count in sorted(status_counts.items())
    ]
    rows.extend(
        {"category": "exclude_reason", "value": reason, "n": count}
        for reason, count in sorted(reason_counts.items())
    )
    return rows

def build_question_order_counts(records: list[dict]) -> list[dict]:
    counts = Counter(record.get("question_order", "") for record in records)
    return [
        {"question_order": question_order, "n": count}
        for question_order, count in sorted(counts.items())
    ]

def build_rt_summary(records: list[dict]) -> list[dict]:
    rows = []
    for field in [
        "consent_rt_ms",
        "instructions_rt_ms",
        "rating_rt_ms",
        "demographics_rt_ms",
    ]:
        stats = summarize_conditions(records, field, NORMING_CONDITIONS)
        rows.append(
            {
                "rt_field": field,
                "n": stats["n"],
                "mean_ms": rounded(stats["mean"]),
                "sd_ms": rounded(stats["sd"]),
                "se_ms": rounded(stats["se"]),
            }
        )
    return rows

def write_analysis_outputs(records: list[dict], output_dir: Path, prefix: str) -> dict[str, Path]:
    screened = add_screening_columns(records)
    clean = analysis_records(screened)
    excluded = [record for record in screened if record.get("screening_status") == "exclude"]

    outputs = {
        "raw": output_dir / f"{prefix}_merged_raw.csv",
        "screened": output_dir / f"{prefix}_screened_all.csv",
        "excluded": output_dir / f"{prefix}_excluded_language_residence.csv",
        "clean": output_dir / f"{prefix}_clean.csv",
        "summary_long": output_dir / f"{prefix}_summary_long.csv",
        "condition_summary": output_dir / f"{prefix}_condition_summary.csv",
        "screening_counts": output_dir / f"{prefix}_screening_counts.csv",
        "question_order_counts": output_dir / f"{prefix}_question_order_counts.csv",
        "question_order_prior_summary": output_dir / f"{prefix}_question_order_prior_summary.csv",
        "rt_summary": output_dir / f"{prefix}_rt_summary.csv",
    }

    write_csv(outputs["raw"], records)
    write_csv(outputs["screened"], screened)
    write_csv(outputs["excluded"], excluded)
    write_csv(outputs["clean"], clean)
    write_csv(outputs["summary_long"], build_summary_long(clean), summary_long_fieldnames())
    write_csv(
        outputs["condition_summary"],
        build_condition_summary(clean),
        condition_summary_fieldnames(),
    )
    write_csv(
        outputs["screening_counts"],
        build_screening_counts(screened),
        ["category", "value", "n"],
    )
    write_csv(
        outputs["question_order_counts"],
        build_question_order_counts(clean),
        ["question_order", "n"],
    )
    write_csv(
        outputs["question_order_prior_summary"],
        build_question_order_prior_summary(clean),
        question_order_prior_summary_fieldnames(),
    )
    write_csv(
        outputs["rt_summary"],
        build_rt_summary(clean),
        ["rt_field", "n", "mean_ms", "sd_ms", "se_ms"],
    )

    return outputs

def summary_long_fieldnames() -> list[str]:
    return ["section", "item", "prior", "condition_id", "measure", "n", "mean", "sd", "se"]

def condition_summary_fieldnames() -> list[str]:
    return [
        "condition_id",
        "item",
        "prior",
        "n",
        "try_mean",
        "try_sd",
        "try_se",
        "completion_mean",
        "completion_sd",
        "completion_se",
        "try_minus_completion_mean",
        "try_minus_completion_sd",
        "try_minus_completion_se",
        "participant_mean_mean",
        "participant_mean_sd",
        "participant_mean_se",
    ]

def question_order_prior_summary_fieldnames() -> list[str]:
    return [
        "section",
        "question_order",
        "question_order_raw",
        "condition_id",
        "item",
        "prior",
        "n",
        "try_mean",
        "try_sd",
        "try_se",
        "completion_mean",
        "completion_sd",
        "completion_se",
        "try_minus_completion_mean",
        "try_minus_completion_sd",
        "try_minus_completion_se",
        "participant_mean_mean",
        "participant_mean_sd",
        "participant_mean_se",
    ]

def print_outputs(outputs: dict[str, Path]) -> None:
    for label, path in outputs.items():
        print(f"{label}: {path}")
