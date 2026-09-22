from __future__ import annotations

import csv
import math
from pathlib import Path

from condition_averaging import MAIN_CONDITIONS, condition_mean

from RSA.m2.core import (
    ALPHA,
    IMPLICATIVES,
    NEGATIVE_IMPLICATIVES,
    POSITIVE_IMPLICATIVES,
    PRIORS,
    UTTERANCES,
    WORLDS,
    build_world_prior,
    derive_outcome_link,
    literal_listener,
    mean,
    pragmatic_listener_try,
    pragmatic_speaker,
    read_naturalness,
    read_norming_priors,
    truth,
    write_csv,
)

QUDS = ("P?", "TRY?")

def qud_answer(world_index: int, qud: str) -> int:
    world = WORLDS[world_index]
    if qud == "P?":
        return world.outcome
    if qud == "TRY?":
        return world.tried
    raise KeyError(qud)

def literal_qud_probability(
    l0: dict[str, list[float]], utterance: str, world_index: int, qud: str
) -> float:
    target_answer = qud_answer(world_index, qud)
    return sum(
        probability
        for other_index, probability in enumerate(l0[utterance])
        if qud_answer(other_index, qud) == target_answer
    )

def deterministic_qud_speaker(
    l0: dict[str, list[float]], costs: dict[str, float], qud: str
) -> list[dict[str, float]]:

    speaker_rows: list[dict[str, float]] = []
    for world_index, world in enumerate(WORLDS):
        logits: dict[str, float] = {}
        for utterance in UTTERANCES:
            if not truth(utterance, world):
                logits[utterance] = -math.inf
                continue
            answer_probability = literal_qud_probability(
                l0, utterance, world_index, qud
            )
            if answer_probability <= 0.0:
                raise ValueError(
                    f"True utterance {utterance} has zero probability for the "
                    f"correct {qud} answer in {world.name}"
                )
            logits[utterance] = ALPHA * (
                math.log(answer_probability) - costs[utterance]
            )

        maximum = max(logits.values())
        weights = {
            utterance: (
                math.exp(logit - maximum) if math.isfinite(logit) else 0.0
            )
            for utterance, logit in logits.items()
        }
        denominator = sum(weights.values())
        if denominator <= 0.0:
            raise ValueError(f"No true alternatives in {world.name} under {qud}")
        speaker_rows.append(
            {utterance: weights[utterance] / denominator for utterance in UTTERANCES}
        )
    return speaker_rows

def read_observed_try_by_qud(
    thesis_root: Path,
) -> dict[tuple[str, str, str], float]:
    path = thesis_root / "results/results_main/main_combined_clean.csv"
    cells: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            if row.get("analysis_status") not in (None, "", "include"):
                continue
            key = (row["prior"], row["qud"], row["utterance_id"])
            cells.setdefault(key, []).append(row)

    expected = {
        (prior, qud, utterance)
        for prior in PRIORS
        for qud in QUDS
        for utterance in UTTERANCES
    }
    if set(cells) != expected:
        raise ValueError(
            f"Observed cells differ from expected: {sorted(set(cells) ^ expected)}"
        )
    return {key: condition_mean(rows, "try_rating_01", MAIN_CONDITIONS)
            for key, rows in cells.items()}

def average_prediction(
    predictions: dict[tuple[str, str, str], float],
    *,
    priors: tuple[str, ...] = PRIORS,
    quds: tuple[str, ...] = QUDS,
    utterances: tuple[str, ...] = UTTERANCES,
) -> float:
    return mean(
        [
            predictions[(prior, qud, utterance)]
            for prior in priors
            for qud in quds
            for utterance in utterances
        ]
    )

def headline_effects(
    predictions: dict[tuple[str, str, str], float]
) -> dict[str, float]:
    prior_effect = average_prediction(
        predictions, priors=("high",), utterances=IMPLICATIVES
    ) - average_prediction(
        predictions, priors=("low",), utterances=IMPLICATIVES
    )
    qud_effect = average_prediction(
        predictions, quds=("P?",), utterances=IMPLICATIVES
    ) - average_prediction(
        predictions, quds=("TRY?",), utterances=IMPLICATIVES
    )
    positive_boost = average_prediction(
        predictions, utterances=POSITIVE_IMPLICATIVES
    ) - average_prediction(predictions, utterances=("did",))
    negative_boost = average_prediction(
        predictions, utterances=NEGATIVE_IMPLICATIVES
    ) - average_prediction(predictions, utterances=("didnt",))
    return {
        "collapsed_implicative_prior_effect": prior_effect,
        "collapsed_implicative_qud_effect_P_minus_TRY": qud_effect,
        "positive_outcome_boost": positive_boost,
        "negative_outcome_boost": negative_boost,
    }

