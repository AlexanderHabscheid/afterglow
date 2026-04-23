# 5 Minute Video Outline

## Goal

Show that the first feature is not random. It is a deliberate wedge that improves the whole dating product.

## Structure

### 0:00-0:40 - Frame the product decision

Say:

"If I were founding a modern dating platform, I would not start by adding more profile fields. I would start by capturing the strongest signal in the system: what happened after a real date. So the first feature I built is a tiny post-date check-in that updates matching memory and decides whether a second-date nudge is welcome."

### 0:40-1:20 - Show the lightweight product surface

Run the API and open the founder surface:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow"
PYTHONPATH=src uvicorn afterglow.api:app --reload --port 8017
```

Open:

- `http://127.0.0.1:8017/demo/founder-surface`
- `http://127.0.0.1:8017/demo/check-in`

Call out:

- the user experience is intentionally tiny
- the interactive demo uses the live API, not mocked screenshots
- the signal set is richer than a star rating
- consent gates the second-date flow

### 1:20-3:20 - Prove the feature works end to end

Run:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow"
./scripts/showcase.sh
```

Walk through:

- match registration
- SMS check-in queueing
- pending state after one reply
- finalization after both replies
- global memory and operator trace

### 3:20-4:20 - Show implementation choices

Point to:

- [service.py](../src/afterglow/service.py) for orchestration
- [engine.py](../src/afterglow/engine.py) for scoring and follow-up logic
- [repository.py](../src/afterglow/repository.py) for durable state
- [api.py](../src/afterglow/api.py) for integration endpoints

Briefly explain:

- Python + FastAPI for speed
- SQLite because this is a tight prototype with durable state
- CLI and MCP because the feature should be easy to automate and integrate

### 4:20-5:00 - Show product thinking

End with:

- why this feature is a better first wedge than profiles or chat
- what assumption you would test next
- how you would iterate toward a user-facing second-date flow

## Backup commands

Run tests:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow"
PYTHONPATH=src python3 -m unittest discover -s tests
```

Print CLI help:

```bash
cd "/Users/ahabscheid/dev/AI PROJECTS/Afterglow"
PYTHONPATH=src python3 -m afterglow.cli --help
```
