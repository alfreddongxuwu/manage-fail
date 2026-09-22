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
from condition_averaging import MAIN_CONDITIONS, summarize_conditions

EXPECTED_ITEM = "photo"
EXPECTED_CONDITION_COUNT = 32
EXPECTED_TOTAL_N = 480
ITEMS = ["photo", "package"]
COMBINED_ITEM_LABEL = "all_items"

PRIORS = ["high", "low"]
QUDS = ["P?", "TRY?"]
UTTERANCES = [
    {
        "utterance_id": "managed",
        "utterance_family": "manage",
        "utterance_polarity": "positive",
        "is_implicative": True,
    },
    {
        "utterance_id": "didnt_manage",
        "utterance_family": "manage",
        "utterance_polarity": "negative",
        "is_implicative": True,
    },
    {
        "utterance_id": "failed",
        "utterance_family": "fail",
        "utterance_polarity": "positive",
        "is_implicative": True,
    },
    {
        "utterance_id": "didnt_fail",
        "utterance_family": "fail",
        "utterance_polarity": "negative",
        "is_implicative": True,
    },
    {
        "utterance_id": "did",
        "utterance_family": "simple",
        "utterance_polarity": "positive",
        "is_implicative": False,
    },
    {
        "utterance_id": "didnt",
        "utterance_family": "simple",
        "utterance_polarity": "negative",
        "is_implicative": False,
    },
    {
        "utterance_id": "tried",
        "utterance_family": "try",
        "utterance_polarity": "positive",
        "is_implicative": False,
    },
    {
        "utterance_id": "didnt_try",
        "utterance_family": "try",
        "utterance_polarity": "negative",
        "is_implicative": False,
    },
]

ENGLISH_NATIVE_LANGUAGE_VALUES = {"english-only", "english-and-other"}
ENGLISH_COUNTRY_VALUES = {
    "united-states",
    "united-kingdom",
    "canada",
    "australia",
    "new-zealand",
}

KNOWN_FIELDS = [
    "source_file",
    "participant_uuid",
    "study",
    "study_version",
    "collection_mode",
    "prolific_pid",
    "prolific_study_id",
    "prolific_session_id",
    "assignment_source",
    "item_route",
    "local_condition_id",
    "global_condition_id",
    "item",
    "prior",
    "qud",
    "utterance_id",
    "utterance_family",
    "utterance_polarity",
    "is_implicative",
    "consent_given",
    "consent_rt_ms",
    "instructions_rt_ms",
    "ratings_rt_ms",
    "rating_order",
    "try_rating",
    "try_rating_01",
    "completion_rating",
    "completion_rating_01",
    "naturalness_rating",
    "naturalness_rating_01",
    "demographics_rt_ms",
    "age",
    "gender",
    "education",
    "native_language",
    "country",
    "screening_reasons",
    "screening_status",
    "analysis_exclusion_reasons",
    "analysis_status",
]

REQUIRED_ANALYSIS_FIELDS = [
    "participant_uuid",
    "study",
    "study_version",
    "collection_mode",
    "prolific_pid",
    "prolific_study_id",
    "prolific_session_id",
    "assignment_source",
    "item_route",
    "local_condition_id",
    "global_condition_id",
    "item",
    "prior",
    "qud",
    "utterance_id",
    "utterance_family",
    "utterance_polarity",
    "is_implicative",
    "consent_given",
    "try_rating",
    "completion_rating",
    "naturalness_rating",
    "rating_order",
    "age",
    "gender",
    "education",
    "native_language",
    "country",
]

RATING_FIELDS = ["try_rating", "completion_rating", "naturalness_rating"]
NORMALIZED_RATING_FIELDS = {field: f"{field}_01" for field in RATING_FIELDS}
RT_FIELDS = ["consent_rt_ms", "instructions_rt_ms", "ratings_rt_ms", "demographics_rt_ms"]
MEASURES = ["try_rating", "completion_rating", "naturalness_rating", "try_minus_completion"]

POSITIVE_COMPLETION_UTTERANCES = {"managed", "did", "didnt_fail"}
NEGATIVE_COMPLETION_UTTERANCES = {"didnt_manage", "didnt", "failed"}

REDUNDANT_DESCRIPTIVE_SUFFIXES = (
    "utterance_try_rating",
    "utterance_naturalness_rating",
    "utterance_qud_prior_effects",
    "implicative_qud_order_try_contrast",
)

def default_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "main" / "main_photo"

def default_output_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "results" / "results_main_photo"

def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir(),
        help="Directory containing main photo participant-level JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
        help="Directory where CSV outputs will be written.",
    )

def global_condition_offset(expected_item: str) -> int:
    if expected_item == "package":
        return len(PRIORS) * len(QUDS) * len(UTTERANCES)
    return 0

def expected_conditions(expected_item: str = EXPECTED_ITEM) -> list[dict]:
    rows = []
    global_offset = global_condition_offset(expected_item)
    for prior_index, prior in enumerate(PRIORS):
        for qud_index, qud in enumerate(QUDS):
            for utterance_index, utterance in enumerate(UTTERANCES):
                local_condition_id = (
                    prior_index * len(QUDS) * len(UTTERANCES)
                    + qud_index * len(UTTERANCES)
                    + utterance_index
                )
                rows.append(
                    {
                        "local_condition_id": local_condition_id,
                        "global_condition_id": global_offset + local_condition_id,
                        "item": expected_item,
                        "prior": prior,
                        "qud": qud,
                        **utterance,
                    }
                )
    return rows

def expected_condition_by_id(expected_item: str = EXPECTED_ITEM) -> dict[int, dict]:
    return {
        row["local_condition_id"]: row
        for row in expected_conditions(expected_item)
    }

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
    if isinstance(record.get("rating_order"), list):
        record["rating_order"] = "|".join(str(value) for value in record["rating_order"])

    for field in [
        "local_condition_id",
        "global_condition_id",
        "age",
        "consent_rt_ms",
        "instructions_rt_ms",
        "ratings_rt_ms",
        "rating_rt_ms",
        "try_rating",
        "completion_rating",
        "naturalness_rating",
        "demographics_rt_ms",
    ]:
        if field in record:
            record[field] = numeric_or_none(record.get(field))

    record["consent_given"] = bool_or_original(record.get("consent_given"))
    record["is_implicative"] = bool_or_original(record.get("is_implicative"))

    if record.get("ratings_rt_ms") is None and record.get("rating_rt_ms") is not None:
        record["ratings_rt_ms"] = record.get("rating_rt_ms")

    for field, normalized_field in NORMALIZED_RATING_FIELDS.items():
        value = record.get(field)
        record[normalized_field] = None if value is None else value / 100

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

def bool_or_original(value):
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    return value

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

def structural_reasons(record: dict, expected_item: str) -> list[str]:
    reasons = []
    condition_id = record.get("local_condition_id")
    expected_by_id = expected_condition_by_id(expected_item)

    if record.get("study") not in ("main-experiment", None):
        reasons.append("study_not_main_experiment")
    if record.get("collection_mode") != "main":
        reasons.append("collection_mode_not_main")
    if record.get("item_route") != expected_item:
        reasons.append("item_route_mismatch")
    if record.get("item") != expected_item:
        reasons.append("item_mismatch")
    if condition_id not in expected_by_id:
        reasons.append("local_condition_id_invalid")
    elif condition_metadata_mismatch(record, expected_by_id[condition_id]):
        reasons.append("condition_metadata_mismatch")

    return reasons

