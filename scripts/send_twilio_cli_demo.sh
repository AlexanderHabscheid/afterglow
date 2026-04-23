#!/usr/bin/env bash
set -euo pipefail

PROFILE="${TWILIO_PROFILE:-norma}"
FROM_NUMBER="${TWILIO_FROM_NUMBER:-}"
TO_NUMBER="${AFTERGLOW_DEMO_PHONE:-+19894934411}"
BODY="${AFTERGLOW_DEMO_BODY:-Quick Afterglow check-in: rate the date 1-5, then share energy, curiosity, comfort, and whether Ditto should nudge date two.}"

if [[ -z "$FROM_NUMBER" ]]; then
  echo "Set TWILIO_FROM_NUMBER to a real Twilio SMS number on profile '$PROFILE'." >&2
  exit 1
fi

twilio api:core:messages:create \
  -p "$PROFILE" \
  --from "$FROM_NUMBER" \
  --to "$TO_NUMBER" \
  --body "$BODY" \
  -o json
