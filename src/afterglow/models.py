from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Literal

DateRating = Literal[1, 2, 3, 4, 5]


class EnergySignal(str, Enum):
    DRAINED = "drained"
    STEADY = "steady"
    CHARGED = "charged"


class CuriositySignal(str, Enum):
    FLAT = "flat"
    INTERESTED = "interested"
    OBSESSED = "obsessed"


class ComfortSignal(str, Enum):
    GUARDED = "guarded"
    OPEN = "open"
    FULLY_SAFE = "fully-safe"


class FollowUpIntent(str, Enum):
    NO = "no"
    MAYBE = "maybe"
    YES = "yes"


class FollowUpAction(str, Enum):
    QUIET_LEARN = "quiet-learn"
    OFFER_SECOND_DATE = "offer-second-date"


class MatchStatus(str, Enum):
    REGISTERED = "registered"
    CHECK_IN_OPEN = "check-in-open"
    PENDING = "pending"
    FINALIZED = "finalized"


@dataclass(slots=True)
class MatchContext:
    match_id: str
    user_a_id: str
    user_b_id: str
    venue_name: str
    completed_at: datetime


@dataclass(slots=True)
class DebriefSubmission:
    match_id: str
    user_id: str
    date_rating: DateRating
    energy: EnergySignal
    curiosity: CuriositySignal
    comfort: ComfortSignal
    follow_up_intent: FollowUpIntent
    note: str = ""
    submitted_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class UserMemoryProfile:
    user_id: str
    conversation_style: str = "playful openers"
    venue_preference: str = "generic campus cafes"
    match_archetype: str = "broad curiosity cluster"
    last_match_score: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class PairMemoryProfile:
    match_id: str
    average_rating: float = 0.0
    rating_spread: int = 0
    conflict_flag: bool = False
    follow_up_action: str = FollowUpAction.QUIET_LEARN.value
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class GlobalRankingFeatures:
    total_finalized_matches: int = 0
    total_second_date_offers: int = 0
    average_match_score: float = 0.0
    average_rating: float = 0.0
    last_updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class MemoryUpdate:
    user_id: str
    field_name: str
    before: str | int
    after: str | int
    rationale: str


@dataclass(slots=True)
class TraceStep:
    stage: str
    title: str
    summary: str
    confidence: int
    latency_ms: int


@dataclass(slots=True)
class FollowUpDecision:
    action: FollowUpAction
    summary: str
    suggested_copy: list[str]


@dataclass(slots=True)
class MatchOutcome:
    match_id: str
    participant_count: int
    match_update_score: int
    average_rating: float
    rating_spread: int
    conflict_flag: bool
    finalized_reason: str
    follow_up_decision: FollowUpDecision
    memory_updates: list[MemoryUpdate]
    trace: list[TraceStep]


@dataclass(slots=True)
class MatchRecord:
    context: MatchContext
    status: MatchStatus
    submissions: dict[str, DebriefSubmission] = field(default_factory=dict)
    finalized_outcome: MatchOutcome | None = None


@dataclass(slots=True)
class OperatorSummary:
    match_id: str
    status: str
    average_rating: float | None
    match_update_score: int | None
    follow_up_action: str | None
    conflict_flag: bool | None
