from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from afterglow.models import (
    ComfortSignal,
    CuriositySignal,
    DebriefSubmission,
    EnergySignal,
    FollowUpIntent,
    MatchContext,
)
from afterglow.service import AfterglowService
from afterglow.sms import CheckInMessage
from afterglow.twilio import TwilioConfig, TwilioSMSClient, build_phone_map_from_env


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "afterglow.db"


def banner(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def emit(label: str, payload: object) -> None:
    print(f"\n[{label}]")
    print(json.dumps(payload, indent=2))


def explain_flow() -> None:
    print(
        """
Existing Ditto flow
  -> date completed
  -> Afterglow opens a tiny check-in
  -> SMS outbox queues provider-ready messages
  -> debrief replies become structured matching signals
  -> user memory + pair memory + global rank features update
  -> operator trace explains the decision
""".strip()
    )


def send_twilio_messages(service: AfterglowService, queued_messages: list[dict[str, object]]) -> None:
    phone_map = build_phone_map_from_env()
    client = TwilioSMSClient(TwilioConfig.from_env())

    banner("LIVE TWILIO SEND")
    for message in queued_messages:
        recipient_id = str(message["recipient_id"])
        to_phone = phone_map.get(recipient_id)
        if not to_phone:
            raise RuntimeError(f"Set AFTERGLOW_PHONE_{recipient_id.upper()} for live Twilio send.")

        receipt = client.send(
            CheckInMessage(
                match_id=str(message["match_id"]),
                recipient_id=recipient_id,
                channel=str(message["channel"]),
                body=str(message["body"]),
            ),
            to_phone_number=to_phone,
        )
        persisted = service.mark_check_in_message_sent(
            int(message["id"]),
            provider_message_id=receipt.sid,
            provider_status=receipt.status,
        )
        emit(f"sent to {recipient_id}", persisted)


def main() -> None:
    parser = argparse.ArgumentParser(description="Show the Afterglow harness in one terminal run.")
    parser.add_argument("--send-twilio", action="store_true", help="Send queued check-ins through Twilio.")
    parser.add_argument("--keep-db", action="store_true", help="Keep the SQLite DB for API/Twilio webhook demos.")
    args = parser.parse_args()

    if DEFAULT_DB_PATH.exists() and not args.keep_db:
        DEFAULT_DB_PATH.unlink()

    service = AfterglowService(db_path=DEFAULT_DB_PATH)
    context = MatchContext(
        match_id="match-terminal-demo",
        user_a_id="avery",
        user_b_id="lena",
        venue_name="Campanile sunset loop",
        completed_at=datetime.now(UTC),
    )

    banner("AFTERGLOW: POST-DATE LEARNING HARNESS")
    explain_flow()

    emit("1. Ditto registers a completed date", service.register_match(context))
    check_in = service.open_check_in_window(context.match_id)
    emit("2. Afterglow queues provider-ready SMS check-ins", check_in)

    if args.send_twilio:
        send_twilio_messages(service, list(check_in["queued_messages"]))  # type: ignore[arg-type]
    else:
        print("\n[Twilio]")
        print("Live send skipped. Add --send-twilio with Twilio env vars to send real SMS.")

    first = service.submit_debrief(
        DebriefSubmission(
            match_id=context.match_id,
            user_id="avery",
            date_rating=4,
            energy=EnergySignal.CHARGED,
            curiosity=CuriositySignal.OBSESSED,
            comfort=ComfortSignal.OPEN,
            follow_up_intent=FollowUpIntent.YES,
            note="The conversation got better when we stopped trying to be cool.",
        )
    )
    emit("3. One reply arrives: system waits instead of overreacting", first)

    second = service.submit_debrief(
        DebriefSubmission(
            match_id=context.match_id,
            user_id="lena",
            date_rating=5,
            energy=EnergySignal.CHARGED,
            curiosity=CuriositySignal.INTERESTED,
            comfort=ComfortSignal.FULLY_SAFE,
            follow_up_intent=FollowUpIntent.YES,
            note="Would absolutely go again.",
        )
    )
    emit("4. Both replies arrive: matcher memory updates", second)
    emit("5. Operator trace", service.get_trace(context.match_id))
    emit("6. Global ranking memory", service.get_global_memory_snapshot())

    banner("VIDEO CLOSE")
    print(
        "The user saw one tiny text. The platform got a ranked outcome, consent-aware "
        "follow-up action, durable memory updates, and an inspectable trace."
    )
    if DEFAULT_DB_PATH.exists() and not args.keep_db:
        DEFAULT_DB_PATH.unlink()


if __name__ == "__main__":
    main()
