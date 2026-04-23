# Afterglow

Afterglow is a Python harness service for a Ditto-style dating system.

It is not a standalone app. It plugs into the existing matching, scheduling, and SMS loop:

1. a date happens inside the existing system
2. each person gives a tiny post-date rating and debrief
3. Afterglow converts that into a structured outcome label
4. matcher memory and ranking features are updated
5. the system optionally nudges a second date
6. an internal trace is emitted for operators

## Why this version is stronger

This project now includes the infrastructure pieces that make the idea feel real:

- `FastAPI` integration surface
- `SQLite` persistence
- messy-case handling:
  - one user submits, the other never does
  - conflicting ratings
  - low rating but high follow-up intent
  - timeout finalization
  - duplicate submissions
  - idempotent intake
- pair-level, user-level, and global ranking state
- operator tooling endpoints
- provider-neutral SMS outbox and inbound reply normalization
- scenario-based evaluation fixtures

## Project structure

- `src/afterglow/models.py`
  Domain models for matches, debriefs, pair outcomes, memory layers, traces, and operator summaries.
- `src/afterglow/repository.py`
  SQLite repository with schema creation, idempotent submission storage, pair outcomes, memories, global features, and traces.
- `src/afterglow/engine.py`
  Scoring logic, conflict handling, timeout behavior, memory updates, and follow-up decisions.
- `src/afterglow/service.py`
  Orchestration layer for match registration, check-in opening, debrief intake, finalization, operator reads, and persistence.
- `src/afterglow/api.py`
  `FastAPI` app exposing user-facing and operator-facing endpoints.
- `src/afterglow/sms.py`
  Message composer and inbound reply normalizer for the text-first integration boundary.
- `src/afterglow/outbox.py`
  SQLite-backed SMS outbox that a real Ditto texting worker can consume and mark sent.
- `src/afterglow/evals.py`
  Fixture runner for scenario-based evaluations.
- `tests/fixtures/eval_scenarios.json`
  Realistic evaluation scenarios.
- `tests/test_afterglow_service.py`
  Service behavior and messy-case tests.
- `tests/test_eval_fixtures.py`
  Fixture-level evaluation assertions.

## Core idea

The best new signal is not another profile field. It is what happened after the real date.

Afterglow uses:

- a `1-5` date rating from each person
- lightweight signals:
  - energy
  - curiosity
  - comfort
  - follow-up intent
- existing system context:
  - venue
  - schedule completion
  - match metadata

Then it produces:

- a pair-level match update score
- a second-date recommendation or suppression
- user memory updates
- pair outcome history
- global ranking feature updates
- a full internal trace

## FastAPI surface

The API is intentionally small:

- `POST /matches/register`
- `POST /matches/{match_id}/check-in`
- `POST /debriefs`
- `POST /debriefs/sms-reply`
- `GET /integrations/sms/outbox`
- `POST /integrations/sms/outbox/{message_id}/sent`
- `POST /matches/{match_id}/finalize`
- `GET /operator/outcomes`
- `GET /operator/matches/{match_id}`
- `GET /operator/matches/{match_id}/trace`
- `GET /operator/memory/users/{user_id}`
- `GET /operator/memory/pairs/{match_id}`
- `GET /operator/memory/global`

This is enough to demonstrate infrastructure thinking without overbuilding.

## How it plugs into an existing Ditto ecosystem

- `register_match(...)`
  Called when the existing schedule/match flow marks a date as scheduled or completed.
- `open_check_in_window(...)`
  Writes provider-ready check-in messages into the durable SMS outbox.
- `GET /integrations/sms/outbox`
  Lets the existing Ditto texting worker pull queued messages and deliver them through the live provider.
- `POST /integrations/sms/outbox/{message_id}/sent`
  Lets the texting worker acknowledge delivery without coupling Afterglow to one SMS vendor.
- `submit_debrief(...)`
  Handles debrief intake idempotently.
- `finalize_match(...)`
  Finalizes automatically when both participants submit, or conservatively on timeout.
- operator endpoints
  Let humans inspect outcomes, memory deltas, and trace steps.

This keeps the visible product simple:

- existing Ditto flow
- tiny debrief
- matching system update
- internal trace

