from __future__ import annotations

import math
from pathlib import Path

from RSA.m2.core import (
    ALPHA, IMPLICATIVES, NEGATIVE_IMPLICATIVES, POSITIVE_IMPLICATIVES,
    PRIORS, UTTERANCES, WORLDS, World, build_world_prior, cause_probability,
    derive_outcome_link, effects, literal_listener, mean, normalize,
    pragmatic_listener_try, pragmatic_speaker, read_naturalness,
    read_norming_priors, read_observed_try, truth, write_csv,
)

def bernoulli_kl(posterior: float, prior: float) -> float:
    divergence = 0.0
    if posterior > 0.0:
        divergence += posterior * math.log(posterior / prior)
    if posterior < 1.0:
        divergence += (1.0 - posterior) * math.log(
            (1.0 - posterior) / (1.0 - prior)
        )
    return divergence

def backoff_response(posterior: float, prior: float) -> tuple[float, float, float]:
    divergence = bernoulli_kl(posterior, prior)
    omega = math.exp(-divergence)
    response = omega * posterior + (1.0 - omega) * prior
    return divergence, omega, response

def main() -> None:
    thesis_root = Path(__file__).resolve().parents[2]
    output_dir = Path(__file__).resolve().parent / "outputs"

    try_prior, outcome_prior = read_norming_priors(thesis_root)
    naturalness = read_naturalness(thesis_root)
    observed = read_observed_try(thesis_root)
    costs = {utterance: -math.log(naturalness[utterance]) for utterance in UTTERANCES}
    r0, r1 = derive_outcome_link(try_prior, outcome_prior)

    base_predictions: dict[tuple[str, str], float] = {}
    backoff_predictions: dict[tuple[str, str], float] = {}
    diagnostics: dict[tuple[str, str], tuple[float, float]] = {}

    for context in PRIORS:
        world_prior = build_world_prior(context, try_prior, r0, r1)

        recovered_try = sum(
            probability * world.tried
            for probability, world in zip(world_prior, WORLDS)
        )
        recovered_outcome = sum(
            probability * world.outcome
            for probability, world in zip(world_prior, WORLDS)
        )
        if not math.isclose(recovered_try, try_prior[context], abs_tol=1e-12):
            raise ValueError(f"TRY marginal not recovered for {context}")
        if not math.isclose(
            recovered_outcome, outcome_prior[context], abs_tol=1e-12
        ):
            raise ValueError(f"Outcome marginal not recovered for {context}")

        l0 = literal_listener(world_prior)
        speaker = pragmatic_speaker(l0, costs)
        l1_try = pragmatic_listener_try(world_prior, speaker)
        for utterance in UTTERANCES:
            key = (context, utterance)
            base_predictions[key] = l1_try[utterance]
            divergence, omega, response = backoff_response(
                l1_try[utterance], try_prior[context]
            )
            diagnostics[key] = (divergence, omega)
            backoff_predictions[key] = response

    prediction_rows: list[dict[str, object]] = []
    for utterance in UTTERANCES:
        row: dict[str, object] = {"utterance_id": utterance}
        for context in PRIORS:
            divergence, omega = diagnostics[(context, utterance)]
            row[f"{context}_l1"] = base_predictions[(context, utterance)]
            row[f"{context}_kl"] = divergence
            row[f"{context}_omega"] = omega
            row[f"{context}_backoff"] = backoff_predictions[(context, utterance)]
            row[f"{context}_observed"] = observed[(context, utterance)]
        row["overall_l1"] = mean(
            [base_predictions[(context, utterance)] for context in PRIORS]
        )
        row["overall_backoff"] = mean(
            [backoff_predictions[(context, utterance)] for context in PRIORS]
        )
        row["overall_observed"] = mean(
            [observed[(context, utterance)] for context in PRIORS]
        )
        prediction_rows.append(row)

    base_effects = effects(base_predictions)
    backoff_effects = effects(backoff_predictions)
    observed_effects = effects(observed)
    effect_rows = []
    for effect_name in base_effects:
        effect_rows.append(
            {
                "effect": effect_name,
                "base_l1": base_effects[effect_name],
                "m2_backoff": backoff_effects[effect_name],
                "observed_descriptive": observed_effects[effect_name],
            }
        )

    prediction_fields = [
        "utterance_id",
        "high_l1",
        "high_kl",
        "high_omega",
        "high_backoff",
        "high_observed",
        "low_l1",
        "low_kl",
        "low_omega",
        "low_backoff",
        "low_observed",
        "overall_l1",
        "overall_backoff",
        "overall_observed",
    ]
    write_csv(output_dir / "predictions.csv", prediction_rows, prediction_fields)
    write_csv(
        output_dir / "effects.csv",
        effect_rows,
        ["effect", "base_l1", "m2_backoff", "observed_descriptive"],
    )

    input_rows = [
        {
            "context": context,
            "try_prior": try_prior[context],
            "completion_prior": outcome_prior[context],
            "p_outcome_given_try": r1,
            "p_outcome_given_no_try": r0,
            "alpha": ALPHA,
        }
        for context in PRIORS
    ]
    write_csv(
        output_dir / "inputs.csv",
        input_rows,
        [
            "context",
            "try_prior",
            "completion_prior",
            "p_outcome_given_try",
            "p_outcome_given_no_try",
            "alpha",
        ],
    )

    print("M-backoff PREDICTIONS")
    print("utterance            high      low  overall")
    for row in prediction_rows:
        print(
            f"{row['utterance_id']:<18} "
            f"{float(row['high_backoff']):7.3f} "
            f"{float(row['low_backoff']):7.3f} "
            f"{float(row['overall_backoff']):8.3f}"
        )

    print("\nHEADLINE EFFECTS")
    print("effect                                  base   backoff  observed")
    for row in effect_rows:
        print(
            f"{row['effect']:<38} "
            f"{float(row['base_l1']):7.3f} "
            f"{float(row['m2_backoff']):9.3f} "
            f"{float(row['observed_descriptive']):9.3f}"
        )

if __name__ == "__main__":
    main()
