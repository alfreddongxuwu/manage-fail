from __future__ import annotations

import unittest
from pathlib import Path
from statistics import mean

from RSA.model_comparison.core import load_empirical_inputs, observed_cell_means
from RSA.m2.core import read_norming_priors, read_naturalness, read_observed_try
from RSA.m2_deterministic_qud.run import read_observed_try_by_qud, QUDS

ROOT = Path(__file__).resolve().parents[3]

class EmpiricalSharingTests(unittest.TestCase):
    def test_all_models_share_full_precision_empirical_inputs(self):
        inputs = load_empirical_inputs()
        tried, completed = read_norming_priors(ROOT)
        self.assertEqual(dict(inputs.try_prior), tried)
        self.assertEqual(dict(inputs.completion_prior), completed)
        self.assertEqual(dict(inputs.naturalness), read_naturalness(ROOT))

        self.assertAlmostEqual(tried["low"], (.2108 + 4.87 / 24) / 2, places=14)
        self.assertAlmostEqual(completed["low"], (.2176 + 6.23 / 24) / 2, places=14)

    def test_observed_means_are_consistent_across_model_branches(self):
        causal = read_observed_try(ROOT)
        qud = read_observed_try_by_qud(ROOT)
        baseline = observed_cell_means()
        for row in baseline.to_dict("records"):
            key = row["context"], row["utterance"]
            self.assertEqual(row["observed_p_try"], causal[key])
            self.assertAlmostEqual(causal[key], mean(qud[key[0], q, key[1]] for q in QUDS), places=14)

if __name__ == "__main__":
    unittest.main()
