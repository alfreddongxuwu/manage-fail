from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from condition_averaging import MAIN_CONDITIONS, NORMING_CONDITIONS, condition_mean
from RSA.settings import ALPHA
PRIORS = ("high", "low")
UTTERANCES = (
    "managed",
    "didnt_manage",
    "failed",
    "didnt_fail",
    "did",
    "didnt",
    "tried",
    "didnt_try",
)
IMPLICATIVES = ("managed", "didnt_manage", "failed", "didnt_fail")
POSITIVE_IMPLICATIVES = ("managed", "didnt_fail")
NEGATIVE_IMPLICATIVES = ("didnt_manage", "failed")

@dataclass(frozen=True)
class World:
    name: str
    tried: int
    outcome: int
    cause: str

WORLDS = (
    World("w1", 1, 1, "TRY"),
    World("w2", 1, 1, "OTHER"),
    World("w3", 1, 1, "NONE"),
    World("w4", 1, 0, "TRY"),
    World("w5", 1, 0, "OTHER"),
    World("w6", 1, 0, "NONE"),
    World("w7", 0, 1, "OTHER"),
    World("w8", 0, 1, "NONE"),
    World("w9", 0, 0, "OTHER"),
    World("w10", 0, 0, "NONE"),
)

def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot take the mean of an empty list")
    return sum(values) / len(values)

def _included_rows(path: Path, status: str) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return [row for row in csv.DictReader(stream)
                if row.get(status) in (None, "", "include")]

def read_norming_priors(
    thesis_root: Path, path: Path | None = None
) -> tuple[dict[str, float], dict[str, float]]:

    rows = _included_rows(
        path or thesis_root / "results/results_norming/norming_clean.csv",
        "screening_status",
    )
    grouped = {prior: [row for row in rows if row["prior"] == prior]
               for prior in PRIORS}
    return (
        {prior: condition_mean(grouped[prior], "try_rating_01", NORMING_CONDITIONS)
         for prior in PRIORS},
        {prior: condition_mean(grouped[prior], "completion_rating_01", NORMING_CONDITIONS)
         for prior in PRIORS},
    )

def read_naturalness(thesis_root: Path, path: Path | None = None) -> dict[str, float]:

    rows = _included_rows(
        path or thesis_root / "results/results_main/main_combined_clean.csv",
        "analysis_status",
    )
    values = {
        utterance: condition_mean(
            [row for row in rows if row["utterance_id"] == utterance],
            "naturalness_rating_01", MAIN_CONDITIONS,
        ) for utterance in UTTERANCES
    }
    if any(not 0.0 < values[utterance] <= 1.0 for utterance in UTTERANCES):
        raise ValueError("Naturalness means must lie in (0, 1]")
    return values

def read_observed_try(
    thesis_root: Path, path: Path | None = None
) -> dict[tuple[str, str], float]:

    rows = _included_rows(
        path or thesis_root / "results/results_main/main_combined_clean.csv",
        "analysis_status",
    )
    return {
        (prior, utterance): condition_mean(
            [row for row in rows
             if row["prior"] == prior and row["utterance_id"] == utterance],
            "try_rating_01", MAIN_CONDITIONS,
        ) for prior in PRIORS for utterance in UTTERANCES
    }

def derive_outcome_link(
    try_prior: dict[str, float], outcome_prior: dict[str, float]
) -> tuple[float, float]:
    slope = (
        (outcome_prior["high"] - outcome_prior["low"])
        / (try_prior["high"] - try_prior["low"])
    )
    r0 = outcome_prior["low"] - slope * try_prior["low"]
    r1 = r0 + slope
    if not (0.0 < r0 < r1 < 1.0):
        raise ValueError(f"Invalid outcome link: r0={r0}, r1={r1}")
    return r0, r1

def cause_probability(world: World) -> float:
    if world.tried == 1:
        return 1.0 / 3.0
    if world.outcome == 1:
        return 2.0 / 3.0 if world.cause == "OTHER" else 1.0 / 3.0
    return 1.0 / 3.0 if world.cause == "OTHER" else 2.0 / 3.0

