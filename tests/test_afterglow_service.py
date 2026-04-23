from __future__ import annotations

from datetime import UTC, datetime
import tempfile
import unittest

from afterglow.models import (
    ComfortSignal,
    CuriositySignal,
    DebriefSubmission,
    EnergySignal,
    FollowUpIntent,
    MatchContext,
)
from afterglow.service import AfterglowService


class AfterglowServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db")
        self.service = AfterglowService(db_path=self.temp_db.name)
        self.context = MatchContext(
            match_id="match-001",
            user_a_id="avery",
            user_b_id="lena",
            venue_name="Campanile sunset loop",
            completed_at=datetime.now(UTC),
        )
        self.service.register_match(self.context)

    def tearDown(self) -> None:
        self.temp_db.close()

    def test_stays_pending_until_both_people_submit(self) -> None:
        result = self.service.submit_debrief(
            DebriefSubmission(
                match_id="match-001",
                user_id="avery",
                date_rating=4,
                energy=EnergySignal.CHARGED,
                curiosity=CuriositySignal.OBSESSED,
                comfort=ComfortSignal.OPEN,
                follow_up_intent=FollowUpIntent.YES,
            )
        )
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["received_submissions"], 1)

    def test_duplicate_submission_is_idempotent(self) -> None:
        submission = DebriefSubmission(
            match_id="match-001",
            user_id="avery",
            date_rating=4,
            energy=EnergySignal.CHARGED,
            curiosity=CuriositySignal.OBSESSED,
            comfort=ComfortSignal.OPEN,
            follow_up_intent=FollowUpIntent.YES,
        )
        self.service.submit_debrief(submission)
        result = self.service.submit_debrief(submission)
        self.assertEqual(result["status"], "duplicate-ignored")

    def test_open_check_in_window_persists_provider_ready_outbox(self) -> None:
        result = self.service.open_check_in_window("match-001")
        queued = self.service.list_check_in_messages(match_id="match-001", status="queued")

        self.assertEqual(result["status"], "check-in-open")
        self.assertEqual(len(queued), 2)
        self.assertEqual({message["recipient_id"] for message in queued}, {"avery", "lena"})
        self.assertTrue(all(message["channel"] == "sms" for message in queued))

        sent = self.service.mark_check_in_message_sent(int(queued[0]["id"]))
        self.assertEqual(sent["status"], "sent")

    def test_recommends_follow_up_when_both_people_like_the_date(self) -> None:
        self.service.submit_debrief(
            DebriefSubmission(
                match_id="match-001",
                user_id="avery",
                date_rating=4,
                energy=EnergySignal.CHARGED,
                curiosity=CuriositySignal.OBSESSED,
                comfort=ComfortSignal.OPEN,
                follow_up_intent=FollowUpIntent.YES,
            )
        )
        result = self.service.submit_debrief(
            DebriefSubmission(
                match_id="match-001",
                user_id="lena",
                date_rating=5,
                energy=EnergySignal.CHARGED,
                curiosity=CuriositySignal.INTERESTED,
                comfort=ComfortSignal.FULLY_SAFE,
                follow_up_intent=FollowUpIntent.YES,
            )
        )
        self.assertEqual(result["status"], "finalized")
        self.assertEqual(result["follow_up_action"], "offer-second-date")
        self.assertGreaterEqual(result["match_update_score"], 76)

    def test_conflicting_ratings_suppress_follow_up(self) -> None:
        self.service.submit_debrief(
            DebriefSubmission(
                match_id="match-001",
                user_id="avery",
                date_rating=5,
                energy=EnergySignal.CHARGED,
                curiosity=CuriositySignal.OBSESSED,
                comfort=ComfortSignal.OPEN,
                follow_up_intent=FollowUpIntent.YES,
            )
        )
        result = self.service.submit_debrief(
            DebriefSubmission(
                match_id="match-001",
                user_id="lena",
                date_rating=2,
                energy=EnergySignal.DRAINED,
                curiosity=CuriositySignal.FLAT,
                comfort=ComfortSignal.GUARDED,
                follow_up_intent=FollowUpIntent.NO,
            )
        )
        self.assertEqual(result["follow_up_action"], "quiet-learn")
        self.assertTrue(result["conflict_flag"])

    def test_timeout_finalization_handles_one_sided_submission(self) -> None:
        self.service.submit_debrief(
            DebriefSubmission(
                match_id="match-001",
                user_id="avery",
                date_rating=4,
                energy=EnergySignal.STEADY,
                curiosity=CuriositySignal.INTERESTED,
                comfort=ComfortSignal.OPEN,
                follow_up_intent=FollowUpIntent.MAYBE,
            )
        )
        result = self.service.finalize_match("match-001", reason="timeout")
        self.assertEqual(result["participant_count"], 1)
        self.assertEqual(result["finalized_reason"], "timeout")
        self.assertEqual(result["follow_up_action"], "quiet-learn")

    def test_operator_views_include_global_memory(self) -> None:
        self.service.submit_debrief(
            DebriefSubmission(
                match_id="match-001",
                user_id="avery",
                date_rating=4,
                energy=EnergySignal.CHARGED,
                curiosity=CuriositySignal.OBSESSED,
                comfort=ComfortSignal.OPEN,
                follow_up_intent=FollowUpIntent.YES,
            )
        )
        self.service.submit_debrief(
            DebriefSubmission(
                match_id="match-001",
                user_id="lena",
                date_rating=4,
                energy=EnergySignal.STEADY,
                curiosity=CuriositySignal.INTERESTED,
                comfort=ComfortSignal.OPEN,
                follow_up_intent=FollowUpIntent.MAYBE,
            )
        )
        latest = self.service.list_latest_outcomes()
        global_memory = self.service.get_global_memory_snapshot()
        self.assertEqual(len(latest), 1)
        self.assertEqual(global_memory["total_finalized_matches"], 1)


if __name__ == "__main__":
    unittest.main()
