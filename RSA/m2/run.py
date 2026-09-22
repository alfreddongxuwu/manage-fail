from __future__ import annotations

import math
from pathlib import Path

from .core import (
    ALPHA, PRIORS, UTTERANCES, WORLDS, build_world_prior,
    derive_outcome_link, effects, literal_listener, mean,
    pragmatic_listener_try, pragmatic_speaker, read_naturalness,
    read_norming_priors, read_observed_try, write_csv,
)

def main() -> None:
    thesis_root = Path(__file__).resolve().parents[2]
    output_dir = Path(__file__).resolve().parent / "outputs"
    try_prior, outcome_prior = read_norming_priors(thesis_root)
    naturalness = read_naturalness(thesis_root)
    observed = read_observed_try(thesis_root)
    costs = {u: -math.log(naturalness[u]) for u in UTTERANCES}
    r0, r1 = derive_outcome_link(try_prior, outcome_prior)
    literal, pragmatic = {}, {}
    for context in PRIORS:
        prior = build_world_prior(context, try_prior, r0, r1)
        l0 = literal_listener(prior)
        s1 = pragmatic_speaker(l0, costs)
        l1 = pragmatic_listener_try(prior, s1)
        for utterance in UTTERANCES:
            key = (context, utterance)
            literal[key] = sum(p * w.tried for p, w in zip(l0[utterance], WORLDS))
            pragmatic[key] = l1[utterance]
    rows = []
    for utterance in UTTERANCES:
        row = {"utterance_id": utterance}
        for context in PRIORS:
            row[f"{context}_l0"] = literal[(context, utterance)]
            row[f"{context}_prediction"] = pragmatic[(context, utterance)]
            row[f"{context}_observed"] = observed[(context, utterance)]
        row["overall_l0"] = mean([literal[(c, utterance)] for c in PRIORS])
        row["overall_prediction"] = mean([pragmatic[(c, utterance)] for c in PRIORS])
        row["overall_observed"] = mean([observed[(c, utterance)] for c in PRIORS])
        rows.append(row)
    write_csv(output_dir / "predictions.csv", rows, list(rows[0]))
    l0_effects, l1_effects, observed_effects = effects(literal), effects(pragmatic), effects(observed)
    effect_rows = [{"effect": name, "m2_l0": l0_effects[name],
                    "m2_l1": l1_effects[name], "observed_descriptive": observed_effects[name]}
                   for name in l1_effects]
    write_csv(output_dir / "effects.csv", effect_rows, list(effect_rows[0]))
    inputs = [{"context": c, "try_prior": try_prior[c], "completion_prior": outcome_prior[c],
               "p_outcome_given_try": r1, "p_outcome_given_no_try": r0, "alpha": ALPHA}
              for c in PRIORS]
    write_csv(output_dir / "inputs.csv", inputs, list(inputs[0]))
    print(f"M-causal alpha={ALPHA:g}: wrote {len(rows)} utterances to {output_dir}")

if __name__ == "__main__":
    main()
