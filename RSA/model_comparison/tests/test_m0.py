from __future__ import annotations

import unittest

import numpy as np

from RSA.model_comparison.core import (
    CONTEXTS,
    UTTERANCES,
    headline_effects,
    load_empirical_inputs,
    prediction_frame,
)
from RSA.model_comparison.m0 import STATES, meaning_matrix, run_m0, world_prior

class M0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inputs = load_empirical_inputs()
        cls.results = run_m0(cls.inputs, alpha=1.0)
        cls.predictions = prediction_frame(cls.results, cls.inputs)

    def test_world_inventory_is_complete(self) -> None:
        observed = {(state.tried, state.outcome) for state in STATES}
        self.assertEqual(observed, {(1, 1), (1, 0), (0, 1), (0, 0)})

    def test_world_priors_recover_both_norming_marginals(self) -> None:
        for context in CONTEXTS:
            prior = world_prior(self.inputs, context)
            self.assertTrue(np.all(prior > 0.0))
            self.assertAlmostEqual(float(prior.sum()), 1.0)
            p_try = sum(p for p, state in zip(prior, STATES) if state.tried)
            p_outcome = sum(p for p, state in zip(prior, STATES) if state.outcome)
            self.assertAlmostEqual(p_try, self.inputs.try_prior[context], places=12)
            self.assertAlmostEqual(
                p_outcome, self.inputs.completion_prior[context], places=12
            )

    def test_complete_m0_lexicon(self) -> None:
        meanings = meaning_matrix()
        self.assertEqual(meanings.shape, (len(UTTERANCES), len(STATES)))
        support = {
            utterance: tuple(
                state.name
                for state, truth in zip(STATES, meanings[index])
                if truth == 1.0
            )
            for index, utterance in enumerate(UTTERANCES)
        }
        self.assertEqual(support["managed"], ("w11", "w01"))
        self.assertEqual(support["didnt_manage"], ("w10", "w00"))
        self.assertEqual(support["failed"], ("w10", "w00"))
        self.assertEqual(support["didnt_fail"], ("w11", "w01"))
        self.assertEqual(support["did"], ("w11", "w01"))
        self.assertEqual(support["didnt"], ("w10", "w00"))
        self.assertEqual(support["tried"], ("w11", "w10"))
        self.assertEqual(support["didnt_try"], ("w01", "w00"))

    def test_distributions_normalize(self) -> None:
        for result in self.results.values():
            self.assertTrue(np.allclose(result.l0.sum(axis=1), 1.0))
            self.assertTrue(np.allclose(result.s1.sum(axis=1), 1.0))
            self.assertTrue(np.allclose(result.l1.sum(axis=1), 1.0))

    def test_naturalness_costs_are_empirical_negative_logs(self) -> None:
        for utterance in UTTERANCES:
            self.assertAlmostEqual(
                self.inputs.costs[utterance],
                -np.log(self.inputs.naturalness[utterance]),
                places=12,
            )

    def test_m0_boosts_are_zero_at_l0_and_l1(self) -> None:
        for column in ("l0_p_try", "l1_p_try"):
            effects = headline_effects(self.predictions, column)
            self.assertAlmostEqual(effects["positive_boost"], 0.0, places=12)
            self.assertAlmostEqual(effects["negative_boost"], 0.0, places=12)

    def test_m0_retains_a_collapsed_prior_effect(self) -> None:
        effects = headline_effects(self.predictions, "l1_p_try")
        self.assertGreater(effects["collapsed_implicative_prior_effect"], 0.0)

if __name__ == "__main__":
    unittest.main()