def build_world_prior(
    context: str,
    try_prior: dict[str, float],
    r0: float,
    r1: float,
) -> list[float]:
    probabilities = []
    for world in WORLDS:
        p_try = try_prior[context] if world.tried else 1.0 - try_prior[context]
        p_outcome_given_try = r1 if world.tried else r0
        p_outcome = (
            p_outcome_given_try if world.outcome else 1.0 - p_outcome_given_try
        )
        probabilities.append(p_try * p_outcome * cause_probability(world))
    if not math.isclose(sum(probabilities), 1.0, abs_tol=1e-12):
        raise ValueError(f"World prior for {context} does not sum to one")
    return probabilities

def truth(utterance: str, world: World) -> bool:
    if utterance in ("managed", "didnt_fail"):
        return world.outcome == 1 and world.cause != "NONE"
    if utterance in ("didnt_manage", "failed"):
        return world.outcome == 0 and world.cause != "NONE"
    if utterance == "did":
        return world.outcome == 1
    if utterance == "didnt":
        return world.outcome == 0
    if utterance == "tried":
        return world.tried == 1
    if utterance == "didnt_try":
        return world.tried == 0
    raise KeyError(utterance)

def normalize(values: list[float]) -> list[float]:
    total = sum(values)
    if total <= 0.0:
        raise ValueError("Cannot normalize zero mass")
    return [value / total for value in values]

def literal_listener(world_prior: list[float]) -> dict[str, list[float]]:
    return {
        utterance: normalize(
            [
                world_prior[index] if truth(utterance, world) else 0.0
                for index, world in enumerate(WORLDS)
            ]
        )
        for utterance in UTTERANCES
    }

def pragmatic_speaker(
    l0: dict[str, list[float]], costs: dict[str, float]
) -> list[dict[str, float]]:
    speaker_rows: list[dict[str, float]] = []
    for world_index, _world in enumerate(WORLDS):
        logits: dict[str, float] = {}
        for utterance in UTTERANCES:
            literal_probability = l0[utterance][world_index]
            logits[utterance] = (
                ALPHA * (math.log(literal_probability) - costs[utterance])
                if literal_probability > 0.0
                else -math.inf
            )
        maximum = max(logits.values())
        weights = {
            utterance: (
                math.exp(logit - maximum) if math.isfinite(logit) else 0.0
            )
            for utterance, logit in logits.items()
        }
        denominator = sum(weights.values())
        speaker_rows.append(
            {utterance: weights[utterance] / denominator for utterance in UTTERANCES}
        )
    return speaker_rows

def pragmatic_listener_try(
    world_prior: list[float], speaker: list[dict[str, float]]
) -> dict[str, float]:
    predictions: dict[str, float] = {}
    for utterance in UTTERANCES:
        posterior = normalize(
            [
                speaker[index][utterance] * world_prior[index]
                for index in range(len(WORLDS))
            ]
        )
        predictions[utterance] = sum(
            probability * world.tried
            for probability, world in zip(posterior, WORLDS)
        )
    return predictions

def effects(predictions: dict[tuple[str, str], float]) -> dict[str, float]:
    collapsed_high = mean(
        [predictions[("high", utterance)] for utterance in IMPLICATIVES]
    )
    collapsed_low = mean(
        [predictions[("low", utterance)] for utterance in IMPLICATIVES]
    )

    overall = {
        utterance: mean(
            [predictions[(prior, utterance)] for prior in PRIORS]
        )
        for utterance in UTTERANCES
    }
    positive_boost = (
        mean([overall[utterance] for utterance in POSITIVE_IMPLICATIVES])
        - overall["did"]
    )
    negative_boost = (
        mean([overall[utterance] for utterance in NEGATIVE_IMPLICATIVES])
        - overall["didnt"]
    )
    return {
        "collapsed_implicative_prior_effect": collapsed_high - collapsed_low,
        "positive_outcome_boost": positive_boost,
        "negative_outcome_boost": negative_boost,
    }

def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
