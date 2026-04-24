from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .models import (
    ComfortSignal,
    CuriositySignal,
    DebriefSubmission,
    EnergySignal,
    FollowUpIntent,
    MatchContext,
)
from .interactive_surface import build_check_in_demo_html
from .product_surface import build_founder_demo_html
from .service import AfterglowService
from .twilio import build_phone_map_from_env, parse_afterglow_reply

DB_PATH = Path(__file__).resolve().parents[2] / "afterglow.db"
service = AfterglowService(db_path=DB_PATH)
app = FastAPI(title="Afterglow API", version="0.2.0")
logger = logging.getLogger("afterglow.twilio")


class MatchRegistrationPayload(BaseModel):
    match_id: str
    user_a_id: str
    user_b_id: str
    venue_name: str
    completed_at: datetime


class DebriefPayload(BaseModel):
    match_id: str
    user_id: str
    date_rating: int = Field(ge=1, le=5)
    energy: EnergySignal
    curiosity: CuriositySignal
    comfort: ComfortSignal
    follow_up_intent: FollowUpIntent
    note: str = ""


class SMSReplyPayload(BaseModel):
    match_id: str
    user_id: str
    rating: int = Field(ge=1, le=5)
    energy: EnergySignal
    curiosity: CuriositySignal
    comfort: ComfortSignal
    follow_up_intent: FollowUpIntent
    note: str = ""


class FinalizePayload(BaseModel):
    reason: str = "timeout"


class ProviderDeliveryPayload(BaseModel):
    provider_message_id: str | None = None
    provider_status: str | None = None


def _print_check_in_result(*, channel: str, user_id: str, result: dict[str, object]) -> None:
    status = str(result.get("status", "unknown"))
    match_id = str(result.get("match_id", "unknown"))
    lines = [
        "",
        "================ AFTERGLOW CHECK-IN ================",
        f"channel: {channel}",
        f"user:    {user_id}",
        f"match:   {match_id}",
        f"status:  {status}",
    ]

    if status == "finalized":
        lines.extend(
            [
                f"score:   {result.get('match_update_score')}",
                f"average: {result.get('average_rating')}",
                f"action:  {result.get('follow_up_action')}",
                f"reason:  {result.get('finalized_reason')}",
            ]
        )
        summary = result.get("follow_up_summary")
        if summary:
            lines.append(f"summary: {summary}")
        lines.append("===================================================")
        print("\n".join(lines), flush=True)
        return

    lines.extend(
        [
            f"count:   {result.get('received_submissions', 0)} submission(s)",
            f"message: {result.get('message', '')}",
            "===================================================",
        ]
    )
    print("\n".join(lines), flush=True)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/demo/founder-surface", response_class=HTMLResponse)
def founder_surface() -> HTMLResponse:
    return HTMLResponse(build_founder_demo_html())


@app.get("/demo/check-in", response_class=HTMLResponse)
def check_in_surface() -> HTMLResponse:
    return HTMLResponse(build_check_in_demo_html())


@app.post("/demo/check-in/session")
def create_demo_check_in_session() -> dict[str, object]:
    match_id = f"match-demo-ui-{uuid4().hex[:8]}"
    context = MatchContext(
        match_id=match_id,
        user_a_id="avery",
        user_b_id="lena",
        venue_name="Campanile sunset loop",
        completed_at=datetime.now(UTC),
    )
    service.register_match(context)
    queued = service.open_check_in_window(match_id)
    return {
        "status": "session-created",
        "match_id": match_id,
        "user_ids": [context.user_a_id, context.user_b_id],
        "queued_messages": queued["queued_messages"],
    }


@app.post("/matches/register")
def register_match(payload: MatchRegistrationPayload) -> dict[str, object]:
    context = MatchContext(**payload.model_dump())
    return service.register_match(context)


@app.post("/matches/{match_id}/check-in")
def open_check_in(match_id: str) -> dict[str, object]:
    return service.open_check_in_window(match_id)


