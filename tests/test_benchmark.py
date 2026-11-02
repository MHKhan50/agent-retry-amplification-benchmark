import sys
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import benchmark
from benchmark import POLICIES, aggregate, evaluate, generate_scenarios, run


class BenchmarkTests(unittest.TestCase):

    def test_scenario_generation_is_deterministic(self):
        self.assertEqual(
            generate_scenarios(10, (7,)),
            generate_scenarios(10, (7,))
        )

    def test_policy_names_are_unique(self):
        self.assertEqual(len(POLICIES), len(set(POLICIES)))

    def test_no_retry_makes_one_attempt(self):
        s = {
            "seed": 1, "scenario_id": "x",
            "operation": "send_notification",
            "transient_failures": 3,
            "commit_before_error": 0,
            "base_latency_steps": 1
        }
        r = evaluate(s, "no_retry")
        self.assertEqual(r["attempts"], 1)
        self.assertEqual(r["task_success"], 0)

    def test_idempotency_deduplicates_committed_retries(self):
        s = {
            "seed": 1, "scenario_id": "x",
            "operation": "create_ticket",
            "transient_failures": 3,
            "commit_before_error": 1,
            "base_latency_steps": 1
        }
        r = evaluate(s, "idempotency_key")
        self.assertEqual(r["side_effect_count"], 1)
        self.assertEqual(r["duplicate_side_effects"], 0)

    def test_naive_retry_can_duplicate_effects(self):
        s = {
            "seed": 1, "scenario_id": "x",
            "operation": "submit_payment",
            "transient_failures": 2,
            "commit_before_error": 1,
            "base_latency_steps": 1
        }
        r = evaluate(s, "naive_retry")
        self.assertEqual(r["attempts"], 3)
        self.assertEqual(r["duplicate_side_effects"], 2)

    def test_bounded_retry_caps_attempts(self):
        s = {
            "seed": 1, "scenario_id": "x",
            "operation": "update_record",
            "transient_failures": 5,
            "commit_before_error": 0,
            "base_latency_steps": 1
        }
        self.assertEqual(evaluate(s, "bounded_backoff")["attempts"], 3)

    def test_aggregate_has_all_policies(self):
        scenarios = generate_scenarios(2, (3,))
        rows = [evaluate(s, p) for s in scenarios for p in POLICIES]
        self.assertEqual(
            {x["policy"] for x in aggregate(rows)},
            set(POLICIES)
        )

    def test_full_run_shape_uses_temporary_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            test_data = root / "data"
            test_output = root / "outputs"

            with patch.object(benchmark, "DATA", test_data), \
                 patch.object(benchmark, "OUT", test_output):

                result = run(3, (2, 5))

            self.assertEqual(result["synthetic_scenarios"], 6)
            self.assertEqual(result["policy_evaluations"], 24)

            with (test_data / "scenarios.csv").open(newline="") as f:
                scenarios = list(csv.DictReader(f))

            with (test_output / "episode_results.csv").open(newline="") as f:
                episodes = list(csv.DictReader(f))

            with (test_output / "policy_summary.csv").open(newline="") as f:
                summaries = list(csv.DictReader(f))

            self.assertEqual(len(scenarios), 6)
            self.assertEqual(len(episodes), 24)
            self.assertEqual(len(summaries), 4)


if __name__ == "__main__":
    unittest.main()
