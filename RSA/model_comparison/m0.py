from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .core import CONTEXTS, UTTERANCES, EmpiricalInputs, RSAResult, rsa_recursion

@dataclass(frozen=True)
class TOState:
    name: str
    tried: int
    outcome: int

STATES = (
    TOState("w11", 1, 1),
    TOState("w10", 1, 0),
    TOState("w01", 0, 1),
    TOState("w00", 0, 0),
)

def world_prior(inputs: EmpiricalInputs, context: str) -> np.ndarray:
    if context not in CONTEXTS:
        raise ValueError(f"Unknown context: {context!r}")
    p_try = inputs.try_prior[context]
    probabilities = []
    for state in STATES:
        p_t = p_try if state.tried else 1.0 - p_try
        p_o_given_t = (
            inputs.response_if_try if state.tried else inputs.response_without_try
        )
        p_o = p_o_given_t if state.outcome else 1.0 - p_o_given_t
        probabilities.append(p_t * p_o)
    prior = np.array(probabilities, dtype=float)
    return prior / prior.sum()

def meaning_matrix() -> np.ndarray:
    rows = []
    for utterance in UTTERANCES:
        if utterance in {"managed", "didnt_fail", "did"}:
            row = [float(state.outcome == 1) for state in STATES]
        elif utterance in {"didnt_manage", "failed", "didnt"}:
            row = [float(state.outcome == 0) for state in STATES]
        elif utterance == "tried":
            row = [float(state.tried == 1) for state in STATES]
        elif utterance == "didnt_try":
            row = [float(state.tried == 0) for state in STATES]
        else:
            raise AssertionError(f"No M0 meaning defined for {utterance!r}")
        rows.append(row)
    return np.array(rows, dtype=float)

def run_m0(inputs: EmpiricalInputs, alpha: float = 1.0) -> Mapping[str, RSAResult]:
    meanings = meaning_matrix()
    costs = np.array([inputs.costs[u] for u in UTTERANCES], dtype=float)
    try_values = np.array([state.tried for state in STATES], dtype=float)
    return {
        context: rsa_recursion(
            prior=world_prior(inputs, context),
            meanings=meanings,
            costs=costs,
            try_values=try_values,
            alpha=alpha,
        )
        for context in CONTEXTS
    }