def condition_metadata_mismatch(record: dict, expected: dict) -> bool:
    for field in [
        "global_condition_id",
        "item",
        "prior",
        "qud",
        "utterance_id",
        "utterance_family",
        "utterance_polarity",
        "is_implicative",
    ]:
        value = record.get(field)
        if value is not None and value != expected[field]:
            return True
    return False

def rating_reasons(record: dict) -> list[str]:
    reasons = []
    for field in RATING_FIELDS:
        value = record.get(field)
        if value is None:
            reasons.append(f"{field}_missing")
        elif value < 0 or value > 100:
            reasons.append(f"{field}_out_of_range")
    return reasons

def missing_required_fields(record: dict) -> list[str]:
    return [
        field
        for field in REQUIRED_ANALYSIS_FIELDS
        if record.get(field) is None or record.get(field) == ""
    ]

def add_screening_and_analysis_columns(records: list[dict], expected_item: str) -> list[dict]:
    return [screen_record(record, expected_item) for record in records]

def add_screening_and_analysis_columns_by_item(records: list[dict]) -> list[dict]:
    return [
        screen_record(record, expected_item_for_record(record))
        for record in records
    ]

def expected_item_for_record(record: dict) -> str:
    item = record.get("item_route") or record.get("item")
    if item in ITEMS:
        return item
    return item or EXPECTED_ITEM

def screen_record(record: dict, expected_item: str) -> dict:
    row = dict(record)
    language_reasons = screening_reasons(row)
    exclusion_reasons = []

    exclusion_reasons.extend(language_reasons)
    exclusion_reasons.extend(structural_reasons(row, expected_item))
    exclusion_reasons.extend(rating_reasons(row))

    if row.get("consent_given") is not True:
        exclusion_reasons.append("consent_not_true")

    row["screening_status"] = "exclude" if language_reasons else "include"
    row["screening_reasons"] = ";".join(language_reasons)
    row["analysis_status"] = "exclude" if exclusion_reasons else "include"
    row["analysis_exclusion_reasons"] = ";".join(exclusion_reasons)
    return row

def analysis_records(records: list[dict]) -> list[dict]:
    return [record for record in records if record.get("analysis_status") == "include"]

def remove_redundant_descriptive_outputs(output_dir: Path, prefix: str) -> None:
    for suffix in REDUNDANT_DESCRIPTIVE_SUFFIXES:
        path = output_dir / f"{prefix}_{suffix}.csv"
        path.unlink(missing_ok=True)

def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = infer_fieldnames(rows)

    fieldnames = output_fieldnames(fieldnames)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def output_fieldnames(fieldnames: list[str]) -> list[str]:
    return fieldnames

def is_uncertainty_field(field: str) -> bool:
    return (
        field in {"sd", "se", "sd_ms", "se_ms"}
        or field.endswith("_sd")
        or field.endswith("_se")
    )

def infer_fieldnames(rows: list[dict]) -> list[str]:
    seen = set()
    for row in rows:
        seen.update(row.keys())

    ordered = [field for field in KNOWN_FIELDS if field in seen]
    ordered.extend(sorted(seen - set(ordered) - {"source_path", "rating_rt_ms"}))
    return ordered

def summarize_values(values: list[float | int]) -> dict:
    clean_values = [float(value) for value in values if value is not None]
    n = len(clean_values)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "se": None, "min": None, "max": None}
    if n == 1:
        value = clean_values[0]
        return {"n": 1, "mean": value, "sd": None, "se": None, "min": value, "max": value}

    sd = stdev(clean_values)
    return {
        "n": n,
        "mean": mean(clean_values),
        "sd": sd,
        "se": sd / math.sqrt(n),
        "min": min(clean_values),
        "max": max(clean_values),
    }

def rounded(value):
    return "" if value is None else round(value, 4)

def summarize_measure(records: list[dict], measure: str) -> dict:

    if measure in RATING_FIELDS:
        key = NORMALIZED_RATING_FIELDS[measure]
    elif measure == "try_minus_completion":
        key = lambda row: (row["try_rating_01"] - row["completion_rating_01"]
                           if row.get("try_rating_01") is not None and
                           row.get("completion_rating_01") is not None else None)
    else:
        raise ValueError(f"Unknown measure: {measure}")
    return summarize_conditions(records, key, MAIN_CONDITIONS)

def measure_values(records: list[dict], measure: str) -> list[float]:
    if measure in RATING_FIELDS:
        normalized_measure = NORMALIZED_RATING_FIELDS[measure]
        return [record.get(normalized_measure) for record in records]
    if measure == "try_minus_completion":
        return [
            record["try_rating_01"] - record["completion_rating_01"]
            for record in records
            if record.get("try_rating_01") is not None
            and record.get("completion_rating_01") is not None
        ]
    raise ValueError(f"Unknown measure: {measure}")

def grouped(records: list[dict], keys: tuple[str, ...]) -> dict[tuple, list[dict]]:
    groups = defaultdict(list)
    for record in records:
        groups[tuple(record.get(key) for key in keys)].append(record)
    return dict(groups)

def sort_tuple_key(values: tuple) -> tuple:
    return tuple("" if value is None else str(value) for value in values)

def summary_row(section: str, records: list[dict], measure: str, **labels) -> dict:
    stats = summarize_measure(records, measure)
    return {
        "section": section,
        "item": labels.get("item", EXPECTED_ITEM),
        "prior": labels.get("prior", "all"),
        "qud": labels.get("qud", "all"),
        "utterance_id": labels.get("utterance_id", "all"),
        "utterance_family": labels.get("utterance_family", "all"),
        "utterance_polarity": labels.get("utterance_polarity", "all"),
        "is_implicative": labels.get("is_implicative", "all"),
        "local_condition_id": labels.get("local_condition_id", ""),
        "measure": measure,
        "n": stats["n"],
        "mean": rounded(stats["mean"]),
        "sd": rounded(stats["sd"]),
        "se": rounded(stats["se"]),
    }

def build_summary_long(records: list[dict], expected_item: str) -> list[dict]:
    rows = []

    for measure in MEASURES:
        rows.append(summary_row("grand_total", records, measure, item=expected_item))

    grouping_specs = [
        ("by_prior", ("prior",)),
        ("by_qud", ("qud",)),
        (
            "by_utterance",
            ("utterance_id", "utterance_family", "utterance_polarity", "is_implicative"),
        ),
        ("by_prior_qud", ("prior", "qud")),
        (
            "by_prior_utterance",
            ("prior", "utterance_id", "utterance_family", "utterance_polarity", "is_implicative"),
        ),
        (
            "by_qud_utterance",
            ("qud", "utterance_id", "utterance_family", "utterance_polarity", "is_implicative"),
        ),
        (
            "condition",
            (
                "local_condition_id",
                "prior",
                "qud",
                "utterance_id",
                "utterance_family",
                "utterance_polarity",
                "is_implicative",
            ),
        ),
    ]

    for section, keys in grouping_specs:
        for group_key, group_records in sorted(
            grouped(records, keys).items(),
            key=lambda item: sort_tuple_key(item[0]),
        ):
            labels = dict(zip(keys, group_key))
            labels["item"] = expected_item
            for measure in MEASURES:
                rows.append(summary_row(section, group_records, measure, **labels))

    return rows

