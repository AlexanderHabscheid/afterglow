from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evals import run_eval_fixtures
from .runtime import (
    DEFAULT_DB_PATH,
    DEFAULT_FIXTURE_PATH,
    build_debrief_submission,
    build_match_context,
    build_service,
)


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2))


def _db_path(value: str | None) -> Path:
    return Path(value) if value else DEFAULT_DB_PATH


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="afterglow",
        description="Afterglow CLI for Ditto-style post-date learning workflows.",
    )
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))

    subparsers = parser.add_subparsers(dest="command", required=True)

    register = subparsers.add_parser("register-match", help="Register a completed date.")
    register.add_argument("--match-id", required=True)
    register.add_argument("--user-a-id", required=True)
    register.add_argument("--user-b-id", required=True)
    register.add_argument("--venue-name", required=True)
    register.add_argument("--completed-at", default="now")

    check_in = subparsers.add_parser("open-check-in", help="Queue post-date check-in messages.")
    check_in.add_argument("--match-id", required=True)

    debrief = subparsers.add_parser("submit-debrief", help="Submit one user debrief.")
    debrief.add_argument("--match-id", required=True)
    debrief.add_argument("--user-id", required=True)
    debrief.add_argument("--date-rating", type=int, required=True)
    debrief.add_argument("--energy", required=True, choices=["drained", "steady", "charged"])
    debrief.add_argument("--curiosity", required=True, choices=["flat", "interested", "obsessed"])
    debrief.add_argument("--comfort", required=True, choices=["guarded", "open", "fully-safe"])
    debrief.add_argument("--follow-up-intent", required=True, choices=["no", "maybe", "yes"])
    debrief.add_argument("--note", default="")

    inbound = subparsers.add_parser("receive-sms", help="Normalize and ingest an SMS-style payload.")
    inbound.add_argument("--match-id", required=True)
    inbound.add_argument("--user-id", required=True)
    inbound.add_argument("--rating", type=int, required=True)
    inbound.add_argument("--energy", required=True, choices=["drained", "steady", "charged"])
    inbound.add_argument("--curiosity", required=True, choices=["flat", "interested", "obsessed"])
    inbound.add_argument("--comfort", required=True, choices=["guarded", "open", "fully-safe"])
    inbound.add_argument("--follow-up-intent", required=True, choices=["no", "maybe", "yes"])
    inbound.add_argument("--note", default="")

    finalize = subparsers.add_parser("finalize-match", help="Finalize a match explicitly.")
    finalize.add_argument("--match-id", required=True)
    finalize.add_argument("--reason", default="timeout")

    match = subparsers.add_parser("get-match", help="Fetch one match summary.")
    match.add_argument("--match-id", required=True)

    trace = subparsers.add_parser("get-trace", help="Fetch the internal reasoning trace.")
    trace.add_argument("--match-id", required=True)

    outbox = subparsers.add_parser("list-outbox", help="List queued or sent SMS work.")
    outbox.add_argument("--match-id")
    outbox.add_argument("--status")
    outbox.add_argument("--limit", type=int, default=50)

    mark_sent = subparsers.add_parser("mark-sent", help="Acknowledge provider delivery.")
    mark_sent.add_argument("--message-id", type=int, required=True)
    mark_sent.add_argument("--provider-message-id")
    mark_sent.add_argument("--provider-status")

    global_memory = subparsers.add_parser("get-global-memory", help="Fetch global ranking state.")

    outcomes = subparsers.add_parser("list-outcomes", help="List recent finalized outcomes.")
    outcomes.add_argument("--limit", type=int, default=10)

    evals = subparsers.add_parser("run-evals", help="Run fixture-based evaluation scenarios.")
    evals.add_argument("--fixture-path", default=str(DEFAULT_FIXTURE_PATH))

    demo = subparsers.add_parser("demo", help="Run the happy-path terminal demonstration.")
    demo.add_argument("--keep-db", action="store_true")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    db_path = _db_path(args.db_path)

    if args.command == "demo":
        from .demo import run_demo

        _print(run_demo(db_path=db_path, keep_db=args.keep_db))
        return

    service = build_service(db_path)

    if args.command == "register-match":
        payload = service.register_match(
            build_match_context(
                match_id=args.match_id,
                user_a_id=args.user_a_id,
                user_b_id=args.user_b_id,
                venue_name=args.venue_name,
                completed_at=args.completed_at,
            )
        )
    elif args.command == "open-check-in":
        payload = service.open_check_in_window(args.match_id)
    elif args.command == "submit-debrief":
        payload = service.submit_debrief(
            build_debrief_submission(
                match_id=args.match_id,
                user_id=args.user_id,
                date_rating=args.date_rating,
                energy=args.energy,
                curiosity=args.curiosity,
                comfort=args.comfort,
                follow_up_intent=args.follow_up_intent,
                note=args.note,
            )
        )
    elif args.command == "receive-sms":
        payload = service.receive_sms_reply(
            {
                "match_id": args.match_id,
                "user_id": args.user_id,
                "rating": args.rating,
                "energy": args.energy,
                "curiosity": args.curiosity,
                "comfort": args.comfort,
                "follow_up_intent": args.follow_up_intent,
                "note": args.note,
            }
        )
    elif args.command == "finalize-match":
        payload = service.finalize_match(args.match_id, reason=args.reason)
    elif args.command == "get-match":
        payload = service.get_match_summary(args.match_id)
    elif args.command == "get-trace":
        payload = service.get_trace(args.match_id)
    elif args.command == "list-outbox":
        payload = service.list_check_in_messages(
            match_id=args.match_id,
            status=args.status,
            limit=args.limit,
        )
    elif args.command == "mark-sent":
        payload = service.mark_check_in_message_sent(
            args.message_id,
            provider_message_id=args.provider_message_id,
            provider_status=args.provider_status,
        )
    elif args.command == "get-global-memory":
        payload = service.get_global_memory_snapshot()
    elif args.command == "list-outcomes":
        payload = service.list_latest_outcomes(limit=args.limit)
    elif args.command == "run-evals":
        payload = run_eval_fixtures(Path(args.fixture_path))
    else:
        parser.error(f"Unknown command: {args.command}")
        return

    _print(payload)


if __name__ == "__main__":
    main()
