import math
import unittest

from judge_agreement import cohen_kappa, bootstrap_ci, band, report


class KappaTests(unittest.TestCase):
    def test_perfect_agreement(self):
        a = ["yes", "no", "yes", "no"]
        self.assertAlmostEqual(cohen_kappa(a, a), 1.0)

    def test_textbook_example(self):
        # 50 items: 20 yes/yes, 5 yes/no, 10 no/yes, 15 no/no -> kappa = 0.4
        a = ["yes"] * 25 + ["no"] * 25
        b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
        self.assertAlmostEqual(cohen_kappa(a, b), 0.4, places=6)

    def test_chance_level_grader(self):
        # a grader that always says "yes" agrees often but carries no information
        a = ["yes"] * 70 + ["no"] * 30
        b = ["yes"] * 100
        self.assertAlmostEqual(cohen_kappa(a, b), 0.0, places=6)
        self.assertEqual(band(0.0), "no better than chance")

    def test_bootstrap_interval_contains_estimate(self):
        a = ["yes"] * 25 + ["no"] * 25
        b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
        lo, hi = bootstrap_ci(a, b, reps=500, seed=1)
        self.assertLessEqual(lo, 0.4)
        self.assertGreaterEqual(hi, 0.4)

    def test_report_verdict(self):
        a = ["yes"] * 70 + ["no"] * 30
        text, k, lo = report(a, ["yes"] * 100, reps=200, seed=0, threshold=0.6)
        self.assertIn("do not trust", text)
        self.assertFalse(math.isnan(k))


if __name__ == "__main__":
    unittest.main()