def build_summary_long_combined(records: list[dict]) -> list[dict]:
    rows = []

    for measure in MEASURES:
        rows.append(
            summary_row("grand_total", records, measure, item=COMBINED_ITEM_LABEL)
        )

    grouping_specs = [
        ("by_item", ("item",)),
        ("by_prior", ("prior",)),
        ("by_qud", ("qud",)),
        (
            "by_utterance",
            ("utterance_id", "utterance_family", "utterance_polarity", "is_implicative"),
        ),
        ("by_item_prior", ("item", "prior")),
        ("by_item_qud", ("item", "qud")),
        ("by_prior_qud", ("prior", "qud")),
        (
            "by_item_utterance",
            ("item", "utterance_id", "utterance_family", "utterance_polarity", "is_implicative"),
        ),
        (
            "by_prior_utterance",
            ("prior", "utterance_id", "utterance_family", "utterance_polarity", "is_implicative"),
        ),
        (
            "by_qud_utterance",
            ("qud", "utterance_id", "utterance_family", "utterance_polarity", "is_implicative"),
        ),
        (
            "condition",
            (
                "item",
                "local_condition_id",
                "prior",
                "qud",
                "utterance_id",
                "utterance_family",
                "utterance_polarity",
                "is_implicative",
            ),
        ),
    ]

    for section, keys in grouping_specs:
        for group_key, group_records in sorted(
            grouped(records, keys).items(),
            key=lambda item: sort_tuple_key(item[0]),
        ):
            labels = dict(zip(keys, group_key))
            if "item" not in labels:
                labels["item"] = COMBINED_ITEM_LABEL
            for measure in MEASURES:
                rows.append(summary_row(section, group_records, measure, **labels))

    return rows

def build_condition_counts(
    screened_records: list[dict],
    expected_item: str,
    target_per_condition: int,
) -> list[dict]:
    expected_by_id = expected_condition_by_id(expected_item)
    raw_counts = Counter(record.get("local_condition_id") for record in screened_records)
    clean_counts = Counter(
        record.get("local_condition_id")
        for record in screened_records
        if record.get("analysis_status") == "include"
    )
    language_excluded_counts = Counter(
        record.get("local_condition_id")
        for record in screened_records
        if record.get("screening_status") == "exclude"
    )
    analysis_excluded_counts = Counter(
        record.get("local_condition_id")
        for record in screened_records
        if record.get("analysis_status") == "exclude"
    )

    rows = []
    for condition_id, expected in expected_by_id.items():
        clean_n = clean_counts[condition_id]
        rows.append(
            {
                **expected,
                "n_raw": raw_counts[condition_id],
                "n_clean": clean_n,
                "n_language_excluded": language_excluded_counts[condition_id],
                "n_analysis_excluded": analysis_excluded_counts[condition_id],
                "target_n": target_per_condition,
                "remaining_to_target": max(target_per_condition - clean_n, 0),
                "over_target": max(clean_n - target_per_condition, 0),
            }
        )

    invalid_raw = sum(
        count for condition_id, count in raw_counts.items() if condition_id not in expected_by_id
    )
    if invalid_raw:
        rows.append(
            {
                "local_condition_id": "invalid_or_missing",
                "global_condition_id": "",
                "item": expected_item,
                "prior": "",
                "qud": "",
                "utterance_id": "",
                "utterance_family": "",
                "utterance_polarity": "",
                "is_implicative": "",
                "n_raw": invalid_raw,
                "n_clean": 0,
                "n_language_excluded": 0,
                "n_analysis_excluded": invalid_raw,
                "target_n": "",
                "remaining_to_target": "",
                "over_target": "",
            }
        )

    return rows

def build_condition_counts_by_item(
    screened_records: list[dict],
    target_per_condition: int,
) -> list[dict]:
    expected_rows = [
        expected
        for item in ITEMS
        for expected in expected_conditions(item)
    ]
    expected_by_key = {
        (expected["item"], expected["local_condition_id"]): expected
        for expected in expected_rows
    }
    raw_counts = Counter(record_condition_key(record) for record in screened_records)
    clean_counts = Counter(
        record_condition_key(record)
        for record in screened_records
        if record.get("analysis_status") == "include"
    )
    language_excluded_counts = Counter(
        record_condition_key(record)
        for record in screened_records
        if record.get("screening_status") == "exclude"
    )
    analysis_excluded_counts = Counter(
        record_condition_key(record)
        for record in screened_records
        if record.get("analysis_status") == "exclude"
    )

    rows = []
    for expected in expected_rows:
        key = (expected["item"], expected["local_condition_id"])
        clean_n = clean_counts[key]
        rows.append(
            {
                **expected,
                "n_raw": raw_counts[key],
                "n_clean": clean_n,
                "n_language_excluded": language_excluded_counts[key],
                "n_analysis_excluded": analysis_excluded_counts[key],
                "target_n": target_per_condition,
                "remaining_to_target": max(target_per_condition - clean_n, 0),
                "over_target": max(clean_n - target_per_condition, 0),
            }
        )

    invalid_raw = sum(
        count for key, count in raw_counts.items() if key not in expected_by_key
    )
    if invalid_raw:
        rows.append(
            {
                "local_condition_id": "invalid_or_missing",
                "global_condition_id": "",
                "item": "invalid_or_missing",
                "prior": "",
                "qud": "",
                "utterance_id": "",
                "utterance_family": "",
                "utterance_polarity": "",
                "is_implicative": "",
                "n_raw": invalid_raw,
                "n_clean": 0,
                "n_language_excluded": 0,
                "n_analysis_excluded": invalid_raw,
                "target_n": "",
                "remaining_to_target": "",
                "over_target": "",
            }
        )

    return rows

def record_condition_key(record: dict) -> tuple:
    return (record.get("item"), record.get("local_condition_id"))

def build_condition_summary(
    clean_records: list[dict],
    expected_item: str,
    target_per_condition: int,
) -> list[dict]:
    condition_records = grouped(clean_records, ("local_condition_id",))
    rows = []
    for expected in expected_conditions(expected_item):
        condition_id = expected["local_condition_id"]
        records = condition_records.get((condition_id,), [])
        row = {
            **expected,
            "n": len(records),
            "target_n": target_per_condition,
            "remaining_to_target": max(target_per_condition - len(records), 0),
        }
        add_wide_measure_stats(row, records)
        rows.append(row)
    return rows

def build_condition_summary_by_item(
    clean_records: list[dict],
    target_per_condition: int,
) -> list[dict]:
    condition_records = grouped(clean_records, ("item", "local_condition_id"))
    rows = []
    for item in ITEMS:
        for expected in expected_conditions(item):
            key = (expected["item"], expected["local_condition_id"])
            records = condition_records.get(key, [])
            row = {
                **expected,
                "n": len(records),
                "target_n": target_per_condition,
                "remaining_to_target": max(target_per_condition - len(records), 0),
            }
            add_wide_measure_stats(row, records)
            rows.append(row)
    return rows

def add_wide_measure_stats(row: dict, records: list[dict]) -> None:
    for label, measure in [
        ("try", "try_rating"),
        ("completion", "completion_rating"),
        ("naturalness", "naturalness_rating"),
        ("try_minus_completion", "try_minus_completion"),
    ]:
        stats = summarize_measure(records, measure)
        row[f"{label}_mean"] = rounded(stats["mean"])
        row[f"{label}_sd"] = rounded(stats["sd"])
        row[f"{label}_se"] = rounded(stats["se"])

