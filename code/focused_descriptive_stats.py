from __future__ import annotations

from pathlib import Path

import main_analysis_utils as utils

IMPLICATIVE_IDS = ("managed", "didnt_manage", "failed", "didnt_fail")
SIMPLE_BASELINE_IDS = ("did", "didnt")
BOOST_PAIRS = (
    ("managed", "did"),
    ("didnt_fail", "did"),
    ("didnt_manage", "didnt"),
    ("failed", "didnt"),
)
GROUPED_BOOSTS = (
    (
        "managed_and_didnt_fail_minus_did",
        ("managed", "didnt_fail"),
        ("did",),
    ),
    (
        "didnt_manage_and_failed_minus_didnt",
        ("didnt_manage", "failed"),
        ("didnt",),
    ),
)
POSITIVE_OUTCOME_CONTRASTS = (
    (
        "positive_outcome_grouped",
        ("managed", "didnt_fail"),
        ("didnt_manage", "failed"),
    ),
    ("managed_minus_didnt_manage", ("managed",), ("didnt_manage",)),
    ("didnt_fail_minus_failed", ("didnt_fail",), ("failed",)),
)
P_FIRST_ORDER = "P?|TRY?|NAT"
TRY_FIRST_ORDER = "TRY?|P?|NAT"

OVERALL_EFFECT_FIELDS = [
    "effect",
    "scope",
    "measure",
    "direction",
    "target_group",
    "target_n",
    "target_mean",
    "reference_group",
    "reference_n",
    "reference_mean",
    "effect_estimate",
]
PRIOR_EFFECT_FIELDS = [
    "utterance_id",
    "measure",
    "direction",
    "high_n",
    "high_try_mean",
    "low_n",
    "low_try_mean",
    "high_minus_low_try_mean",
]
QUD_EFFECT_FIELDS = [
    "utterance_id",
    "measure",
    "direction",
    "p_qud_n",
    "p_qud_try_mean",
    "try_qud_n",
    "try_qud_try_mean",
    "p_qud_minus_try_qud_try_mean",
]
TRY_MEAN_BY_UTTERANCE_FIELDS = [
    "utterance_id",
    "n",
    "try_mean",
    "try_sd",
    "completion_mean",
    "completion_sd",
]
BOOST_FIELDS = [
    "contrast",
    "measure",
    "direction",
    "implicative_utterance",
    "implicative_n",
    "implicative_try_mean",
    "baseline_utterance",
    "baseline_n",
    "baseline_try_mean",
    "implicative_minus_baseline_try_mean",
]
GROUPED_BOOST_FIELDS = [
    "contrast",
    "target_utterances",
    "target_n",
    "target_try_mean",
    "target_try_sd",
    "baseline_utterances",
    "baseline_n",
    "baseline_try_mean",
    "baseline_try_sd",
    "target_minus_baseline_try_mean",
]
POSITIVE_OUTCOME_FIELDS = [
    "contrast",
    "positive_utterances",
    "positive_n",
    "positive_try_mean",
    "positive_try_sd",
    "negative_utterances",
    "negative_n",
    "negative_try_mean",
    "negative_try_sd",
    "positive_minus_negative_try_mean",
]
QUESTION_ORDER_FIELDS = [
    "scope",
    "utterance_id",
    "qud",
    "measure",
    "direction",
    "matched_rating_order",
    "matched_order_n",
    "matched_order_try_mean",
    "other_rating_order",
    "other_order_n",
    "other_order_try_mean",
    "matched_minus_other_order_try_mean",
]
NATURALNESS_FIELDS = [
    "section",
    "item",
    "prior",
    "qud",
    "utterance_id",
    "rating_order",
    "n",
    "naturalness_mean",
]

def _records_with_ids(records: list[dict], utterance_ids: tuple[str, ...]) -> list[dict]:
    return [
        record
        for record in records
        if record.get("utterance_id") in utterance_ids
    ]

def _try_stats(records: list[dict]) -> dict:
    return utils.summarize_measure(records, "try_rating")

def _completion_stats(records: list[dict]) -> dict:
    return utils.summarize_measure(records, "completion_rating")

def _naturalness_stats(records: list[dict]) -> dict:
    return utils.summarize_measure(records, "naturalness_rating")

