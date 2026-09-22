from __future__ import annotations

import unittest

import numpy as np

import RSA.model_comparison.m0 as m0
import RSA.model_comparison.m1 as m1
from RSA.model_comparison.core import CONTEXTS, load_empirical_inputs

class M1SharingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inputs = load_empirical_inputs()

    def test_m1_reuses_m0_states_and_world_prior_function(self) -> None:
        self.assertIs(m1.STATES, m0.STATES)
        self.assertIs(m1.world_prior, m0.world_prior)

    def test_m1_and_m0_receive_identical_world_priors(self) -> None:
        for context in CONTEXTS:
            self.assertTrue(
                np.array_equal(
                    m1.world_prior(self.inputs, context),
                    m0.world_prior(self.inputs, context),
                )
            )

if __name__ == "__main__":
    unittest.main()
