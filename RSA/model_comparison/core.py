from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from RSA.m2.core import read_naturalness, read_norming_priors, read_observed_try
from RSA.settings import ALPHA

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
CONTEXTS = ("high", "low")
IMPLICATIVES = ("managed", "didnt_manage", "failed", "didnt_fail")
POSITIVE_IMPLICATIVES = ("managed", "didnt_fail")
NEGATIVE_IMPLICATIVES = ("didnt_manage", "failed")

THESIS_ROOT = Path(__file__).resolve().parents[2]
NORMING_PATH = THESIS_ROOT / "results/results_norming/norming_clean.csv"
NATURALNESS_PATH = (
    THESIS_ROOT / "results/results_main/main_combined_clean.csv"
)
MAIN_DATA_PATH = THESIS_ROOT / "results/results_main/main_combined_clean.csv"

@dataclass(frozen=True)
class EmpiricalInputs:
    try_prior: Mapping[str, float]
    completion_prior: Mapping[str, float]
    response_if_try: float
    response_without_try: float
    naturalness: Mapping[str, float]
    costs: Mapping[str, float]

@dataclass(frozen=True)
class RSAResult:
    l0: np.ndarray
    s1: np.ndarray
    l1: np.ndarray
    p_try_l0: np.ndarray
    p_try_l1: np.ndarray

def load_empirical_inputs(
    norming_path: Path = NORMING_PATH,
    naturalness_path: Path = NATURALNESS_PATH,
) -> EmpiricalInputs:
    try_prior, completion_prior = read_norming_priors(THESIS_ROOT, norming_path)
    from RSA.m2.core import derive_outcome_link
    response_without_try, response_if_try = derive_outcome_link(try_prior, completion_prior)
    naturalness = read_naturalness(THESIS_ROOT, naturalness_path)
    costs = {u: float(-np.log(naturalness[u])) for u in UTTERANCES}
    return EmpiricalInputs(
        try_prior=try_prior,
        completion_prior=completion_prior,
        response_if_try=response_if_try,
        response_without_try=response_without_try,
        naturalness=naturalness,
        costs=costs,
    )

def rsa_recursion(
    prior: np.ndarray,
    meanings: np.ndarray,
    costs: np.ndarray,
    try_values: np.ndarray,
    alpha: float = 1.0,
) -> RSAResult:
    prior = np.asarray(prior, dtype=float)
    meanings = np.asarray(meanings, dtype=float)
    costs = np.asarray(costs, dtype=float)
    try_values = np.asarray(try_values, dtype=float)

    if alpha != ALPHA:
        raise ValueError("The retained models use fixed alpha = 1")
    if meanings.shape != (len(costs), len(prior)):
        raise ValueError("meanings must have shape utterances x worlds")
    if try_values.shape != prior.shape:
        raise ValueError("try_values must have one value per world")
    if np.any(prior <= 0.0) or not np.isclose(prior.sum(), 1.0):
        raise ValueError("world prior must have full support and sum to one")
    if np.any((meanings < 0.0) | (meanings > 1.0)):
        raise ValueError("meaning values must lie in [0, 1]")

    l0_raw = meanings * prior[None, :]
    l0_denominator = l0_raw.sum(axis=1, keepdims=True)
    if np.any(l0_denominator <= 0.0):
        raise ValueError("every utterance must be true in at least one world")
    l0 = l0_raw / l0_denominator

    with np.errstate(divide="ignore"):
        utility = np.log(l0.T) - costs[None, :]
    scaled_utility = alpha * utility
    row_max = np.max(scaled_utility, axis=1, keepdims=True)
    if np.any(~np.isfinite(row_max)):
        raise ValueError("every world must make at least one alternative true")
    speaker_weights = np.exp(scaled_utility - row_max)
    speaker_weights[~np.isfinite(scaled_utility)] = 0.0
    s1 = speaker_weights / speaker_weights.sum(axis=1, keepdims=True)

    l1_raw = s1.T * prior[None, :]
    l1_denominator = l1_raw.sum(axis=1, keepdims=True)
    if np.any(l1_denominator <= 0.0):
        raise ValueError("every utterance must have positive pragmatic probability")
    l1 = l1_raw / l1_denominator

    return RSAResult(
        l0=l0,
        s1=s1,
        l1=l1,
        p_try_l0=l0 @ try_values,
        p_try_l1=l1 @ try_values,
    )

def cost_vector(inputs: EmpiricalInputs) -> np.ndarray:
    return np.array([inputs.costs[u] for u in UTTERANCES], dtype=float)

def prediction_frame(
    results: Mapping[str, RSAResult], inputs: EmpiricalInputs
) -> pd.DataFrame:
    rows = []
    for context in CONTEXTS:
        result = results[context]
        for index, utterance in enumerate(UTTERANCES):
            rows.append(
                {
                    "context": context,
                    "utterance": utterance,
                    "naturalness": inputs.naturalness[utterance],
                    "cost": inputs.costs[utterance],
                    "l0_p_try": float(result.p_try_l0[index]),
                    "l1_p_try": float(result.p_try_l1[index]),
                }
            )
    return pd.DataFrame(rows)

def headline_effects(frame: pd.DataFrame, value_column: str) -> dict[str, float]:
    cells = frame.set_index(["context", "utterance"])[value_column]
    prior_effects = [
        float(cells.loc[("high", u)] - cells.loc[("low", u)])
        for u in IMPLICATIVES
    ]
    overall = {
        u: float(np.mean([cells.loc[(context, u)] for context in CONTEXTS]))
        for u in UTTERANCES
    }
    return {
        "collapsed_implicative_prior_effect": float(np.mean(prior_effects)),
        "positive_boost": float(
            np.mean([overall[u] for u in POSITIVE_IMPLICATIVES]) - overall["did"]
        ),
        "negative_boost": float(
            np.mean([overall[u] for u in NEGATIVE_IMPLICATIVES]) - overall["didnt"]
        ),
    }

def observed_cell_means(path: Path = MAIN_DATA_PATH) -> pd.DataFrame:

    cells = read_observed_try(THESIS_ROOT, path)
    return pd.DataFrame([
        {"context": context, "utterance": utterance, "observed_p_try": value}
        for (context, utterance), value in cells.items()
    ])