def _effect_row(
    effect: str,
    scope: str,
    direction: str,
    target_group: str,
    target_records: list[dict],
    reference_group: str,
    reference_records: list[dict],
) -> dict:
    target = _try_stats(target_records)
    reference = _try_stats(reference_records)
    difference = None
    if target["mean"] is not None and reference["mean"] is not None:
        difference = target["mean"] - reference["mean"]
    return {
        "effect": effect,
        "scope": scope,
        "measure": "try_rating",
        "direction": direction,
        "target_group": target_group,
        "target_n": target["n"],
        "target_mean": utils.rounded(target["mean"]),
        "reference_group": reference_group,
        "reference_n": reference["n"],
        "reference_mean": utils.rounded(reference["mean"]),
        "effect_estimate": utils.rounded(difference),
    }

def build_overall_effects(records: list[dict]) -> list[dict]:
    implicatives = _records_with_ids(records, IMPLICATIVE_IDS)
    simple_baselines = _records_with_ids(records, SIMPLE_BASELINE_IDS)
    return [
        _effect_row(
            "prior_effect",
            "all_four_implicatives",
            "high - low",
            "high",
            [row for row in implicatives if row.get("prior") == "high"],
            "low",
            [row for row in implicatives if row.get("prior") == "low"],
        ),
        _effect_row(
            "qud_effect",
            "all_four_implicatives",
            "P? - TRY?",
            "P?",
            [row for row in implicatives if row.get("qud") == "P?"],
            "TRY?",
            [row for row in implicatives if row.get("qud") == "TRY?"],
        ),
        _effect_row(
            "implicative_boost",
            "all_four_implicatives_vs_did_and_didnt",
            "all_four_implicatives - did_and_didnt",
            "all_four_implicatives",
            implicatives,
            "did_and_didnt",
            simple_baselines,
        ),
    ]

def build_prior_effects_by_implicative(records: list[dict]) -> list[dict]:
    rows = []
    for utterance_id in (
        utterance['utterance_id'] for utterance in utils.UTTERANCES
    ):
        utterance_records = [
            row for row in records if row.get("utterance_id") == utterance_id
        ]
        high = _try_stats(
            [row for row in utterance_records if row.get("prior") == "high"]
        )
        low = _try_stats(
            [row for row in utterance_records if row.get("prior") == "low"]
        )
        difference = None
        if high["mean"] is not None and low["mean"] is not None:
            difference = high["mean"] - low["mean"]
        rows.append(
            {
                "utterance_id": utterance_id,
                "measure": "try_rating",
                "direction": "high - low",
                "high_n": high["n"],
                "high_try_mean": utils.rounded(high["mean"]),
                "low_n": low["n"],
                "low_try_mean": utils.rounded(low["mean"]),
                "high_minus_low_try_mean": utils.rounded(difference),
            }
        )
    return rows

def build_qud_effects_by_implicative(records: list[dict]) -> list[dict]:
    rows = []
    for utterance_id in (
        utterance['utterance_id'] for utterance in utils.UTTERANCES
    ):
        utterance_records = [
            row for row in records if row.get("utterance_id") == utterance_id
        ]
        p_qud = _try_stats(
            [row for row in utterance_records if row.get("qud") == "P?"]
        )
        try_qud = _try_stats(
            [row for row in utterance_records if row.get("qud") == "TRY?"]
        )
        difference = None
        if p_qud["mean"] is not None and try_qud["mean"] is not None:
            difference = p_qud["mean"] - try_qud["mean"]
        rows.append(
            {
                "utterance_id": utterance_id,
                "measure": "try_rating",
                "direction": "P? - TRY?",
                "p_qud_n": p_qud["n"],
                "p_qud_try_mean": utils.rounded(p_qud["mean"]),
                "try_qud_n": try_qud["n"],
                "try_qud_try_mean": utils.rounded(try_qud["mean"]),
                "p_qud_minus_try_qud_try_mean": utils.rounded(difference),
            }
        )
    return rows

def build_try_means_by_utterance(records: list[dict]) -> list[dict]:
    rows = []
    for utterance in utils.UTTERANCES:
        utterance_id = utterance["utterance_id"]
        utterance_records = [
            row for row in records if row.get("utterance_id") == utterance_id
        ]
        try_stats = _try_stats(utterance_records)
        completion_stats = _completion_stats(utterance_records)
        rows.append(
            {
                "utterance_id": utterance_id,
                "n": try_stats["n"],
                "try_mean": utils.rounded(try_stats["mean"]),
                "try_sd": utils.rounded(try_stats["sd"]),
                "completion_mean": utils.rounded(completion_stats["mean"]),
                "completion_sd": utils.rounded(completion_stats["sd"]),
            }
        )
    return rows