@app.post("/debriefs")
def submit_debrief(payload: DebriefPayload) -> dict[str, object]:
    submission = DebriefSubmission(**payload.model_dump())
    result = service.submit_debrief(submission)
    _print_check_in_result(channel="ui", user_id=submission.user_id, result=result)
    return result


@app.post("/debriefs/sms-reply")
def submit_sms_reply(payload: SMSReplyPayload) -> dict[str, object]:
    result = service.receive_sms_reply(payload.model_dump())
    _print_check_in_result(channel="sms-api", user_id=payload.user_id, result=result)
    return result


@app.get("/integrations/sms/outbox")
def list_sms_outbox(
    match_id: str | None = None,
    status: str | None = "queued",
    limit: int = 50,
) -> list[dict[str, object]]:
    return service.list_check_in_messages(match_id=match_id, status=status, limit=limit)


@app.post("/integrations/sms/outbox/{message_id}/sent")
def mark_sms_message_sent(
    message_id: int,
    payload: ProviderDeliveryPayload | None = None,
) -> dict[str, object]:
    payload = payload or ProviderDeliveryPayload()
    return service.mark_check_in_message_sent(
        message_id,
        provider_message_id=payload.provider_message_id,
        provider_status=payload.provider_status,
    )


@app.post("/integrations/twilio/inbound")
async def receive_twilio_inbound(request: Request) -> Response:
    raw_body = (await request.body()).decode()
    form = {key: values[0] for key, values in parse_qs(raw_body).items()}
    sender = form.get("From", "")
    message_body = form.get("Body", "")
    logger.info("Twilio inbound SMS from=%s body=%s", sender, message_body)
    print(f"[twilio inbound] from={sender} body={message_body}", flush=True)

    try:
        payload = parse_afterglow_reply(
            message_body,
            from_number=sender,
            phone_to_user=build_phone_map_from_env(),
            default_match_id=os.environ.get("AFTERGLOW_ACTIVE_MATCH_ID"),
        )
        result = service.receive_sms_reply(payload)
        logger.info("Afterglow processed Twilio reply result=%s", result.get("status"))
        _print_check_in_result(
            channel="twilio",
            user_id=str(payload.get("user_id", "unknown")),
            result=result,
        )
        twiml = "<Response><Message>Got it. Afterglow saved your check-in.</Message></Response>"
    except Exception as error:
        logger.exception("Afterglow could not process Twilio reply")
        twiml = (
            "<Response><Message>"
            "I could not read that yet. Reply like: 5 charged interested open yes"
            f" ({type(error).__name__})"
            "</Message></Response>"
        )

    return Response(content=twiml, media_type="application/xml")


@app.post("/matches/{match_id}/finalize")
def finalize_match(match_id: str, payload: FinalizePayload) -> dict[str, object]:
    return service.finalize_match(match_id, reason=payload.reason)


@app.get("/operator/outcomes")
def list_latest_outcomes(limit: int = 10) -> list[dict[str, object]]:
    return service.list_latest_outcomes(limit=limit)


@app.get("/operator/matches/{match_id}")
def get_match(match_id: str) -> dict[str, object]:
    return service.get_match_summary(match_id)


@app.get("/operator/matches/{match_id}/trace")
def get_trace(match_id: str) -> list[dict[str, object]]:
    return service.get_trace(match_id)


@app.get("/operator/memory/users/{user_id}")
def get_user_memory(user_id: str) -> dict[str, object]:
    return service.get_user_memory_snapshot(user_id)


@app.get("/operator/memory/pairs/{match_id}")
def get_pair_memory(match_id: str) -> dict[str, object] | None:
    return service.get_pair_memory_snapshot(match_id)


@app.get("/operator/memory/global")
def get_global_memory() -> dict[str, object]:
    return service.get_global_memory_snapshot()