def build_quality_flags(records: list[dict], expected_item: str | None) -> list[dict]:
    prolific_pid_counts = Counter(record.get("prolific_pid") for record in records)
    prolific_session_counts = Counter(record.get("prolific_session_id") for record in records)

    rows = []
    for record in records:
        rating_values = [record.get(field) for field in RATING_FIELDS]
        numeric_ratings = [value for value in rating_values if value is not None]
        missing_fields = missing_required_fields(record)
        duplicate_pid = (
            record.get("prolific_pid") not in (None, "")
            and prolific_pid_counts[record.get("prolific_pid")] > 1
        )
        duplicate_session = (
            record.get("prolific_session_id") not in (None, "")
            and prolific_session_counts[record.get("prolific_session_id")] > 1
        )
        total_rt = total_task_rt_ms(record)

        rows.append(
            {
                "source_file": record.get("source_file"),
                "participant_uuid": record.get("participant_uuid"),
                "prolific_pid": record.get("prolific_pid"),
                "prolific_session_id": record.get("prolific_session_id"),
                "local_condition_id": record.get("local_condition_id"),
                "item": record.get("item"),
                "prior": record.get("prior"),
                "qud": record.get("qud"),
                "utterance_id": record.get("utterance_id"),
                "screening_status": record.get("screening_status"),
                "analysis_status": record.get("analysis_status"),
                "screening_reasons": record.get("screening_reasons", ""),
                "analysis_exclusion_reasons": record.get("analysis_exclusion_reasons", ""),
                "missing_required_fields": ";".join(missing_fields),
                "duplicate_prolific_pid": duplicate_pid,
                "duplicate_prolific_session_id": duplicate_session,
                "invalid_condition": "local_condition_id_invalid"
                in record.get("analysis_exclusion_reasons", ""),
                "condition_metadata_mismatch": "condition_metadata_mismatch"
                in record.get("analysis_exclusion_reasons", ""),
                "wrong_item": record.get("item") != (
                    expected_item if expected_item is not None else expected_item_for_record(record)
                ),
                "any_rating_missing": any(value is None for value in rating_values),
                "any_rating_out_of_range": any(
                    value is not None and (value < 0 or value > 100)
                    for value in rating_values
                ),
                "all_three_ratings_equal": len(numeric_ratings) == 3
                and len(set(numeric_ratings)) == 1,
                "all_three_ratings_at_endpoint": len(numeric_ratings) == 3
                and all(value in (0, 100) for value in numeric_ratings),
                "low_naturalness_under_20": record.get("naturalness_rating") is not None
                and record.get("naturalness_rating") < 20,
                "ratings_rt_under_5000ms": record.get("ratings_rt_ms") is not None
                and record.get("ratings_rt_ms") < 5000,
                "total_task_rt_under_30000ms": total_rt is not None and total_rt < 30000,
                "total_task_rt_ms": total_rt if total_rt is not None else "",
            }
        )
    return rows

def total_task_rt_ms(record: dict):
    values = [record.get(field) for field in RT_FIELDS]
    if any(value is None for value in values):
        return None
    return sum(values)

def build_rating_order_summary(records: list[dict], expected_item: str) -> list[dict]:
    rows = []
    specs = [
        ("overall", ("rating_order",)),
        ("by_prior", ("rating_order", "prior")),
        ("by_qud", ("rating_order", "qud")),
        ("by_prior_qud", ("rating_order", "prior", "qud")),
    ]

    for section, keys in specs:
        for group_key, group_records in sorted(
            grouped(records, keys).items(),
            key=lambda item: sort_tuple_key(item[0]),
        ):
            labels = dict(zip(keys, group_key))
            row = {
                "section": section,
                "rating_order": labels.get("rating_order") or "missing",
                "item": expected_item,
                "prior": labels.get("prior", "all"),
                "qud": labels.get("qud", "all"),
                "n": len(group_records),
            }
            add_wide_measure_stats(row, group_records)
            rows.append(row)

    return rows

def build_rating_order_summary_combined(records: list[dict]) -> list[dict]:
    rows = []
    specs = [
        ("overall", ("rating_order",)),
        ("by_item", ("rating_order", "item")),
        ("by_prior", ("rating_order", "prior")),
        ("by_qud", ("rating_order", "qud")),
        ("by_item_prior", ("rating_order", "item", "prior")),
        ("by_item_qud", ("rating_order", "item", "qud")),
        ("by_prior_qud", ("rating_order", "prior", "qud")),
        ("by_item_prior_qud", ("rating_order", "item", "prior", "qud")),
    ]

    for section, keys in specs:
        for group_key, group_records in sorted(
            grouped(records, keys).items(),
            key=lambda item: sort_tuple_key(item[0]),
        ):
            labels = dict(zip(keys, group_key))
            row = {
                "section": section,
                "rating_order": labels.get("rating_order") or "missing",
                "item": labels.get("item", COMBINED_ITEM_LABEL),
                "prior": labels.get("prior", "all"),
                "qud": labels.get("qud", "all"),
                "n": len(group_records),
            }
            add_wide_measure_stats(row, group_records)
            rows.append(row)

    return rows

def build_utterance_try_rating_summary(records: list[dict], expected_item: str) -> list[dict]:
    rows = []
    for utterance in UTTERANCES:
        utterance_id = utterance["utterance_id"]
        group_records = [
            record
            for record in records
            if record.get("utterance_id") == utterance_id
        ]
        try_stats = summarize_measure(group_records, "try_rating")
        completion_stats = summarize_measure(group_records, "completion_rating")
        rows.append(
            {
                "item": expected_item,
                "utterance_id": utterance_id,
                "utterance_family": utterance["utterance_family"],
                "utterance_polarity": utterance["utterance_polarity"],
                "is_implicative": utterance["is_implicative"],
                "n": try_stats["n"],
                "try_mean": rounded(try_stats["mean"]),
                "try_sd": rounded(try_stats["sd"]),
                "try_se": rounded(try_stats["se"]),
                "completion_mean": rounded(completion_stats["mean"]),
                "completion_sd": rounded(completion_stats["sd"]),
                "completion_se": rounded(completion_stats["se"]),
            }
        )
    return rows

def build_utterance_naturalness_rating_summary(
    records: list[dict],
    expected_item: str,
) -> list[dict]:
    rows = []
    for utterance in UTTERANCES:
        utterance_id = utterance["utterance_id"]
        group_records = [
            record
            for record in records
            if record.get("utterance_id") == utterance_id
        ]
        stats = summarize_measure(group_records, "naturalness_rating")
        rows.append(
            {
                "item": expected_item,
                "utterance_id": utterance_id,
                "utterance_family": utterance["utterance_family"],
                "utterance_polarity": utterance["utterance_polarity"],
                "is_implicative": utterance["is_implicative"],
                "n": stats["n"],
                "naturalness_mean": rounded(stats["mean"]),
                "naturalness_sd": rounded(stats["sd"]),
                "naturalness_se": rounded(stats["se"]),
            }
        )
    return rows