def build_implicative_boosts_by_pair(records: list[dict]) -> list[dict]:
    rows = []
    for implicative_id, baseline_id in BOOST_PAIRS:
        implicative = _try_stats(
            [row for row in records if row.get("utterance_id") == implicative_id]
        )
        baseline = _try_stats(
            [row for row in records if row.get("utterance_id") == baseline_id]
        )
        difference = None
        if implicative["mean"] is not None and baseline["mean"] is not None:
            difference = implicative["mean"] - baseline["mean"]
        rows.append(
            {
                "contrast": f"{implicative_id}_minus_{baseline_id}",
                "measure": "try_rating",
                "direction": f"{implicative_id} - {baseline_id}",
                "implicative_utterance": implicative_id,
                "implicative_n": implicative["n"],
                "implicative_try_mean": utils.rounded(implicative["mean"]),
                "baseline_utterance": baseline_id,
                "baseline_n": baseline["n"],
                "baseline_try_mean": utils.rounded(baseline["mean"]),
                "implicative_minus_baseline_try_mean": utils.rounded(difference),
            }
        )
    return rows

def build_grouped_implicative_boosts(records: list[dict]) -> list[dict]:
    rows = []
    for contrast, target_ids, baseline_ids in GROUPED_BOOSTS:
        target = _try_stats(_records_with_ids(records, target_ids))
        baseline = _try_stats(_records_with_ids(records, baseline_ids))
        rows.append(
            {
                "contrast": contrast,
                "target_utterances": "|".join(target_ids),
                "target_n": target["n"],
                "target_try_mean": utils.rounded(target["mean"]),
                "target_try_sd": utils.rounded(target["sd"]),
                "baseline_utterances": "|".join(baseline_ids),
                "baseline_n": baseline["n"],
                "baseline_try_mean": utils.rounded(baseline["mean"]),
                "baseline_try_sd": utils.rounded(baseline["sd"]),
                "target_minus_baseline_try_mean": utils.rounded(
                    target["mean"] - baseline["mean"]
                ),
            }
        )
    return rows

def build_positive_outcome_contrasts(records: list[dict]) -> list[dict]:
    rows = []
    for contrast, positive_ids, negative_ids in POSITIVE_OUTCOME_CONTRASTS:
        positive = _try_stats(_records_with_ids(records, positive_ids))
        negative = _try_stats(_records_with_ids(records, negative_ids))
        rows.append(
            {
                "contrast": contrast,
                "positive_utterances": "|".join(positive_ids),
                "positive_n": positive["n"],
                "positive_try_mean": utils.rounded(positive["mean"]),
                "positive_try_sd": utils.rounded(positive["sd"]),
                "negative_utterances": "|".join(negative_ids),
                "negative_n": negative["n"],
                "negative_try_mean": utils.rounded(negative["mean"]),
                "negative_try_sd": utils.rounded(negative["sd"]),
                "positive_minus_negative_try_mean": utils.rounded(
                    positive["mean"] - negative["mean"]
                ),
            }
        )
    return rows

def build_question_order_effects(records: list[dict]) -> list[dict]:
    implicatives = _records_with_ids(records, IMPLICATIVE_IDS)
    groups = [("all_four_implicatives", "all", implicatives)]
    groups.extend(
        (
            "by_implicative",
            utterance_id,
            [
                row
                for row in implicatives
                if row.get("utterance_id") == utterance_id
            ],
        )
        for utterance_id in IMPLICATIVE_IDS
    )

    rows = []
    for scope, utterance_id, group_records in groups:
        for qud, matched_order, other_order in [
            ("TRY?", TRY_FIRST_ORDER, P_FIRST_ORDER),
            ("P?", P_FIRST_ORDER, TRY_FIRST_ORDER),
        ]:
            qud_records = [
                row for row in group_records if row.get("qud") == qud
            ]
            matched = _try_stats(
                [
                    row
                    for row in qud_records
                    if row.get("rating_order") == matched_order
                ]
            )
            other = _try_stats(
                [
                    row
                    for row in qud_records
                    if row.get("rating_order") == other_order
                ]
            )
            difference = None
            if matched["mean"] is not None and other["mean"] is not None:
                difference = matched["mean"] - other["mean"]
            rows.append(
                {
                    "scope": scope,
                    "utterance_id": utterance_id,
                    "qud": qud,
                    "measure": "try_rating",
                    "direction": "QUD-matched order - other order",
                    "matched_rating_order": matched_order,
                    "matched_order_n": matched["n"],
                    "matched_order_try_mean": utils.rounded(
                        matched["mean"]
                    ),
                    "other_rating_order": other_order,
                    "other_order_n": other["n"],
                    "other_order_try_mean": utils.rounded(other["mean"]),
                    "matched_minus_other_order_try_mean": utils.rounded(
                        difference
                    ),
                }
            )
    return rows

