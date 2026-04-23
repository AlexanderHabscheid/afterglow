from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import tempfile

from .models import (
    ComfortSignal,
    CuriositySignal,
    DebriefSubmission,
    EnergySignal,
    FollowUpIntent,
    MatchContext,
)
from .service import AfterglowService


def run_eval_fixtures(fixture_path: str | Path) -> list[dict[str, object]]:
    fixture_path = Path(fixture_path)
    scenarios = json.loads(fixture_path.read_text())
    results: list[dict[str, object]] = []

    for scenario in scenarios:
        with tempfile.NamedTemporaryFile(suffix=".db") as handle:
            service = AfterglowService(db_path=handle.name)
            context = MatchContext(
                match_id=scenario["match"]["match_id"],
                user_a_id=scenario["match"]["user_a_id"],
                user_b_id=scenario["match"]["user_b_id"],
                venue_name=scenario["match"]["venue_name"],
                completed_at=datetime.fromisoformat(scenario["match"]["completed_at"]),
            )
            service.register_match(context)

            for submission in scenario["submissions"]:
                service.submit_debrief(
                    DebriefSubmission(
                        match_id=context.match_id,
                        user_id=submission["user_id"],
                        date_rating=submission["date_rating"],
                        energy=EnergySignal(submission["energy"]),
                        curiosity=CuriositySignal(submission["curiosity"]),
                        comfort=ComfortSignal(submission["comfort"]),
                        follow_up_intent=FollowUpIntent(submission["follow_up_intent"]),
                        note=submission.get("note", ""),
                    )
                )

            if scenario.get("finalize_reason"):
                outcome = service.finalize_match(context.match_id, reason=scenario["finalize_reason"])
            else:
                outcome = service.get_match_summary(context.match_id)["outcome"]

            passed = (
                outcome["follow_up_action"] == scenario["expected"]["follow_up_action"]
                and outcome["finalized_reason"] == scenario["expected"]["finalized_reason"]
                and outcome["conflict_flag"] == scenario["expected"]["conflict_flag"]
            )

            results.append(
                {
                    "name": scenario["name"],
                    "passed": passed,
                    "outcome": outcome,
                    "expected": scenario["expected"],
                }
            )

    return results
