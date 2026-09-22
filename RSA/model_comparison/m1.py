from __future__ import annotations

from typing import Mapping

import numpy as np

from .core import CONTEXTS, UTTERANCES, EmpiricalInputs, RSAResult, rsa_recursion
from .m0 import STATES, world_prior

IMPLICATIVES = {"managed", "didnt_manage", "failed", "didnt_fail"}

def meaning_matrix() -> np.ndarray:
    rows = []
    for utterance in UTTERANCES:
        if utterance in {"managed", "didnt_fail"}:
            row = [
                float(state.outcome == 1 and state.tried == 1) for state in STATES
            ]
        elif utterance in {"didnt_manage", "failed"}:
            row = [
                float(state.outcome == 0 and state.tried == 1) for state in STATES
            ]
        elif utterance == "did":
            row = [float(state.outcome == 1) for state in STATES]
        elif utterance == "didnt":
            row = [float(state.outcome == 0) for state in STATES]
        elif utterance == "tried":
            row = [float(state.tried == 1) for state in STATES]
        elif utterance == "didnt_try":
            row = [float(state.tried == 0) for state in STATES]
        else:
            raise AssertionError(f"No M-attempt meaning defined for {utterance!r}")
        rows.append(row)
    return np.array(rows, dtype=float)

def run_m1(inputs: EmpiricalInputs, alpha: float = 1.0) -> Mapping[str, RSAResult]:
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