def _naturalness_row(
    section: str,
    records: list[dict],
    **labels,
) -> dict:
    stats = _naturalness_stats(records)
    return {
        "section": section,
        "item": labels.get("item", "all"),
        "prior": labels.get("prior", "all"),
        "qud": labels.get("qud", "all"),
        "utterance_id": labels.get("utterance_id", "all"),
        "rating_order": labels.get("rating_order", "all"),
        "n": stats["n"],
        "naturalness_mean": utils.rounded(stats["mean"]),
    }

def build_naturalness_descriptives(records: list[dict]) -> list[dict]:
    rows = [_naturalness_row("overall", records)]
    grouping_specs = [
        ("by_item", ("item",)),
        ("by_utterance", ("utterance_id",)),
        ("by_item_utterance", ("item", "utterance_id")),
        ("by_prior_utterance", ("prior", "utterance_id")),
        ("by_qud_utterance", ("qud", "utterance_id")),
        ("by_rating_order_utterance", ("rating_order", "utterance_id")),
    ]
    for section, keys in grouping_specs:
        for group_key, group_records in sorted(
            utils.grouped(records, keys).items(),
            key=lambda item: utils.sort_tuple_key(item[0]),
        ):
            rows.append(
                _naturalness_row(
                    section,
                    group_records,
                    **dict(zip(keys, group_key)),
                )
            )
    return rows

FOCUSED_OUTPUT_SPECS = (
    (
        "effects_overall",
        "effects_overall",
        build_overall_effects,
        OVERALL_EFFECT_FIELDS,
    ),
    (
        "prior_effect_by_implicative",
        "prior_effect_by_implicative",
        build_prior_effects_by_implicative,
        PRIOR_EFFECT_FIELDS,
    ),
    (
        "qud_effect_by_implicative",
        "qud_effect_by_implicative",
        build_qud_effects_by_implicative,
        QUD_EFFECT_FIELDS,
    ),
    (
        "try_mean_by_utterance",
        "try_mean_by_utterance",
        build_try_means_by_utterance,
        TRY_MEAN_BY_UTTERANCE_FIELDS,
    ),
    (
        "implicative_boost_by_pair",
        "implicative_boost_by_pair",
        build_implicative_boosts_by_pair,
        BOOST_FIELDS,
    ),
    (
        "implicative_boost_grouped",
        "implicative_boost_grouped",
        build_grouped_implicative_boosts,
        GROUPED_BOOST_FIELDS,
    ),
    (
        "positive_outcome_contrasts",
        "positive_outcome_contrasts",
        build_positive_outcome_contrasts,
        POSITIVE_OUTCOME_FIELDS,
    ),
    (
        "question_order_effects",
        "question_order_effects",
        build_question_order_effects,
        QUESTION_ORDER_FIELDS,
    ),
    (
        "naturalness_descriptives",
        "naturalness_descriptives",
        build_naturalness_descriptives,
        NATURALNESS_FIELDS,
    ),
)

def write_focused_descriptive_outputs(
    records: list[dict],
    output_dir: Path,
    prefix: str,
) -> dict[str, Path]:
    outputs = {}
    for label, suffix, builder, fieldnames in FOCUSED_OUTPUT_SPECS:
        path = output_dir / f"{prefix}_{suffix}.csv"
        utils.write_csv(path, builder(records), fieldnames)
        outputs[label] = path
    return outputs

def remove_stale_prefixed_csvs(
    output_dir: Path,
    prefix: str,
    keep_paths: list[Path],
) -> None:
    keep_names = {path.name for path in keep_paths}
    for path in output_dir.glob(f"{prefix}_*.csv"):
        if path.name not in keep_names:
            path.unlink()
