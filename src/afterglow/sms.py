from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import (
    ComfortSignal,
    CuriositySignal,
    DebriefSubmission,
    EnergySignal,
    FollowUpIntent,
    MatchContext,
)


@dataclass(frozen=True, slots=True)
class CheckInMessage:
    match_id: str
    recipient_id: str
    channel: str
    body: str


class CheckInMessageComposer:
    def build_messages(self, context: MatchContext) -> list[CheckInMessage]:
        body = (
            "Quick Afterglow check-in: rate the date 1-5, then share energy, "
            "curiosity, comfort, and whether Ditto should nudge date two."
        )
        return [
            CheckInMessage(
                match_id=context.match_id,
                recipient_id=recipient_id,
                channel="sms",
                body=body,
            )
            for recipient_id in (context.user_a_id, context.user_b_id)
        ]


class SMSReplyNormalizer:
    @staticmethod
    def _enum_value(value: object) -> str:
        if isinstance(value, Enum):
            return str(value.value)
        return str(value)

    def normalize(self, payload: dict[str, object]) -> DebriefSubmission:
        rating = payload.get("rating", payload.get("date_rating"))
        if rating is None:
            raise ValueError("SMS reply payload must include rating or date_rating.")

        return DebriefSubmission(
            match_id=str(payload["match_id"]),
            user_id=str(payload["user_id"]),
            date_rating=int(rating),  # type: ignore[arg-type]
            energy=EnergySignal(self._enum_value(payload["energy"])),
            curiosity=CuriositySignal(self._enum_value(payload["curiosity"])),
            comfort=ComfortSignal(self._enum_value(payload["comfort"])),
            follow_up_intent=FollowUpIntent(self._enum_value(payload["follow_up_intent"])),
            note=str(payload.get("note", "")),
        )
