from __future__ import annotations

from pathlib import Path
import unittest

from afterglow.evals import run_eval_fixtures


class EvalFixtureTests(unittest.TestCase):
    def test_eval_fixtures_all_pass(self) -> None:
        fixture_path = Path(__file__).parent / "fixtures" / "eval_scenarios.json"
        results = run_eval_fixtures(fixture_path)
        self.assertTrue(results)
        self.assertTrue(all(result["passed"] for result in results))


if __name__ == "__main__":
    unittest.main()
