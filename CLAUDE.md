# Afterglow

## What this project is

Afterglow is a backend-first prototype for a dating-platform feature that learns from real post-date feedback.

The core feature is:

- register a completed date
- send a tiny post-date check-in
- collect structured debrief signals
- score the outcome
- decide whether a second-date nudge is appropriate
- update user, pair, and global matching memory

## Main entry points

- API: `PYTHONPATH=src uvicorn afterglow.api:app --reload --port 8017`
- CLI: `PYTHONPATH=src python3 -m afterglow.cli --help`
- Showcase: `./scripts/showcase.sh`
- Tests: `PYTHONPATH=src python3 -m unittest discover -s tests`

## Important files

- `src/afterglow/service.py`
  Main orchestration layer.
- `src/afterglow/engine.py`
  Match scoring and follow-up decision logic.
- `src/afterglow/repository.py`
  SQLite persistence and durable state.
- `src/afterglow/api.py`
  FastAPI integration surface and demo routes.
- `src/afterglow/product_surface.py`
  Lightweight product-facing demo page for the internship walkthrough.
- `src/afterglow/interactive_surface.py`
  Interactive end-user check-in demo backed by the live API.
- `docs/customer_research.md`
  Product framing and assumptions.
- `docs/secondary_research.md`
  Public-source market context.
- `docs/interview_guide.md`
  Primary research guide.
- `docs/usability_test_plan.md`
  Usability validation plan.
- `docs/iteration_log.md`
  Concise v0 to v1 story.
- `docs/build_journal.md`
  Timestamped build notes for this submission pass.
- `docs/video_outline.md`
  Suggested 5-minute walkthrough.

## Notes

- This project directory is currently not its own Git repository.
- Keep files modular and avoid oversized modules.
- If you change behavior, rerun tests and a quick import/compile check.
