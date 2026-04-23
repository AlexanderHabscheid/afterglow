from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .models import (
    ComfortSignal,
    CuriositySignal,
    DebriefSubmission,
    EnergySignal,
    FollowUpIntent,
    MatchContext,
)
from .service import AfterglowService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "afterglow.db"
DEFAULT_FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "eval_scenarios.json"


def parse_datetime(value: str) -> datetime:
    if value == "now":
        return datetime.now(UTC)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def build_service(db_path: str | Path | None = None) -> AfterglowService:
    return AfterglowService(db_path=db_path or DEFAULT_DB_PATH)


def build_match_context(
    *,
    match_id: str,
    user_a_id: str,
    user_b_id: str,
    venue_name: str,
    completed_at: str,
) -> MatchContext:
    return MatchContext(
        match_id=match_id,
        user_a_id=user_a_id,
        user_b_id=user_b_id,
        venue_name=venue_name,
        completed_at=parse_datetime(completed_at),
    )


def build_debrief_submission(
    *,
    match_id: str,
    user_id: str,
    date_rating: int,
    energy: str,
    curiosity: str,
    comfort: str,
    follow_up_intent: str,
    note: str = "",
) -> DebriefSubmission:
    return DebriefSubmission(
        match_id=match_id,
        user_id=user_id,
        date_rating=int(date_rating),
        energy=EnergySignal(energy),
        curiosity=CuriositySignal(curiosity),
        comfort=ComfortSignal(comfort),
        follow_up_intent=FollowUpIntent(follow_up_intent),
        note=note,
    )