def build_utterance_try_by_prior_summary(
    records: list[dict],
    expected_item: str,
) -> list[dict]:
    rows = []
    for utterance in UTTERANCES:
        utterance_id = utterance["utterance_id"]
        row = {
            "item": expected_item,
            "utterance_id": utterance_id,
            "utterance_family": utterance["utterance_family"],
            "utterance_polarity": utterance["utterance_polarity"],
            "is_implicative": utterance["is_implicative"],
        }
        for prior in PRIORS:
            group_records = [
                record
                for record in records
                if record.get("utterance_id") == utterance_id
                and record.get("prior") == prior
            ]
            stats = summarize_measure(group_records, "try_rating")
            row[f"{prior}_n"] = stats["n"]
            row[f"{prior}_try_mean"] = rounded(stats["mean"])
            row[f"{prior}_try_sd"] = rounded(stats["sd"])
            row[f"{prior}_try_se"] = rounded(stats["se"])
        rows.append(row)
    return rows

def build_utterance_try_by_qud_summary(
    records: list[dict],
    expected_item: str,
) -> list[dict]:
    rows = []
    for utterance in UTTERANCES:
        utterance_id = utterance["utterance_id"]
        qud_means = {}
        row = {
            "item": expected_item,
            "utterance_id": utterance_id,
            "utterance_family": utterance["utterance_family"],
            "utterance_polarity": utterance["utterance_polarity"],
            "is_implicative": utterance["is_implicative"],
        }
        for qud in QUDS:
            prefix = "try_qud" if qud == "TRY?" else "p_qud"
            group_records = [
                record
                for record in records
                if record.get("utterance_id") == utterance_id
                and record.get("qud") == qud
            ]
            stats = summarize_measure(group_records, "try_rating")
            row[f"{prefix}_n"] = stats["n"]
            row[f"{prefix}_try_mean"] = rounded(stats["mean"])
            qud_means[qud] = stats["mean"]
            row[f"{prefix}_try_sd"] = rounded(stats["sd"])
            row[f"{prefix}_try_se"] = rounded(stats["se"])
        mean_diff = None
        if qud_means.get("P?") is not None and qud_means.get("TRY?") is not None:
            mean_diff = qud_means["P?"] - qud_means["TRY?"]
        row["p_qud_minus_try_qud_try_mean"] = rounded(mean_diff)
        rows.append(row)
    return rows

def build_utterance_qud_prior_effects(
    records: list[dict],
    expected_item: str,
) -> list[dict]:
    rows = []
    for utterance in UTTERANCES:
        utterance_id = utterance["utterance_id"]
        utterance_records = [
            record
            for record in records
            if record.get("utterance_id") == utterance_id
        ]
        high_stats = summarize_measure([
                    record
                    for record in utterance_records
                    if record.get("prior") == "high"
                ], "try_rating")
        low_stats = summarize_measure([
                    record
                    for record in utterance_records
                    if record.get("prior") == "low"
                ], "try_rating")
        try_qud_stats = summarize_measure([
                    record
                    for record in utterance_records
                    if record.get("qud") == "TRY?"
                ], "try_rating")
        p_qud_stats = summarize_measure([
                    record
                    for record in utterance_records
                    if record.get("qud") == "P?"
                ], "try_rating")

        prior_diff = None
        if high_stats["mean"] is not None and low_stats["mean"] is not None:
            prior_diff = high_stats["mean"] - low_stats["mean"]

        qud_diff = None
        if p_qud_stats["mean"] is not None and try_qud_stats["mean"] is not None:
            qud_diff = p_qud_stats["mean"] - try_qud_stats["mean"]

        rows.append(
            {
                "item": expected_item,
                "utterance_id": utterance_id,
                "utterance_family": utterance["utterance_family"],
                "utterance_polarity": utterance["utterance_polarity"],
                "is_implicative": utterance["is_implicative"],
                "measure": "try_rating",
                "high_n": high_stats["n"],
                "high_try_mean": rounded(high_stats["mean"]),
                "low_n": low_stats["n"],
                "low_try_mean": rounded(low_stats["mean"]),
                "high_minus_low_try_mean": rounded(prior_diff),
                "try_qud_n": try_qud_stats["n"],
                "try_qud_try_mean": rounded(try_qud_stats["mean"]),
                "p_qud_n": p_qud_stats["n"],
                "p_qud_try_mean": rounded(p_qud_stats["mean"]),
                "p_qud_minus_try_qud_try_mean": rounded(qud_diff),
            }
        )
    return rows

def rating_order_matches_qud(record: dict) -> bool:
    return (
        record.get("qud") == "TRY?"
        and record.get("rating_order") == "TRY?|P?|NAT"
    ) or (
        record.get("qud") == "P?"
        and record.get("rating_order") == "P?|TRY?|NAT"
    )

def build_qud_order_match_counts(records: list[dict], expected_item: str) -> list[dict]:
    rows = []
    total_n = len(records)
    matched_records = [record for record in records if rating_order_matches_qud(record)]
    mismatched_records = [
        record for record in records if not rating_order_matches_qud(record)
    ]

    for label, group_records in [
        ("matched", matched_records),
        ("not_matched", mismatched_records),
    ]:
        rows.append(
            {
                "section": "overall",
                "item": expected_item,
                "qud": "all",
                "rating_order": "all",
                "qud_order_match": label,
                "n": len(group_records),
                "percent_clean": rounded(
                    100 * len(group_records) / total_n if total_n else None
                ),
            }
        )

    for group_key, group_records in sorted(
        grouped(records, ("qud", "rating_order")).items(),
        key=lambda item: sort_tuple_key(item[0]),
    ):
        qud, rating_order = group_key
        qud_order_match = (
            (qud == "TRY?" and rating_order == "TRY?|P?|NAT")
            or (qud == "P?" and rating_order == "P?|TRY?|NAT")
        )
        rows.append(
            {
                "section": "by_qud_rating_order",
                "item": expected_item,
                "qud": qud or "missing",
                "rating_order": rating_order or "missing",
                "qud_order_match": "matched" if qud_order_match else "not_matched",
                "n": len(group_records),
                "percent_clean": rounded(
                    100 * len(group_records) / total_n if total_n else None
                ),
            }
        )
    return rows

def build_qud_order_matched_effects(
    records: list[dict],
    expected_item: str,
) -> list[dict]:
    matched_records = [record for record in records if rating_order_matches_qud(record)]
    rows = []

    def add_row(section: str, group_records: list[dict], labels: dict) -> None:
        try_qud_records = [
            record for record in group_records if record.get("qud") == "TRY?"
        ]
        p_qud_records = [
            record for record in group_records if record.get("qud") == "P?"
        ]
        try_qud_stats = summarize_measure(try_qud_records, "try_rating")
        p_qud_stats = summarize_measure(p_qud_records, "try_rating")
        mean_diff = None
        if p_qud_stats["mean"] is not None and try_qud_stats["mean"] is not None:
            mean_diff = p_qud_stats["mean"] - try_qud_stats["mean"]

        rows.append(
            {
                "section": section,
                "item": expected_item,
                **labels,
                "measure": "try_rating",
                "matched_n": len(group_records),
                "p_qud": "P?",
                "p_qud_rating_order": "P?|TRY?|NAT",
                "p_qud_n": p_qud_stats["n"],
                "p_qud_try_mean": rounded(p_qud_stats["mean"]),
                "p_qud_try_sd": rounded(p_qud_stats["sd"]),
                "p_qud_try_se": rounded(p_qud_stats["se"]),
                "try_qud": "TRY?",
                "try_qud_rating_order": "TRY?|P?|NAT",
                "try_qud_n": try_qud_stats["n"],
                "try_qud_try_mean": rounded(try_qud_stats["mean"]),
                "try_qud_try_sd": rounded(try_qud_stats["sd"]),
                "try_qud_try_se": rounded(try_qud_stats["se"]),
                "p_qud_minus_try_qud_try_mean": rounded(mean_diff),
            }
        )

    implicative_records = [
        record for record in matched_records if record.get("is_implicative") is True
    ]
    add_row(
        "overall_implicatives",
        implicative_records,
        {
            "utterance_id": "all_implicatives",
            "utterance_family": "all",
            "utterance_polarity": "all",
            "is_implicative": True,
        },
    )

    for utterance in UTTERANCES:
        utterance_id = utterance["utterance_id"]
        add_row(
            "by_utterance",
            [
                record
                for record in matched_records
                if record.get("utterance_id") == utterance_id
            ],
            {
                "utterance_id": utterance_id,
                "utterance_family": utterance["utterance_family"],
                "utterance_polarity": utterance["utterance_polarity"],
                "is_implicative": utterance["is_implicative"],
            },
        )
    return rows

