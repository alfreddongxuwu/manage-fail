from __future__ import annotations

import unittest

import numpy as np

from RSA.model_comparison.core import (
    CONTEXTS,
    IMPLICATIVES,
    UTTERANCES,
    headline_effects,
    load_empirical_inputs,
    prediction_frame,
)
from RSA.model_comparison.m0 import meaning_matrix as m0_meaning_matrix
from RSA.model_comparison.m0 import world_prior
from RSA.model_comparison.m1 import meaning_matrix as m1_meaning_matrix
from RSA.model_comparison.m1 import run_m1

class M1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inputs = load_empirical_inputs()
        cls.results = run_m1(cls.inputs, alpha=1.0)
        cls.predictions = prediction_frame(cls.results, cls.inputs)

    def test_m1_uses_the_exact_m0_world_priors(self) -> None:
        for context in CONTEXTS:
            self.assertTrue(
                np.array_equal(
                    world_prior(self.inputs, context),
                    world_prior(self.inputs, context),
                )
            )

    def test_only_implicative_meanings_change_from_m0(self) -> None:
        m0 = m0_meaning_matrix()
        m1 = m1_meaning_matrix()
        for index, utterance in enumerate(UTTERANCES):
            if utterance in IMPLICATIVES:
                self.assertFalse(np.array_equal(m0[index], m1[index]))
            else:
                self.assertTrue(np.array_equal(m0[index], m1[index]))

    def test_complete_m1_lexicon(self) -> None:
        meanings = m1_meaning_matrix()
        support = {
            utterance: tuple(
                state_name
                for state_name, truth in zip(
                    ("w11", "w10", "w01", "w00"), meanings[index]
                )
                if truth == 1.0
            )
            for index, utterance in enumerate(UTTERANCES)
        }
        self.assertEqual(support["managed"], ("w11",))
        self.assertEqual(support["didnt_manage"], ("w10",))
        self.assertEqual(support["failed"], ("w10",))
        self.assertEqual(support["didnt_fail"], ("w11",))
        self.assertEqual(support["did"], ("w11", "w01"))
        self.assertEqual(support["didnt"], ("w10", "w00"))
        self.assertEqual(support["tried"], ("w11", "w10"))
        self.assertEqual(support["didnt_try"], ("w01", "w00"))

    def test_all_implicatives_are_categorical_try_at_l0_and_l1(self) -> None:
        cells = self.predictions.set_index(["context", "utterance"])
        for context in CONTEXTS:
            for utterance in IMPLICATIVES:
                self.assertAlmostEqual(
                    cells.loc[(context, utterance), "l0_p_try"], 1.0, places=12
                )
                self.assertAlmostEqual(
                    cells.loc[(context, utterance), "l1_p_try"], 1.0, places=12
                )

    def test_m1_eliminates_implicative_prior_effect(self) -> None:
        effects = headline_effects(self.predictions, "l1_p_try")
        self.assertAlmostEqual(
            effects["collapsed_implicative_prior_effect"], 0.0, places=12
        )

    def test_m1_predicts_both_positive_and_negative_boosts(self) -> None:
        effects = headline_effects(self.predictions, "l1_p_try")
        self.assertGreater(effects["positive_boost"], 0.0)
        self.assertGreater(effects["negative_boost"], 0.0)
        self.assertGreater(effects["negative_boost"], effects["positive_boost"])

    def test_distributions_normalize(self) -> None:
        for result in self.results.values():
            self.assertTrue(np.allclose(result.l0.sum(axis=1), 1.0))
            self.assertTrue(np.allclose(result.s1.sum(axis=1), 1.0))
            self.assertTrue(np.allclose(result.l1.sum(axis=1), 1.0))

if __name__ == "__main__":
    unittest.main()