## Quickstart

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow"
python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m afterglow.cli
PYTHONPATH=src python3 -c "from afterglow.api import app; print(app.title)"
```

## Internship submission companion

This repo now includes a small set of assets to help the project read like a product decision, not just a backend harness:

- `docs/customer_research.md`
  Short note on the user problem, assumptions, and why this is the right first feature.
- `docs/secondary_research.md`
  Market context from public research, used honestly as supporting evidence rather than fake interview claims.
- `docs/interview_guide.md`
  Primary-research guide for real user validation.
- `docs/usability_test_plan.md`
  Near-term plan for testing the end-user flow.
- `docs/iteration_log.md`
  Tight v0 to v1 story for the feature.
- `docs/build_journal.md`
  Timestamped build log for this submission pass.
- `docs/video_outline.md`
  A concrete 5-minute walkthrough plan with commands.
- `GET /demo/founder-surface`
  Lightweight product-facing surface for the video and reviewer walkthrough.
- `GET /demo/check-in`
  Interactive end-user check-in experience backed by the live API.

To show the founder-facing product surface locally:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow"
PYTHONPATH=src uvicorn afterglow.api:app --reload --port 8017
```

Then open:

```text
http://127.0.0.1:8017/demo/founder-surface
http://127.0.0.1:8017/demo/check-in
```

## One-command terminal showcase

For the 5-minute video, run:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow" && ./scripts/showcase.sh
```

That prints the full harness story in order:

- Ditto registers a completed date.
- Afterglow queues real provider-ready SMS work.
- One reply arrives and the system waits.
- Both replies arrive and the matcher updates memory.
- Operator trace explains the decision.

## Professional packaging surface

Afterglow now exposes the same integration contract in two transports:

- CLI for deterministic automation and cron-style orchestration
- MCP for agent/tool-based invocation inside a broader Ditto AI system

One wrapper script handles both:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow" && ./scripts/afterglow.sh --help
```

CLI examples:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow" && ./scripts/afterglow.sh register-match --match-id match-001 --user-a-id avery --user-b-id lena --venue-name "Campanile sunset loop" --completed-at now
```

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow" && ./scripts/afterglow.sh open-check-in --match-id match-001
```

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow" && ./scripts/afterglow.sh submit-debrief --match-id match-001 --user-id avery --date-rating 5 --energy charged --curiosity interested --comfort open --follow-up-intent yes
```

MCP server:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow" && ./scripts/afterglow.sh mcp
```

That starts a stdio MCP server exposing tools like:

- `register_match`
- `open_check_in`
- `submit_debrief`
- `receive_sms`
- `finalize_match`
- `get_match`
- `get_trace`
- `list_outbox`
- `mark_sent`
- `get_global_memory`
- `demo`

A ready-to-drop MCP registration example lives at:

- [afterglow.mcp.json](</Users/ahabscheid/dev/AI PROJECTS/Afterglow/integration/afterglow.mcp.json>)

## Live Twilio path

The Twilio path uses the real Programmable Messaging API. It does not simulate delivery.

Set environment variables:

```bash
export TWILIO_ACCOUNT_SID="AC..."
export TWILIO_AUTH_TOKEN="..."
export TWILIO_FROM_NUMBER="+15551234567"
export AFTERGLOW_PHONE_AVERY="+15550001001"
export AFTERGLOW_PHONE_LENA="+15550001002"
export AFTERGLOW_ACTIVE_MATCH_ID="match-terminal-demo"
```

Send the queued check-ins through Twilio:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow" && ./scripts/showcase.sh --send-twilio --keep-db
```

If you want to demo a direct Twilio CLI send instead of the Python Twilio client:

```bash
export TWILIO_PROFILE="norma"
export TWILIO_FROM_NUMBER="+1YOUR_TWILIO_NUMBER"
export AFTERGLOW_DEMO_PHONE="+19894934411"
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow" && ./scripts/send_twilio_cli_demo.sh
```

To receive real replies, run the API in another terminal:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow" && PYTHONPATH=src uvicorn afterglow.api:app --reload --port 8017
```

Expose that local server with a tunnel and configure the Twilio inbound webhook to:

```text
https://YOUR-TUNNEL-DOMAIN/integrations/twilio/inbound
```

Reply format:

```text
5 charged interested open yes
```

Or explicit format:

```text
match=match-terminal-demo user=avery rating=5 energy=charged curiosity=interested comfort=open follow=yes
```
