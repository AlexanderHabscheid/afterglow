from __future__ import annotations

import json
import os
import shlex
from base64 import b64encode
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .sms import CheckInMessage


@dataclass(frozen=True, slots=True)
class TwilioConfig:
    account_sid: str
    auth_token: str
    from_number: str | None = None
    messaging_service_sid: str | None = None
    status_callback: str | None = None

    @classmethod
    def from_env(cls) -> "TwilioConfig":
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_FROM_NUMBER")
        messaging_service_sid = os.environ.get("TWILIO_MESSAGING_SERVICE_SID")

        if not account_sid or not auth_token:
            raise RuntimeError("Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.")
        if not from_number and not messaging_service_sid:
            raise RuntimeError("Set TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID.")

        return cls(
            account_sid=account_sid,
            auth_token=auth_token,
            from_number=from_number,
            messaging_service_sid=messaging_service_sid,
            status_callback=os.environ.get("TWILIO_STATUS_CALLBACK_URL"),
        )


@dataclass(frozen=True, slots=True)
class TwilioSendReceipt:
    sid: str
    status: str
    to: str
    direction: str


class TwilioSMSClient:
    def __init__(self, config: TwilioConfig) -> None:
        self.config = config

    def send(self, message: CheckInMessage, to_phone_number: str) -> TwilioSendReceipt:
        form = {
            "To": to_phone_number,
            "Body": message.body,
        }
        if self.config.messaging_service_sid:
            form["MessagingServiceSid"] = self.config.messaging_service_sid
        else:
            form["From"] = self.config.from_number or ""
        if self.config.status_callback:
            form["StatusCallback"] = self.config.status_callback

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.config.account_sid}/Messages.json"
        encoded_auth = b64encode(f"{self.config.account_sid}:{self.config.auth_token}".encode()).decode()
        request = Request(
            url,
            data=urlencode(form).encode(),
            headers={
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode())
        except HTTPError as error:
            detail = error.read().decode()
            raise RuntimeError(f"Twilio rejected the message: {detail}") from error

        return TwilioSendReceipt(
            sid=str(payload.get("sid", "")),
            status=str(payload.get("status", "")),
            to=str(payload.get("to", to_phone_number)),
            direction=str(payload.get("direction", "")),
        )


def build_phone_map_from_env(prefix: str = "AFTERGLOW_PHONE_") -> dict[str, str]:
    return {
        key.removeprefix(prefix).lower(): value
        for key, value in os.environ.items()
        if key.startswith(prefix) and value
    }


def parse_afterglow_reply(
    body: str,
    *,
    from_number: str = "",
    phone_to_user: dict[str, str] | None = None,
    default_match_id: str | None = None,
) -> dict[str, object]:
    tokens = shlex.split(body)
    fields: dict[str, str] = {}
    aliases = {
        "match": "match_id",
        "user": "user_id",
        "follow": "follow_up_intent",
        "follow_up": "follow_up_intent",
        "date_rating": "rating",
    }

    for token in tokens:
        if "=" in token:
            raw_key, raw_value = token.split("=", 1)
            key = aliases.get(raw_key.strip().lower(), raw_key.strip().lower())
            fields[key] = raw_value.strip()

    if not fields and len(tokens) >= 5:
        fields.update(
            {
                "rating": tokens[0],
                "energy": tokens[1],
                "curiosity": tokens[2],
                "comfort": tokens[3],
                "follow_up_intent": tokens[4],
                "note": " ".join(tokens[5:]),
            }
        )

    reverse_phone_map = {phone: user_id for user_id, phone in (phone_to_user or {}).items()}
    match_id = fields.get("match_id") or default_match_id
    user_id = fields.get("user_id") or reverse_phone_map.get(from_number)
    required = ("rating", "energy", "curiosity", "comfort", "follow_up_intent")
    missing = [key for key in required if not fields.get(key)]
    if not match_id:
        missing.append("match_id")
    if not user_id:
        missing.append("user_id")
    if missing:
        raise ValueError(f"Reply missing: {', '.join(missing)}")

    return {
        "match_id": match_id,
        "user_id": user_id,
        "rating": int(fields["rating"]),
        "energy": fields["energy"],
        "curiosity": fields["curiosity"],
        "comfort": fields["comfort"],
        "follow_up_intent": fields["follow_up_intent"],
        "note": fields.get("note", ""),
    }
