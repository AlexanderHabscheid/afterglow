from __future__ import annotations

from collections.abc import Iterable

from .models import (
    ComfortSignal,
    CuriositySignal,
    DebriefSubmission,
    EnergySignal,
    FollowUpAction,
    FollowUpDecision,
    FollowUpIntent,
    MatchContext,
    MatchOutcome,
    MemoryUpdate,
    TraceStep,
)

MATCH_WEIGHTS = {
    "rating": 0.34,
    "curiosity": 0.2,
    "comfort": 0.18,
    "energy": 0.16,
    "follow_up": 0.12,
}


def _score_rating(value: int) -> int:
    return value * 20


def _score_curiosity(value: CuriositySignal) -> int:
    return {
        CuriositySignal.FLAT: 40,
        CuriositySignal.INTERESTED: 74,
        CuriositySignal.OBSESSED: 95,
    }[value]


def _score_comfort(value: ComfortSignal) -> int:
    return {
        ComfortSignal.GUARDED: 48,
        ComfortSignal.OPEN: 80,
        ComfortSignal.FULLY_SAFE: 96,
    }[value]


def _score_energy(value: EnergySignal) -> int:
    return {
        EnergySignal.DRAINED: 42,
        EnergySignal.STEADY: 72,
        EnergySignal.CHARGED: 95,
    }[value]


def _score_follow_up(value: FollowUpIntent) -> int:
    return {
        FollowUpIntent.NO: 25,
        FollowUpIntent.MAYBE: 68,
        FollowUpIntent.YES: 98,
    }[value]


def _mean(values: Iterable[int]) -> float:
    items = list(values)
    return sum(items) / len(items)


def _build_trace(submissions: list[DebriefSubmission], score: int, finalized_reason: str) -> list[TraceStep]:
    participant_count = len(submissions)
    return [
        TraceStep(
            stage="01",
            title="Tiny check-in became a structured label",
            summary=(
                f"Read {participant_count} participant submission(s), including 1-5 rating and "
                "lightweight debrief signals, and normalized them into a compact outcome record."
            ),
            confidence=93,
            latency_ms=120,
        ),
        TraceStep(
            stage="02",
            title="Outcome model judged how much the matcher should learn",
            summary=(
                f"Combined the submissions into a match update score of {score}, separating polite "
                "dates from strong future matching signal."
            ),
            confidence=max(70, score - 4),
            latency_ms=210,
        ),
        TraceStep(
            stage="03",
            title="Safety and consent policy gated the next action",
            summary=(
                "Checked whether a second-date nudge would feel welcome, or whether the system "
                "should learn quietly and keep the visible user flow unchanged."
            ),
            confidence=90,
            latency_ms=90,
        ),
        TraceStep(
            stage="04",
            title="Matcher memory and rank features were rewritten",
            summary=(
                f"Persisted user memory and emitted trace events after a {finalized_reason} finalization path."
            ),
            confidence=88,
            latency_ms=85,
        ),
    ]


def _memory_updates_for_submission(
    context: MatchContext,
    submission: DebriefSubmission,
    score: int,
) -> list[MemoryUpdate]:
    conversation_style = (
        "high-ambition banter"
        if submission.curiosity is CuriositySignal.OBSESSED
        else "slower conversational ramp"
    )
    venue_preference = (
        "very public, low-pressure spots"
        if submission.comfort is ComfortSignal.GUARDED
        else f"walk + anchor venue near {context.venue_name}"
    )
    match_archetype = (
        "agents with momentum"
        if submission.energy is EnergySignal.CHARGED
        else "steadier personalities"
    )

    return [
        MemoryUpdate(
            user_id=submission.user_id,
            field_name="conversation_style",
            before="playful openers",
            after=conversation_style,
            rationale="Real date signal beat static onboarding preference.",
        ),
        MemoryUpdate(
            user_id=submission.user_id,
            field_name="venue_preference",
            before="generic campus cafes",
            after=venue_preference,
            rationale="The system stores what setting felt best after a real date.",
        ),
        MemoryUpdate(
            user_id=submission.user_id,
            field_name="match_archetype",
            before="broad curiosity cluster",
            after=match_archetype,
            rationale=f"Outcome-derived score {score} should influence future retrieval.",
        ),
    ]


def _build_follow_up_decision(
    context: MatchContext,
    submissions: list[DebriefSubmission],
    score: int,
    rating_spread: int,
    finalized_reason: str,
) -> FollowUpDecision:
    any_no = any(s.follow_up_intent is FollowUpIntent.NO for s in submissions)
    if (
        score >= 76
        and not any_no
        and rating_spread < 3
        and finalized_reason != "timeout"
        and len(submissions) == 2
    ):
        average_rating = round(sum(sub.date_rating for sub in submissions) / len(submissions), 1)
        user_ids = " and ".join(sub.user_id for sub in submissions)
        return FollowUpDecision(
            action=FollowUpAction.OFFER_SECOND_DATE,
            summary=(
                "The rating signal and lighter debrief indicate enough traction to reuse inside "
                "the existing follow-up flow."
            ),
            suggested_copy=[
                f"Ditto: sounds like {user_ids} had real momentum ({average_rating}/5 avg).",
                f"I can tee up a second plan near {context.venue_name} this weekend.",
            ],
        )

    return FollowUpDecision(
        action=FollowUpAction.QUIET_LEARN,
        summary=(
            "The harness should update matcher memory but avoid any extra user-facing step."
        ),
        suggested_copy=[
            "No second-date nudge is sent.",
            "The signal is still written back into future matching memory.",
        ],
    )


def evaluate_match(
    context: MatchContext,
    submissions: list[DebriefSubmission],
    finalized_reason: str = "complete",
) -> MatchOutcome:
    avg_rating = _mean(sub.date_rating for sub in submissions)
    avg_curiosity = _mean(_score_curiosity(sub.curiosity) for sub in submissions)
    avg_comfort = _mean(_score_comfort(sub.comfort) for sub in submissions)
    avg_energy = _mean(_score_energy(sub.energy) for sub in submissions)
    avg_follow_up = _mean(_score_follow_up(sub.follow_up_intent) for sub in submissions)

    ratings = [sub.date_rating for sub in submissions]
    rating_spread = max(ratings) - min(ratings)
    conflict_flag = rating_spread >= 2

    score = round(
        _score_rating(round(avg_rating)) * MATCH_WEIGHTS["rating"]
        + avg_curiosity * MATCH_WEIGHTS["curiosity"]
        + avg_comfort * MATCH_WEIGHTS["comfort"]
        + avg_energy * MATCH_WEIGHTS["energy"]
        + avg_follow_up * MATCH_WEIGHTS["follow_up"]
        - (12 if len(submissions) == 1 else 0)
        - (10 if conflict_flag else 0)
    )

    memory_updates: list[MemoryUpdate] = []
    for submission in submissions:
        memory_updates.extend(_memory_updates_for_submission(context, submission, score))

    return MatchOutcome(
        match_id=context.match_id,
        participant_count=len(submissions),
        match_update_score=max(0, score),
        average_rating=round(avg_rating, 2),
        rating_spread=rating_spread,
        conflict_flag=conflict_flag,
        finalized_reason=finalized_reason,
        follow_up_decision=_build_follow_up_decision(
            context,
            submissions,
            max(0, score),
            rating_spread,
            finalized_reason,
        ),
        memory_updates=memory_updates,
        trace=_build_trace(submissions, max(0, score), finalized_reason),
    )
