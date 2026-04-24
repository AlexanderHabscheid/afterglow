from __future__ import annotations

import unittest
from unittest.mock import patch

from afterglow.api import _print_check_in_result


class APILoggingTests(unittest.TestCase):
    def test_pending_check_in_logs_submission_state(self) -> None:
        with patch("builtins.print") as mock_print:
            _print_check_in_result(
                channel="ui",
                user_id="avery",
                result={
                    "status": "pending",
                    "match_id": "match-demo-ui-001",
                    "received_submissions": 1,
                    "message": "Stored participant check-in. Waiting for the remaining rating.",
                },
            )

        logged_line = mock_print.call_args.args[0]
        self.assertIn("channel=ui", logged_line)
        self.assertIn("user=avery", logged_line)
        self.assertIn("status=pending", logged_line)
        self.assertIn("received_submissions=1", logged_line)

    def test_finalized_check_in_logs_score_and_follow_up(self) -> None:
        with patch("builtins.print") as mock_print:
            _print_check_in_result(
                channel="ui",
                user_id="lena",
                result={
                    "status": "finalized",
                    "match_id": "match-demo-ui-001",
                    "match_update_score": 87,
                    "follow_up_action": "offer-second-date",
                    "average_rating": 4.5,
                    "finalized_reason": "complete",
                },
            )

        logged_line = mock_print.call_args.args[0]
        self.assertIn("status=finalized", logged_line)
        self.assertIn("score=87", logged_line)
        self.assertIn("follow_up=offer-second-date", logged_line)
        self.assertIn("avg_rating=4.5", logged_line)


if __name__ == "__main__":
    unittest.main()
