# Customer Research Framing

This note is intentionally short. The internship prompt is looking for product judgment, not a giant research deck.

For stronger evidence and next-step validation assets, also see:

- `docs/secondary_research.md`
- `docs/interview_guide.md`
- `docs/usability_test_plan.md`

## Product thesis

The first feature should create a learning loop after a real date.

Reasoning:

- Swipes and profile edits are weak signals.
- Chat volume is noisy.
- Real-world chemistry is the best signal a dating platform can capture.
- The platform should only become more active after it earns the right to do so with better outcomes.

## Primary users

- Singles who want better matches without doing more work.
- Operators or internal teams who need to understand why the system changed a recommendation.

## Jobs to be done

- "Help me get better matches without making me fill out another questionnaire."
- "If a date went well, make the next step feel natural."
- "If a date did not go well, learn quietly and do not create an awkward follow-up."

## Core assumptions

- A tiny post-date check-in is realistic to complete.
- SMS is a low-friction channel for early versions.
- A structured signal set is more useful than a single satisfaction rating.
- Consent and comfort have to gate any second-date nudge.

## Why this feature first

- It improves the matching system itself.
- It is small enough to build quickly.
- It creates durable product leverage because each completed date improves future recommendations.
- It connects product design, infrastructure, and ranking logic in one slice.

## What to learn next

- What reply rate do we get from a one-line SMS check-in versus a web form?
- Which signal is most predictive of a successful second date: rating, comfort, curiosity, or follow-up intent?
- Does suggesting a second date increase user satisfaction or create pressure?