def build_implicative_qud_order_try_contrast(
    records: list[dict],
    expected_item: str,
) -> list[dict]:
    rows = []
    implicative_utterances = [
        utterance for utterance in UTTERANCES if utterance["is_implicative"] is True
    ]

    def add_row(section: str, utterance: dict | None = None) -> None:
        if utterance is None:
            base_records = [
                record for record in records if record.get("is_implicative") is True
            ]
            utterance_labels = {
                "utterance_id": "all_implicatives",
                "utterance_family": "all",
                "utterance_polarity": "all",
            }
        else:
            utterance_id = utterance["utterance_id"]
            base_records = [
                record
                for record in records
                if record.get("utterance_id") == utterance_id
            ]
            utterance_labels = {
                "utterance_id": utterance_id,
                "utterance_family": utterance["utterance_family"],
                "utterance_polarity": utterance["utterance_polarity"],
            }

        at_issue_records = [
            record
            for record in base_records
            if record.get("qud") == "TRY?"
            and record.get("rating_order") == "TRY?|P?|NAT"
        ]
        not_at_issue_records = [
            record
            for record in base_records
            if record.get("qud") == "P?"
            and record.get("rating_order") == "P?|TRY?|NAT"
        ]
        at_issue_stats = summarize_measure(at_issue_records, "try_rating")
        not_at_issue_stats = summarize_measure(not_at_issue_records, "try_rating")
        mean_diff = None
        if at_issue_stats["mean"] is not None and not_at_issue_stats["mean"] is not None:
            mean_diff = not_at_issue_stats["mean"] - at_issue_stats["mean"]

        rows.append(
            {
                "section": section,
                "item": expected_item,
                **utterance_labels,
                "measure": "try_rating",
                "at_issue_qud": "TRY?",
                "at_issue_rating_order": "TRY?|P?|NAT",
                "at_issue_n": at_issue_stats["n"],
                "at_issue_try_mean": rounded(at_issue_stats["mean"]),
                "at_issue_try_sd": rounded(at_issue_stats["sd"]),
                "at_issue_try_se": rounded(at_issue_stats["se"]),
                "not_at_issue_qud": "P?",
                "not_at_issue_rating_order": "P?|TRY?|NAT",
                "not_at_issue_n": not_at_issue_stats["n"],
                "not_at_issue_try_mean": rounded(not_at_issue_stats["mean"]),
                "not_at_issue_try_sd": rounded(not_at_issue_stats["sd"]),
                "not_at_issue_try_se": rounded(not_at_issue_stats["se"]),
                "p_qud_minus_try_qud_try_mean": rounded(mean_diff),
            }
        )

    add_row("overall_implicatives")
    for utterance in implicative_utterances:
        add_row("by_implicative_utterance", utterance)
    return rows

def build_core_try_effects(records: list[dict]) -> list[dict]:
    implicative_records = [
        record
        for record in records
        if record.get("is_implicative") is True
    ]

    return [
        compact_try_contrast(
            contrast="prior_effect_collapsing_implicatives",
            left_label="high",
            right_label="low",
            left_records=[
                record for record in implicative_records if record.get("prior") == "high"
            ],
            right_records=[
                record for record in implicative_records if record.get("prior") == "low"
            ],
        ),
        compact_try_contrast(
            contrast="qud_effect_p_qud_minus_try_qud_collapsing_implicatives",
            left_label="P?",
            right_label="TRY?",
            left_records=[
                record for record in implicative_records if record.get("qud") == "P?"
            ],
            right_records=[
                record for record in implicative_records if record.get("qud") == "TRY?"
            ],
        ),
        matched_utterance_try_contrast(records, "managed", "did"),
        matched_utterance_try_contrast(records, "didnt_fail", "did"),
        matched_utterance_try_contrast(records, "failed", "didnt"),
        matched_utterance_try_contrast(records, "didnt_manage", "didnt"),
    ]

def matched_utterance_try_contrast(
    records: list[dict],
    left_utterance_id: str,
    right_utterance_id: str,
) -> dict:
    return compact_try_contrast(
        contrast=f"{left_utterance_id}_minus_{right_utterance_id}",
        left_label=left_utterance_id,
        right_label=right_utterance_id,
        left_records=[
            record for record in records if record.get("utterance_id") == left_utterance_id
        ],
        right_records=[
            record for record in records if record.get("utterance_id") == right_utterance_id
        ],
    )

def compact_try_contrast(
    contrast: str,
    left_label: str,
    right_label: str,
    left_records: list[dict],
    right_records: list[dict],
) -> dict:
    left_stats = summarize_measure(left_records, "try_rating")
    right_stats = summarize_measure(right_records, "try_rating")
    left_mean = left_stats["mean"]
    right_mean = right_stats["mean"]
    mean_diff = None
    if left_mean is not None and right_mean is not None:
        mean_diff = left_mean - right_mean

    return {
        "contrast": contrast,
        "measure": "try_rating",
        "left_group": left_label,
        "right_group": right_label,
        "left_n": left_stats["n"],
        "left_mean": rounded(left_mean),
        "right_n": right_stats["n"],
        "right_mean": rounded(right_mean),
        "mean_diff": rounded(mean_diff),
    }

def build_rt_summary(records: list[dict]) -> list[dict]:
    rows = []
    for field in [*RT_FIELDS, "total_task_rt_ms"]:
        key = total_task_rt_ms if field == "total_task_rt_ms" else field
        stats = summarize_conditions(records, key, MAIN_CONDITIONS)
        rows.append(
            {
                "rt_field": field,
                "n": stats["n"],
                "mean_ms": rounded(stats["mean"]),
                "sd_ms": rounded(stats["sd"]),
                "se_ms": rounded(stats["se"]),
                "min_ms": rounded(stats["min"]),
                "max_ms": rounded(stats["max"]),
            }
        )
    return rows

