from __future__ import annotations

from pathlib import Path

from .evals import run_eval_fixtures
from .runtime import DEFAULT_FIXTURE_PATH, build_debrief_submission, build_match_context, build_service


def run_demo(
    *,
    db_path: str | Path,
    keep_db: bool = False,
    fixture_path: str | Path = DEFAULT_FIXTURE_PATH,
) -> dict[str, object]:
    db_path = Path(db_path)
    if db_path.exists() and not keep_db:
        db_path.unlink()

    service = build_service(db_path)
    context = build_match_context(
        match_id="match-berkeley-001",
        user_a_id="avery",
        user_b_id="lena",
        venue_name="Campanile sunset loop",
        completed_at="now",
    )
    register = service.register_match(context)
    open_check_in = service.open_check_in_window(context.match_id)
    pending = service.submit_debrief(
        build_debrief_submission(
            match_id=context.match_id,
            user_id="avery",
            date_rating=4,
            energy="charged",
            curiosity="obsessed",
            comfort="open",
            follow_up_intent="yes",
            note="The conversation got better when we stopped trying to be cool.",
        )
    )
    finalized = service.submit_debrief(
        build_debrief_submission(
            match_id=context.match_id,
            user_id="lena",
            date_rating=5,
            energy="charged",
            curiosity="interested",
            comfort="fully-safe",
            follow_up_intent="yes",
            note="Would absolutely go again.",
        )
    )

    payload = {
        "register": register,
        "open_check_in": open_check_in,
        "pending": pending,
        "finalized": finalized,
        "operator_outcomes": service.list_latest_outcomes(),
        "global_memory": service.get_global_memory_snapshot(),
        "evals": run_eval_fixtures(Path(fixture_path)),
    }

    if not keep_db and db_path.exists():
        db_path.unlink()
    return payload
