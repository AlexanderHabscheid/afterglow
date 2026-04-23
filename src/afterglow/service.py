from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path

from .engine import evaluate_match
from .models import (
    DebriefSubmission,
    GlobalRankingFeatures,
    MatchContext,
    MatchOutcome,
    MatchStatus,
    OperatorSummary,
)
from .outbox import SQLiteSMSOutbox
from .repository import SQLiteAfterglowRepository
from .sms import CheckInMessageComposer, SMSReplyNormalizer


def _json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()  # type: ignore[union-attr]
    return value


class AfterglowService:
    def __init__(
        self,
        db_path: str | Path = "afterglow.db",
        repository: SQLiteAfterglowRepository | None = None,
        sms_outbox: SQLiteSMSOutbox | None = None,
        message_composer: CheckInMessageComposer | None = None,
        reply_normalizer: SMSReplyNormalizer | None = None,
    ) -> None:
        self.repository = repository or SQLiteAfterglowRepository(db_path=db_path)
        self.sms_outbox = sms_outbox or SQLiteSMSOutbox(db_path=db_path)
        self.message_composer = message_composer or CheckInMessageComposer()
        self.reply_normalizer = reply_normalizer or SMSReplyNormalizer()

    def register_match(self, context: MatchContext) -> dict[str, object]:
        self.repository.register_match(context)
        return {"status": "registered", "match_id": context.match_id}

    def open_check_in_window(self, match_id: str) -> dict[str, object]:
        record = self.repository.get_match(match_id)
        self.repository.set_match_status(match_id, MatchStatus.CHECK_IN_OPEN)
        messages = self.message_composer.build_messages(record.context)
        queued_messages = self.sms_outbox.enqueue_messages(messages)
        return {
            "status": "check-in-open",
            "match_id": match_id,
            "queued_messages": queued_messages,
        }

    def submit_debrief(self, submission: DebriefSubmission) -> dict[str, object]:
        record = self.repository.get_match(submission.match_id)
        if record.finalized_outcome is not None:
            return self._outcome_payload(record.finalized_outcome, status="already-finalized")

        intake_status = self.repository.upsert_submission(submission)
        self.repository.set_match_status(submission.match_id, MatchStatus.PENDING)
        record = self.repository.get_match(submission.match_id)

        if intake_status == "duplicate":
            if len(record.submissions) < 2:
                return {
                    "status": "duplicate-ignored",
                    "match_id": submission.match_id,
                    "received_submissions": len(record.submissions),
                    "message": "Identical submission already stored. Waiting for the remaining participant.",
                }

        if len(record.submissions) < 2:
            return {
                "status": "pending",
                "match_id": submission.match_id,
                "received_submissions": len(record.submissions),
                "message": "Stored participant check-in. Waiting for the remaining rating.",
            }

        outcome = evaluate_match(record.context, list(record.submissions.values()), finalized_reason="complete")
        self._persist_outcome(outcome)
        return self._outcome_payload(outcome, status="finalized")

    def finalize_match(self, match_id: str, reason: str = "timeout") -> dict[str, object]:
        record = self.repository.get_match(match_id)
        if record.finalized_outcome is not None:
            return self._outcome_payload(record.finalized_outcome, status="already-finalized")
        if not record.submissions:
            raise ValueError("Cannot finalize a match with no submissions.")

        outcome = evaluate_match(record.context, list(record.submissions.values()), finalized_reason=reason)
        self._persist_outcome(outcome)
        return self._outcome_payload(outcome, status="finalized")

    def get_trace(self, match_id: str) -> list[dict[str, object]]:
        return self.repository.get_trace(match_id)

    def get_match_summary(self, match_id: str) -> dict[str, object]:
        record = self.repository.get_match(match_id)
        pair_memory = self.repository.get_pair_memory(match_id)
        return {
            "match_id": match_id,
            "status": record.status.value,
            "submission_count": len(record.submissions),
            "pair_memory": _json_ready(asdict(pair_memory)) if pair_memory else None,
            "outcome": self._outcome_payload(record.finalized_outcome, status="finalized")
            if record.finalized_outcome
            else None,
        }

    def get_user_memory_snapshot(self, user_id: str) -> dict[str, object]:
        profile = self.repository.get_user_memory_profile(user_id)
        return _json_ready(asdict(profile))  # type: ignore[return-value]

    def get_pair_memory_snapshot(self, match_id: str) -> dict[str, object] | None:
        pair_memory = self.repository.get_pair_memory(match_id)
        return _json_ready(asdict(pair_memory)) if pair_memory else None  # type: ignore[return-value]

    def get_global_memory_snapshot(self) -> dict[str, object]:
        return _json_ready(asdict(self.repository.get_global_features()))  # type: ignore[return-value]

    def list_latest_outcomes(self, limit: int = 10) -> list[dict[str, object]]:
        summaries: list[OperatorSummary] = self.repository.list_latest_outcomes(limit=limit)
        return [asdict(summary) for summary in summaries]

    def list_check_in_messages(
        self,
        *,
        match_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        return self.sms_outbox.list_messages(match_id=match_id, status=status, limit=limit)

    def mark_check_in_message_sent(
        self,
        message_id: int,
        *,
        provider_message_id: str | None = None,
        provider_status: str | None = None,
    ) -> dict[str, object]:
        return self.sms_outbox.mark_sent(
            message_id,
            provider_message_id=provider_message_id,
            provider_status=provider_status,
        )

    def receive_sms_reply(self, payload: dict[str, object]) -> dict[str, object]:
        submission = self.reply_normalizer.normalize(payload)
        return self.submit_debrief(submission)

    def _persist_outcome(self, outcome: MatchOutcome) -> None:
        for update in outcome.memory_updates:
            current = self.repository.get_user_memory_profile(update.user_id)
            next_profile = replace(
                current,
                **{
                    update.field_name: update.after,
                    "last_match_score": outcome.match_update_score,
                },
            )
            self.repository.update_user_memory(next_profile)

        global_features = self.repository.get_global_features()
        next_global = GlobalRankingFeatures(
            total_finalized_matches=global_features.total_finalized_matches + 1,
            total_second_date_offers=global_features.total_second_date_offers
            + int(outcome.follow_up_decision.action.value == "offer-second-date"),
            average_match_score=round(
                (
                    global_features.average_match_score * global_features.total_finalized_matches
                    + outcome.match_update_score
                )
                / (global_features.total_finalized_matches + 1),
                2,
            ),
            average_rating=round(
                (
                    global_features.average_rating * global_features.total_finalized_matches
                    + outcome.average_rating
                )
                / (global_features.total_finalized_matches + 1),
                2,
            ),
        )
        self.repository.update_global_features(next_global)
        self.repository.save_outcome(outcome)

    def _outcome_payload(self, outcome: MatchOutcome | None, status: str) -> dict[str, object] | None:
        if outcome is None:
            return None
        return {
            "status": status,
            "match_id": outcome.match_id,
            "participant_count": outcome.participant_count,
            "average_rating": outcome.average_rating,
            "rating_spread": outcome.rating_spread,
            "conflict_flag": outcome.conflict_flag,
            "finalized_reason": outcome.finalized_reason,
            "match_update_score": outcome.match_update_score,
            "follow_up_action": outcome.follow_up_decision.action.value,
            "follow_up_summary": outcome.follow_up_decision.summary,
            "suggested_copy": outcome.follow_up_decision.suggested_copy,
            "memory_updates": [asdict(item) for item in outcome.memory_updates],
            "trace": [asdict(item) for item in outcome.trace],
        }