def build_screening_counts(records: list[dict]) -> list[dict]:
    rows = []
    for field in ["screening_status", "analysis_status"]:
        counts = Counter(record.get(field) for record in records)
        rows.extend(
            {"category": field, "value": value, "n": count}
            for value, count in sorted(counts.items())
        )

    reason_counts = Counter()
    for record in records:
        reasons = record.get("analysis_exclusion_reasons", "")
        if reasons:
            reason_counts.update(reasons.split(";"))

    rows.extend(
        {"category": "analysis_exclusion_reason", "value": reason, "n": count}
        for reason, count in sorted(reason_counts.items())
    )
    return rows

def write_analysis_outputs(
    records: list[dict],
    output_dir: Path,
    prefix: str,
    expected_item: str,
    target_per_condition: int,
) -> dict[str, Path]:
    screened = add_screening_and_analysis_columns(records, expected_item)
    clean = analysis_records(screened)
    excluded_language = [
        record for record in screened if record.get("screening_status") == "exclude"
    ]

    remove_redundant_descriptive_outputs(output_dir, prefix)
    outputs = {
        "raw": output_dir / f"{prefix}_merged_raw.csv",
        "screened": output_dir / f"{prefix}_screened_all.csv",
        "excluded": output_dir / f"{prefix}_excluded_language_residence.csv",
        "clean": output_dir / f"{prefix}_clean.csv",
        "condition_counts": output_dir / f"{prefix}_condition_counts.csv",
        "condition_summary": output_dir / f"{prefix}_condition_summary.csv",
        "summary_long": output_dir / f"{prefix}_summary_long.csv",
        "quality_flags": output_dir / f"{prefix}_quality_flags.csv",
        "rating_order_summary": output_dir / f"{prefix}_rating_order_summary.csv",
        "utterance_try_by_prior": output_dir / f"{prefix}_utterance_try_by_prior.csv",
        "utterance_try_by_qud": output_dir / f"{prefix}_utterance_try_by_qud.csv",
        "qud_order_match_counts": output_dir
        / f"{prefix}_qud_order_match_counts.csv",
        "qud_order_matched_effects": output_dir
        / f"{prefix}_qud_order_matched_effects.csv",
        "core_try_effects": output_dir / f"{prefix}_core_try_effects.csv",
        "rt_summary": output_dir / f"{prefix}_rt_summary.csv",
        "screening_counts": output_dir / f"{prefix}_screening_counts.csv",
    }

    write_csv(outputs["raw"], records)
    write_csv(outputs["screened"], screened)
    write_csv(outputs["excluded"], excluded_language)
    write_csv(outputs["clean"], clean)
    write_csv(
        outputs["condition_counts"],
        build_condition_counts(screened, expected_item, target_per_condition),
        condition_counts_fieldnames(),
    )
    write_csv(
        outputs["condition_summary"],
        build_condition_summary(clean, expected_item, target_per_condition),
        condition_summary_fieldnames(),
    )
    write_csv(
        outputs["summary_long"],
        build_summary_long(clean, expected_item),
        summary_long_fieldnames(),
    )
    write_csv(
        outputs["quality_flags"],
        build_quality_flags(screened, expected_item),
        quality_flags_fieldnames(),
    )
    write_csv(
        outputs["rating_order_summary"],
        build_rating_order_summary(clean, expected_item),
        rating_order_summary_fieldnames(),
    )
    write_csv(
        outputs["utterance_try_by_prior"],
        build_utterance_try_by_prior_summary(clean, expected_item),
        utterance_try_by_prior_fieldnames(),
    )
    write_csv(
        outputs["utterance_try_by_qud"],
        build_utterance_try_by_qud_summary(clean, expected_item),
        utterance_try_by_qud_fieldnames(),
    )
    write_csv(
        outputs["qud_order_match_counts"],
        build_qud_order_match_counts(clean, expected_item),
        qud_order_match_counts_fieldnames(),
    )
    write_csv(
        outputs["qud_order_matched_effects"],
        build_qud_order_matched_effects(clean, expected_item),
        qud_order_matched_effects_fieldnames(),
    )
    write_csv(
        outputs["core_try_effects"],
        build_core_try_effects(clean),
        core_try_effects_fieldnames(),
    )
    write_csv(
        outputs["rt_summary"],
        build_rt_summary(clean),
        ["rt_field", "n", "mean_ms", "sd_ms", "se_ms", "min_ms", "max_ms"],
    )
    write_csv(
        outputs["screening_counts"],
        build_screening_counts(screened),
        ["category", "value", "n"],
    )

    return outputs

def write_combined_analysis_outputs(
    records: list[dict],
    output_dir: Path,
    prefix: str,
    target_per_condition: int,
) -> dict[str, Path]:
    screened = add_screening_and_analysis_columns_by_item(records)
    clean = analysis_records(screened)
    excluded_language = [
        record for record in screened if record.get("screening_status") == "exclude"
    ]

    remove_redundant_descriptive_outputs(output_dir, prefix)
    outputs = {
        "raw": output_dir / f"{prefix}_merged_raw.csv",
        "screened": output_dir / f"{prefix}_screened_all.csv",
        "excluded": output_dir / f"{prefix}_excluded_language_residence.csv",
        "clean": output_dir / f"{prefix}_clean.csv",
        "condition_counts": output_dir / f"{prefix}_condition_counts.csv",
        "condition_summary": output_dir / f"{prefix}_condition_summary.csv",
        "summary_long": output_dir / f"{prefix}_summary_long.csv",
        "quality_flags": output_dir / f"{prefix}_quality_flags.csv",
        "rating_order_summary": output_dir / f"{prefix}_rating_order_summary.csv",
        "utterance_try_by_prior": output_dir / f"{prefix}_utterance_try_by_prior.csv",
        "utterance_try_by_qud": output_dir / f"{prefix}_utterance_try_by_qud.csv",
        "qud_order_match_counts": output_dir
        / f"{prefix}_qud_order_match_counts.csv",
        "qud_order_matched_effects": output_dir
        / f"{prefix}_qud_order_matched_effects.csv",
        "core_try_effects": output_dir / f"{prefix}_core_try_effects.csv",
        "rt_summary": output_dir / f"{prefix}_rt_summary.csv",
        "screening_counts": output_dir / f"{prefix}_screening_counts.csv",
    }

    write_csv(outputs["raw"], records)
    write_csv(outputs["screened"], screened)
    write_csv(outputs["excluded"], excluded_language)
    write_csv(outputs["clean"], clean)
    write_csv(
        outputs["condition_counts"],
        build_condition_counts_by_item(screened, target_per_condition),
        condition_counts_fieldnames(),
    )
    write_csv(
        outputs["condition_summary"],
        build_condition_summary_by_item(clean, target_per_condition),
        condition_summary_fieldnames(),
    )
    write_csv(
        outputs["summary_long"],
        build_summary_long_combined(clean),
        summary_long_fieldnames(),
    )
    write_csv(
        outputs["quality_flags"],
        build_quality_flags(screened, None),
        quality_flags_fieldnames(),
    )
    write_csv(
        outputs["rating_order_summary"],
        build_rating_order_summary_combined(clean),
        rating_order_summary_fieldnames(),
    )
    write_csv(
        outputs["utterance_try_by_prior"],
        build_utterance_try_by_prior_summary(clean, COMBINED_ITEM_LABEL),
        utterance_try_by_prior_fieldnames(),
    )
    write_csv(
        outputs["utterance_try_by_qud"],
        build_utterance_try_by_qud_summary(clean, COMBINED_ITEM_LABEL),
        utterance_try_by_qud_fieldnames(),
    )
    write_csv(
        outputs["qud_order_match_counts"],
        build_qud_order_match_counts(clean, COMBINED_ITEM_LABEL),
        qud_order_match_counts_fieldnames(),
    )
    write_csv(
        outputs["qud_order_matched_effects"],
        build_qud_order_matched_effects(clean, COMBINED_ITEM_LABEL),
        qud_order_matched_effects_fieldnames(),
    )
    write_csv(
        outputs["core_try_effects"],
        build_core_try_effects(clean),
        core_try_effects_fieldnames(),
    )
    write_csv(
        outputs["rt_summary"],
        build_rt_summary(clean),
        ["rt_field", "n", "mean_ms", "sd_ms", "se_ms", "min_ms", "max_ms"],
    )
    write_csv(
        outputs["screening_counts"],
        build_screening_counts(screened),
        ["category", "value", "n"],
    )

    return outputs

