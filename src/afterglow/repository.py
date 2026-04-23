from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .models import (
    DebriefSubmission,
    GlobalRankingFeatures,
    MatchContext,
    MatchOutcome,
    MatchRecord,
    MatchStatus,
    OperatorSummary,
    PairMemoryProfile,
    TraceStep,
    UserMemoryProfile,
)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _serialize_submission(submission: DebriefSubmission) -> str:
    payload = asdict(submission)
    payload["energy"] = submission.energy.value
    payload["curiosity"] = submission.curiosity.value
    payload["comfort"] = submission.comfort.value
    payload["follow_up_intent"] = submission.follow_up_intent.value
    payload["submitted_at"] = submission.submitted_at.isoformat()
    return json.dumps(payload, sort_keys=True)


class SQLiteAfterglowRepository:
    def __init__(self, db_path: str | Path = "afterglow.db") -> None:
        self.db_path = str(db_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _session(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._session() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS matches (
                    match_id TEXT PRIMARY KEY,
                    user_a_id TEXT NOT NULL,
                    user_b_id TEXT NOT NULL,
                    venue_name TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    finalized_reason TEXT,
                    outcome_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS submissions (
                    match_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    PRIMARY KEY (match_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id TEXT PRIMARY KEY,
                    conversation_style TEXT NOT NULL,
                    venue_preference TEXT NOT NULL,
                    match_archetype TEXT NOT NULL,
                    last_match_score INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pair_memory (
                    match_id TEXT PRIMARY KEY,
                    average_rating REAL NOT NULL,
                    rating_spread INTEGER NOT NULL,
                    conflict_flag INTEGER NOT NULL,
                    follow_up_action TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS global_features (
                    feature_name TEXT PRIMARY KEY,
                    feature_value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def register_match(self, context: MatchContext) -> MatchRecord:
        created_at = _iso_now()
        with self._session() as connection:
            connection.execute(
                """
                INSERT INTO matches (
                    match_id, user_a_id, user_b_id, venue_name, completed_at,
                    status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(match_id) DO UPDATE SET
                    user_a_id=excluded.user_a_id,
                    user_b_id=excluded.user_b_id,
                    venue_name=excluded.venue_name,
                    completed_at=excluded.completed_at,
                    updated_at=excluded.updated_at
                """,
                (
                    context.match_id,
                    context.user_a_id,
                    context.user_b_id,
                    context.venue_name,
                    context.completed_at.isoformat(),
                    MatchStatus.REGISTERED.value,
                    created_at,
                    created_at,
                ),
            )
        self.get_user_memory_profile(context.user_a_id)
        self.get_user_memory_profile(context.user_b_id)
        return self.get_match(context.match_id)

    def set_match_status(self, match_id: str, status: MatchStatus, finalized_reason: str | None = None) -> None:
        with self._session() as connection:
            connection.execute(
                """
                UPDATE matches
                SET status = ?, finalized_reason = COALESCE(?, finalized_reason), updated_at = ?
                WHERE match_id = ?
                """,
                (status.value, finalized_reason, _iso_now(), match_id),
            )

    def get_match(self, match_id: str) -> MatchRecord:
        with self._session() as connection:
            match_row = connection.execute(
                "SELECT * FROM matches WHERE match_id = ?",
                (match_id,),
            ).fetchone()
            if match_row is None:
                raise KeyError(f"Unknown match_id: {match_id}")

            submissions = {
                row["user_id"]: self._deserialize_submission(row["payload_json"])
                for row in connection.execute(
                    "SELECT * FROM submissions WHERE match_id = ?",
                    (match_id,),
                ).fetchall()
            }
            outcome = (
                self._deserialize_outcome(match_row["outcome_json"])
                if match_row["outcome_json"]
                else None
            )
            context = MatchContext(
                match_id=match_row["match_id"],
                user_a_id=match_row["user_a_id"],
                user_b_id=match_row["user_b_id"],
                venue_name=match_row["venue_name"],
                completed_at=datetime.fromisoformat(match_row["completed_at"]),
            )
            return MatchRecord(
                context=context,
                status=MatchStatus(match_row["status"]),
                submissions=submissions,
                finalized_outcome=outcome,
            )

    def upsert_submission(self, submission: DebriefSubmission) -> str:
        payload_json = _serialize_submission(submission)
        payload_hash = str(hash(payload_json))
        with self._session() as connection:
            existing = connection.execute(
                "SELECT payload_hash FROM submissions WHERE match_id = ? AND user_id = ?",
                (submission.match_id, submission.user_id),
            ).fetchone()

            if existing is not None and existing["payload_hash"] == payload_hash:
                return "duplicate"

            connection.execute(
                """
                INSERT INTO submissions (match_id, user_id, payload_json, payload_hash, submitted_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(match_id, user_id) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    payload_hash=excluded.payload_hash,
                    submitted_at=excluded.submitted_at
                """,
                (
                    submission.match_id,
                    submission.user_id,
                    payload_json,
                    payload_hash,
                    submission.submitted_at.isoformat(),
                ),
            )
        return "updated" if existing is not None else "inserted"

    def save_outcome(self, outcome: MatchOutcome) -> None:
        outcome_payload = {
            "match_id": outcome.match_id,
            "participant_count": outcome.participant_count,
            "match_update_score": outcome.match_update_score,
            "average_rating": outcome.average_rating,
            "rating_spread": outcome.rating_spread,
            "conflict_flag": outcome.conflict_flag,
            "finalized_reason": outcome.finalized_reason,
            "follow_up_decision": {
                "action": outcome.follow_up_decision.action.value,
                "summary": outcome.follow_up_decision.summary,
                "suggested_copy": outcome.follow_up_decision.suggested_copy,
            },
            "memory_updates": [asdict(item) for item in outcome.memory_updates],
            "trace": [asdict(item) for item in outcome.trace],
        }

        with self._session() as connection:
            connection.execute("DELETE FROM traces WHERE match_id = ?", (outcome.match_id,))
            for step in outcome.trace:
                connection.execute(
                    """
                    INSERT INTO traces (
                        match_id, stage, title, summary, confidence, latency_ms, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        outcome.match_id,
                        step.stage,
                        step.title,
                        step.summary,
                        step.confidence,
                        step.latency_ms,
                        _iso_now(),
                    ),
                )

            connection.execute(
                """
                UPDATE matches
                SET status = ?, finalized_reason = ?, outcome_json = ?, updated_at = ?
                WHERE match_id = ?
                """,
                (
                    MatchStatus.FINALIZED.value,
                    outcome.finalized_reason,
                    json.dumps(outcome_payload, sort_keys=True),
                    _iso_now(),
                    outcome.match_id,
                ),
            )
            connection.execute(
                """
                INSERT INTO pair_memory (
                    match_id, average_rating, rating_spread, conflict_flag, follow_up_action, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(match_id) DO UPDATE SET
                    average_rating=excluded.average_rating,
                    rating_spread=excluded.rating_spread,
                    conflict_flag=excluded.conflict_flag,
                    follow_up_action=excluded.follow_up_action,
                    updated_at=excluded.updated_at
                """,
                (
                    outcome.match_id,
                    outcome.average_rating,
                    outcome.rating_spread,
                    int(outcome.conflict_flag),
                    outcome.follow_up_decision.action.value,
                    _iso_now(),
                ),
            )

    def get_user_memory_profile(self, user_id: str) -> UserMemoryProfile:
        with self._session() as connection:
            row = connection.execute(
                "SELECT * FROM user_memory WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if row is None:
                profile = UserMemoryProfile(user_id=user_id)
                connection.execute(
                    """
                    INSERT INTO user_memory (
                        user_id, conversation_style, venue_preference,
                        match_archetype, last_match_score, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        profile.user_id,
                        profile.conversation_style,
                        profile.venue_preference,
                        profile.match_archetype,
                        profile.last_match_score,
                        profile.updated_at.isoformat(),
                    ),
                )
                return profile
            return UserMemoryProfile(
                user_id=row["user_id"],
                conversation_style=row["conversation_style"],
                venue_preference=row["venue_preference"],
                match_archetype=row["match_archetype"],
                last_match_score=row["last_match_score"],
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def update_user_memory(self, profile: UserMemoryProfile) -> None:
        with self._session() as connection:
            connection.execute(
                """
                UPDATE user_memory
                SET conversation_style = ?, venue_preference = ?, match_archetype = ?,
                    last_match_score = ?, updated_at = ?
                WHERE user_id = ?
                """,
                (
                    profile.conversation_style,
                    profile.venue_preference,
                    profile.match_archetype,
                    profile.last_match_score,
                    profile.updated_at.isoformat(),
                    profile.user_id,
                ),
            )

    def update_global_features(self, features: GlobalRankingFeatures) -> None:
        entries = {
            "total_finalized_matches": features.total_finalized_matches,
            "total_second_date_offers": features.total_second_date_offers,
            "average_match_score": features.average_match_score,
            "average_rating": features.average_rating,
            "last_updated_at": features.last_updated_at.isoformat(),
        }
        with self._session() as connection:
            for name, value in entries.items():
                connection.execute(
                    """
                    INSERT INTO global_features (feature_name, feature_value, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(feature_name) DO UPDATE SET
                        feature_value=excluded.feature_value,
                        updated_at=excluded.updated_at
                    """,
                    (name, json.dumps(value), _iso_now()),
                )

    def get_global_features(self) -> GlobalRankingFeatures:
        with self._session() as connection:
            rows = connection.execute("SELECT * FROM global_features").fetchall()
        if not rows:
            return GlobalRankingFeatures()
        values = {row["feature_name"]: json.loads(row["feature_value"]) for row in rows}
        return GlobalRankingFeatures(
            total_finalized_matches=int(values.get("total_finalized_matches", 0)),
            total_second_date_offers=int(values.get("total_second_date_offers", 0)),
            average_match_score=float(values.get("average_match_score", 0.0)),
            average_rating=float(values.get("average_rating", 0.0)),
            last_updated_at=datetime.fromisoformat(values.get("last_updated_at", _iso_now())),
        )

    def get_pair_memory(self, match_id: str) -> PairMemoryProfile | None:
        with self._session() as connection:
            row = connection.execute(
                "SELECT * FROM pair_memory WHERE match_id = ?",
                (match_id,),
            ).fetchone()
        if row is None:
            return None
        return PairMemoryProfile(
            match_id=row["match_id"],
            average_rating=row["average_rating"],
            rating_spread=row["rating_spread"],
            conflict_flag=bool(row["conflict_flag"]),
            follow_up_action=row["follow_up_action"],
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def list_latest_outcomes(self, limit: int = 10) -> list[OperatorSummary]:
        with self._session() as connection:
            rows = connection.execute(
                """
                SELECT match_id, status, outcome_json
                FROM matches
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        summaries: list[OperatorSummary] = []
        for row in rows:
            payload = json.loads(row["outcome_json"]) if row["outcome_json"] else {}
            follow_up = payload.get("follow_up_decision", {})
            summaries.append(
                OperatorSummary(
                    match_id=row["match_id"],
                    status=row["status"],
                    average_rating=payload.get("average_rating"),
                    match_update_score=payload.get("match_update_score"),
                    follow_up_action=follow_up.get("action"),
                    conflict_flag=payload.get("conflict_flag"),
                )
            )
        return summaries

    def get_trace(self, match_id: str) -> list[dict[str, object]]:
        with self._session() as connection:
            rows = connection.execute(
                """
                SELECT stage, title, summary, confidence, latency_ms
                FROM traces
                WHERE match_id = ?
                ORDER BY id ASC
                """,
                (match_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _deserialize_submission(self, payload_json: str) -> DebriefSubmission:
        payload = json.loads(payload_json)
        from .models import ComfortSignal, CuriositySignal, EnergySignal, FollowUpIntent

        return DebriefSubmission(
            match_id=payload["match_id"],
            user_id=payload["user_id"],
            date_rating=payload["date_rating"],
            energy=EnergySignal(payload["energy"]),
            curiosity=CuriositySignal(payload["curiosity"]),
            comfort=ComfortSignal(payload["comfort"]),
            follow_up_intent=FollowUpIntent(payload["follow_up_intent"]),
            note=payload["note"],
            submitted_at=datetime.fromisoformat(payload["submitted_at"]),
        )

    def _deserialize_outcome(self, payload_json: str) -> MatchOutcome:
        from .models import FollowUpAction, FollowUpDecision, MemoryUpdate, TraceStep

        payload = json.loads(payload_json)
        return MatchOutcome(
            match_id=payload["match_id"],
            participant_count=payload["participant_count"],
            match_update_score=payload["match_update_score"],
            average_rating=payload["average_rating"],
            rating_spread=payload["rating_spread"],
            conflict_flag=payload["conflict_flag"],
            finalized_reason=payload["finalized_reason"],
            follow_up_decision=FollowUpDecision(
                action=FollowUpAction(payload["follow_up_decision"]["action"]),
                summary=payload["follow_up_decision"]["summary"],
                suggested_copy=payload["follow_up_decision"]["suggested_copy"],
            ),
            memory_updates=[MemoryUpdate(**item) for item in payload["memory_updates"]],
            trace=[TraceStep(**item) for item in payload["trace"]],
        )
