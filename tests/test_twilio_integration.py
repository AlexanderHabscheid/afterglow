from __future__ import annotations

import os
import unittest

from afterglow.models import ComfortSignal, CuriositySignal, EnergySignal, FollowUpIntent
from afterglow.sms import SMSReplyNormalizer
from afterglow.twilio import TwilioConfig, parse_afterglow_reply


class TwilioIntegrationTests(unittest.TestCase):
    def test_sms_reply_normalizer_accepts_enum_instances(self) -> None:
        payload = SMSReplyNormalizer().normalize(
            {
                "match_id": "match-003",
                "user_id": "avery",
                "rating": 4,
                "energy": EnergySignal.STEADY,
                "curiosity": CuriositySignal.INTERESTED,
                "comfort": ComfortSignal.OPEN,
                "follow_up_intent": FollowUpIntent.YES,
                "note": "Still interested.",
            }
        )

        self.assertEqual(payload.match_id, "match-003")
        self.assertEqual(payload.energy, EnergySignal.STEADY)
        self.assertEqual(payload.follow_up_intent, FollowUpIntent.YES)

    def test_parses_compact_sms_reply_with_phone_lookup(self) -> None:
        payload = parse_afterglow_reply(
            "5 charged interested open yes",
            from_number="+15550001001",
            phone_to_user={"avery": "+15550001001"},
            default_match_id="match-001",
        )

        self.assertEqual(payload["match_id"], "match-001")
        self.assertEqual(payload["user_id"], "avery")
        self.assertEqual(payload["rating"], 5)
        self.assertEqual(payload["follow_up_intent"], "yes")

    def test_parses_key_value_reply(self) -> None:
        payload = parse_afterglow_reply(
            "match=match-002 user=lena rating=4 energy=steady curiosity=interested comfort=open follow=maybe",
        )

        self.assertEqual(payload["match_id"], "match-002")
        self.assertEqual(payload["user_id"], "lena")
        self.assertEqual(payload["follow_up_intent"], "maybe")

    def test_twilio_config_requires_real_credentials(self) -> None:
        previous = {key: os.environ.get(key) for key in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN")}
        os.environ.pop("TWILIO_ACCOUNT_SID", None)
        os.environ.pop("TWILIO_AUTH_TOKEN", None)
        try:
            with self.assertRaises(RuntimeError):
                TwilioConfig.from_env()
        finally:
            for key, value in previous.items():
                if value is not None:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