def condition_metadata_fieldnames() -> list[str]:
    return [
        "local_condition_id",
        "global_condition_id",
        "item",
        "prior",
        "qud",
        "utterance_id",
        "utterance_family",
        "utterance_polarity",
        "is_implicative",
    ]

def condition_counts_fieldnames() -> list[str]:
    return [
        *condition_metadata_fieldnames(),
        "n_raw",
        "n_clean",
        "n_language_excluded",
        "n_analysis_excluded",
        "target_n",
        "remaining_to_target",
        "over_target",
    ]

def condition_summary_fieldnames() -> list[str]:
    return [
        *condition_metadata_fieldnames(),
        "n",
        "target_n",
        "remaining_to_target",
        "try_mean",
        "try_sd",
        "try_se",
        "completion_mean",
        "completion_sd",
        "completion_se",
        "naturalness_mean",
        "naturalness_sd",
        "naturalness_se",
        "try_minus_completion_mean",
        "try_minus_completion_sd",
        "try_minus_completion_se",
    ]

def summary_long_fieldnames() -> list[str]:
    return [
        "section",
        "item",
        "prior",
        "qud",
        "utterance_id",
        "utterance_family",
        "utterance_polarity",
        "is_implicative",
        "local_condition_id",
        "measure",
        "n",
        "mean",
        "sd",
        "se",
    ]

def quality_flags_fieldnames() -> list[str]:
    return [
        "source_file",
        "participant_uuid",
        "prolific_pid",
        "prolific_session_id",
        "local_condition_id",
        "item",
        "prior",
        "qud",
        "utterance_id",
        "screening_status",
        "analysis_status",
        "screening_reasons",
        "analysis_exclusion_reasons",
        "missing_required_fields",
        "duplicate_prolific_pid",
        "duplicate_prolific_session_id",
        "invalid_condition",
        "condition_metadata_mismatch",
        "wrong_item",
        "any_rating_missing",
        "any_rating_out_of_range",
        "all_three_ratings_equal",
        "all_three_ratings_at_endpoint",
        "low_naturalness_under_20",
        "ratings_rt_under_5000ms",
        "total_task_rt_under_30000ms",
        "total_task_rt_ms",
    ]

def rating_order_summary_fieldnames() -> list[str]:
    return [
        "section",
        "rating_order",
        "item",
        "prior",
        "qud",
        "n",
        "try_mean",
        "try_sd",
        "try_se",
        "completion_mean",
        "completion_sd",
        "completion_se",
        "naturalness_mean",
        "naturalness_sd",
        "naturalness_se",
        "try_minus_completion_mean",
        "try_minus_completion_sd",
        "try_minus_completion_se",
    ]

def utterance_try_rating_fieldnames() -> list[str]:
    return [
        "item",
        "utterance_id",
        "utterance_family",
        "utterance_polarity",
        "is_implicative",
        "n",
        "try_mean",
        "try_sd",
        "try_se",
        "completion_mean",
        "completion_sd",
        "completion_se",
    ]

def utterance_naturalness_rating_fieldnames() -> list[str]:
    return [
        "item",
        "utterance_id",
        "utterance_family",
        "utterance_polarity",
        "is_implicative",
        "n",
        "naturalness_mean",
        "naturalness_sd",
        "naturalness_se",
    ]

def utterance_try_by_prior_fieldnames() -> list[str]:
    return [
        "item",
        "utterance_id",
        "utterance_family",
        "utterance_polarity",
        "is_implicative",
        "high_n",
        "high_try_mean",
        "high_try_sd",
        "high_try_se",
        "low_n",
        "low_try_mean",
        "low_try_sd",
        "low_try_se",
    ]

def utterance_try_by_qud_fieldnames() -> list[str]:
    return [
        "item",
        "utterance_id",
        "utterance_family",
        "utterance_polarity",
        "is_implicative",
        "p_qud_n",
        "p_qud_try_mean",
        "p_qud_try_sd",
        "p_qud_try_se",
        "try_qud_n",
        "try_qud_try_mean",
        "try_qud_try_sd",
        "try_qud_try_se",
        "p_qud_minus_try_qud_try_mean",
    ]

def utterance_qud_prior_effects_fieldnames() -> list[str]:
    return [
        "item",
        "utterance_id",
        "utterance_family",
        "utterance_polarity",
        "is_implicative",
        "measure",
        "high_n",
        "high_try_mean",
        "low_n",
        "low_try_mean",
        "high_minus_low_try_mean",
        "p_qud_n",
        "p_qud_try_mean",
        "try_qud_n",
        "try_qud_try_mean",
        "p_qud_minus_try_qud_try_mean",
    ]

def qud_order_match_counts_fieldnames() -> list[str]:
    return [
        "section",
        "item",
        "qud",
        "rating_order",
        "qud_order_match",
        "n",
        "percent_clean",
    ]

def qud_order_matched_effects_fieldnames() -> list[str]:
    return [
        "section",
        "item",
        "utterance_id",
        "utterance_family",
        "utterance_polarity",
        "is_implicative",
        "measure",
        "matched_n",
        "p_qud",
        "p_qud_rating_order",
        "p_qud_n",
        "p_qud_try_mean",
        "p_qud_try_sd",
        "p_qud_try_se",
        "try_qud",
        "try_qud_rating_order",
        "try_qud_n",
        "try_qud_try_mean",
        "try_qud_try_sd",
        "try_qud_try_se",
        "p_qud_minus_try_qud_try_mean",
    ]

def implicative_qud_order_try_contrast_fieldnames() -> list[str]:
    return [
        "section",
        "item",
        "utterance_id",
        "utterance_family",
        "utterance_polarity",
        "measure",
        "at_issue_qud",
        "at_issue_rating_order",
        "at_issue_n",
        "at_issue_try_mean",
        "at_issue_try_sd",
        "at_issue_try_se",
        "not_at_issue_qud",
        "not_at_issue_rating_order",
        "not_at_issue_n",
        "not_at_issue_try_mean",
        "not_at_issue_try_sd",
        "not_at_issue_try_se",
        "p_qud_minus_try_qud_try_mean",
    ]

def core_try_effects_fieldnames() -> list[str]:
    return [
        "contrast",
        "measure",
        "left_group",
        "right_group",
        "left_n",
        "left_mean",
        "right_n",
        "right_mean",
        "mean_diff",
    ]

def print_outputs(outputs: dict[str, Path]) -> None:
    for label, path in outputs.items():
        print(f"{label}: {path}")
