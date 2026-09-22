
from __future__ import annotations
import csv
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from condition_averaging import condition_mean, summarize_conditions

class ConditionAveragingTests(unittest.TestCase):
    def test_unequal_cell_sizes_do_not_change_cell_weights(self):
        rows = [dict(cell="a", y=y) for y in (0, 2)]
        rows += [dict(cell="b", y=y) for y in (10, 10, 12, 12)]
        result = summarize_conditions(rows, "y", ("cell",))
        self.assertEqual(result["n"], 6)
        self.assertEqual(result["n_cells"], 2)
        self.assertEqual(result["mean"], 6)
        self.assertAlmostEqual(result["se"], math.sqrt(1 / 3))
        self.assertAlmostEqual(result["df"], 12 / 7)
        self.assertAlmostEqual(result["sd"], math.sqrt(80 / 3))

    def test_question_order_is_pooled_within_design_cell(self):
        rows = [dict(cell="a", order="first", y=0),
                dict(cell="a", order="first", y=0),
                dict(cell="a", order="second", y=10)]
        self.assertAlmostEqual(condition_mean(rows, "y", ("cell",)), 10 / 3)
        self.assertEqual(condition_mean(rows, "y", ("cell", "order")), 5)

    def test_single_cell_reduces_to_sample_summary(self):
        result = summarize_conditions([dict(cell=1, y=y) for y in (1, 2, 3)],
                                      "y", ("cell",))
        self.assertEqual(result["mean"], 2)
        self.assertEqual(result["sd"], 1)
        self.assertAlmostEqual(result["se"], 1 / math.sqrt(3))
        self.assertEqual(result["df"], 2)

    def test_missing_and_singleton_values_have_explicit_uncertainty(self):
        result = summarize_conditions([dict(cell=1, y=None), dict(cell=2, y=4)],
                                      "y", ("cell",))
        self.assertEqual(result["mean"], 4)
        self.assertEqual(result["n_cells"], 1)
        self.assertIsNone(result["se"])
        with self.assertRaises(ValueError):
            condition_mean([], "y", ("cell",))

    def test_saved_main_descriptives_match_independent_64_cell_audit(self):
        path = ROOT / "results/results_main/main_combined_try_mean_by_utterance.csv"
        with path.open(encoding="utf-8-sig") as stream:
            rows = {row["utterance_id"]: row for row in csv.DictReader(stream)}
        expected = {"managed": .7386, "didnt_manage": .3589, "failed": .3234,
                    "didnt_fail": .6691, "did": .6902, "didnt": .2491,
                    "tried": .6483, "didnt_try": .1844}
        self.assertEqual({u: float(row["try_mean"]) for u, row in rows.items()}, expected)
        path = ROOT / "results/results_main/main_combined_naturalness_descriptives.csv"
        with path.open(encoding="utf-8-sig") as stream:
            rows = {row["utterance_id"]: float(row["naturalness_mean"])
                    for row in csv.DictReader(stream) if row["section"] == "by_utterance"}
        self.assertEqual(rows, {"managed": .6075, "didnt_manage": .5267,
            "failed": .3651, "didnt_fail": .2302, "did": .6297,
            "didnt": .6700, "tried": .5535, "didnt_try": .5892})

    def test_saved_norming_low_prior_gives_items_equal_weight(self):
        path = ROOT / "results/results_norming/norming_summary_long.csv"
        with path.open(encoding="utf-8-sig") as stream:
            rows = {row["measure"]: row for row in csv.DictReader(stream)
                    if row["section"] == "overall_by_prior" and row["prior"] == "low"}
        self.assertEqual(float(rows["try_rating"]["mean"]), .2069)
        self.assertEqual(float(rows["completion_rating"]["mean"]), .2386)
        self.assertEqual(int(rows["try_rating"]["n"]), 49)

if __name__ == "__main__":
    unittest.main()