def main() -> None:
    thesis_root = Path(__file__).resolve().parents[2]
    output_dir = Path(__file__).resolve().parent / "outputs"

    try_prior, outcome_prior = read_norming_priors(thesis_root)
    naturalness = read_naturalness(thesis_root)
    observed = read_observed_try_by_qud(thesis_root)
    costs = {utterance: -math.log(naturalness[utterance]) for utterance in UTTERANCES}
    r0, r1 = derive_outcome_link(try_prior, outcome_prior)

    predictions: dict[tuple[str, str, str], float] = {}
    base_predictions: dict[tuple[str, str], float] = {}

    for prior in PRIORS:
        world_prior = build_world_prior(prior, try_prior, r0, r1)
        l0 = literal_listener(world_prior)

        base_speaker = pragmatic_speaker(l0, costs)
        base_try = pragmatic_listener_try(world_prior, base_speaker)
        for utterance in UTTERANCES:
            base_predictions[(prior, utterance)] = base_try[utterance]

        for qud in QUDS:
            speaker = deterministic_qud_speaker(l0, costs, qud)
            for row in speaker:
                if not math.isclose(sum(row.values()), 1.0, abs_tol=1e-12):
                    raise ValueError(f"S1 row does not normalize under {prior}, {qud}")
            l1_try = pragmatic_listener_try(world_prior, speaker)
            for utterance in UTTERANCES:
                predictions[(prior, qud, utterance)] = l1_try[utterance]

    prediction_rows: list[dict[str, object]] = []
    for utterance in UTTERANCES:
        for qud in QUDS:
            high = predictions[("high", qud, utterance)]
            low = predictions[("low", qud, utterance)]
            high_observed = observed[("high", qud, utterance)]
            low_observed = observed[("low", qud, utterance)]
            prediction_rows.append(
                {
                    "utterance_id": utterance,
                    "qud": qud,
                    "high_prediction": high,
                    "low_prediction": low,
                    "overall_prediction": mean([high, low]),
                    "high_observed": high_observed,
                    "low_observed": low_observed,
                    "overall_observed": mean([high_observed, low_observed]),
                    "high_base_no_qud": base_predictions[("high", utterance)],
                    "low_base_no_qud": base_predictions[("low", utterance)],
                    "overall_base_no_qud": mean(
                        [
                            base_predictions[("high", utterance)],
                            base_predictions[("low", utterance)],
                        ]
                    ),
                }
            )

    model_effects = headline_effects(predictions)
    observed_effects = headline_effects(observed)
    effect_rows: list[dict[str, object]] = []
    for effect_name in model_effects:
        effect_rows.append(
            {
                "effect": effect_name,
                "deterministic_qud_m2": model_effects[effect_name],
                "observed_descriptive": observed_effects[effect_name],
            }
        )

    for qud in QUDS:
        for effect_name, positive, baseline in (
            ("positive_outcome_boost", POSITIVE_IMPLICATIVES, ("did",)),
            ("negative_outcome_boost", NEGATIVE_IMPLICATIVES, ("didnt",)),
        ):
            model_value = average_prediction(
                predictions, quds=(qud,), utterances=positive
            ) - average_prediction(predictions, quds=(qud,), utterances=baseline)
            observed_value = average_prediction(
                observed, quds=(qud,), utterances=positive
            ) - average_prediction(observed, quds=(qud,), utterances=baseline)
            effect_rows.append(
                {
                    "effect": f"{effect_name}_within_{qud}",
                    "deterministic_qud_m2": model_value,
                    "observed_descriptive": observed_value,
                }
            )

    qud_effect_rows: list[dict[str, object]] = []
    for utterance in UTTERANCES:
        model_value = average_prediction(
            predictions, quds=("P?",), utterances=(utterance,)
        ) - average_prediction(
            predictions, quds=("TRY?",), utterances=(utterance,)
        )
        observed_value = average_prediction(
            observed, quds=("P?",), utterances=(utterance,)
        ) - average_prediction(
            observed, quds=("TRY?",), utterances=(utterance,)
        )
        qud_effect_rows.append(
            {
                "utterance_id": utterance,
                "deterministic_qud_m2_P_minus_TRY": model_value,
                "observed_P_minus_TRY": observed_value,
            }
        )

    write_csv(
        output_dir / "predictions.csv",
        prediction_rows,
        [
            "utterance_id",
            "qud",
            "high_prediction",
            "low_prediction",
            "overall_prediction",
            "high_observed",
            "low_observed",
            "overall_observed",
            "high_base_no_qud",
            "low_base_no_qud",
            "overall_base_no_qud",
        ],
    )
    write_csv(
        output_dir / "effects.csv",
        effect_rows,
        ["effect", "deterministic_qud_m2", "observed_descriptive"],
    )
    write_csv(
        output_dir / "qud_effect_by_utterance.csv",
        qud_effect_rows,
        [
            "utterance_id",
            "deterministic_qud_m2_P_minus_TRY",
            "observed_P_minus_TRY",
        ],
    )
    write_csv(
        output_dir / "inputs.csv",
        [
            {
                "prior": prior,
                "try_prior": try_prior[prior],
                "completion_prior": outcome_prior[prior],
                "p_outcome_given_try": r1,
                "p_outcome_given_no_try": r0,
                "alpha": ALPHA,
                "qud_observation": "deterministic",
            }
            for prior in PRIORS
        ],
        [
            "prior",
            "try_prior",
            "completion_prior",
            "p_outcome_given_try",
            "p_outcome_given_no_try",
            "alpha",
            "qud_observation",
        ],
    )

    print("DETERMINISTIC-QUD M2 PREDICTIONS")
    print("utterance          QUD     high      low  overall  observed")
    for row in prediction_rows:
        print(
            f"{str(row['utterance_id']):<18} "
            f"{str(row['qud']):<5} "
            f"{float(row['high_prediction']):7.3f} "
            f"{float(row['low_prediction']):7.3f} "
            f"{float(row['overall_prediction']):8.3f} "
            f"{float(row['overall_observed']):9.3f}"
        )

    print("\nHEADLINE EFFECTS")
    print("effect                                          model  observed")
    for row in effect_rows:
        print(
            f"{str(row['effect']):<46} "
            f"{float(row['deterministic_qud_m2']):7.3f} "
            f"{float(row['observed_descriptive']):9.3f}"
        )

    print("\nQUD EFFECT BY UTTERANCE (P? - TRY?)")
    print("utterance            model  observed")
    for row in qud_effect_rows:
        print(
            f"{str(row['utterance_id']):<18} "
            f"{float(row['deterministic_qud_m2_P_minus_TRY']):7.3f} "
            f"{float(row['observed_P_minus_TRY']):9.3f}"
        )

if __name__ == "__main__":
    main()
