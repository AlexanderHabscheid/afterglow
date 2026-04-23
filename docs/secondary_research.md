# Secondary Research Notes

This file exists to strengthen the internship submission with real external context, without pretending the project already has live interview data.

## What the public research suggests

### 1. Online daters report mixed experiences, including safety concerns and harassment

Pew Research's 2023 findings on online dating in the U.S. show that online dating is mainstream, but the experience is uneven and often stressful for users.

Product implication:

- A dating product should not optimize only for more matches.
- It should make downstream interactions feel safer and more intentional.
- Comfort and consent should affect follow-up flows, not just match probability.

Sources:

- https://www.pewresearch.org/internet/2023/02/02/the-experiences-of-u-s-online-daters/
- https://www.pewresearch.org/short-reads/2023/02/02/key-findings-about-online-dating-in-the-u-s/

### 2. A better match is more valuable than more app time

Modern dating products compete in a market where users are fatigued by repetitive swiping and low-quality conversations.

Product implication:

- A strong first feature should improve match quality, not just acquisition loops.
- Post-date feedback is more strategically valuable than another profile field because it creates a real learning loop.

Source context:

- Pew's reporting above supports the gap between usage and satisfaction.

### 3. Any second-date nudge should be gated by comfort and mutual interest

If the platform becomes more active after the first date, the product has to be careful not to create pressure.

Product implication:

- The first automated follow-up should be consent-aware.
- A "quiet learn" path is product design, not just backend logic.

## How this affected Afterglow

The feature design in this repo intentionally reflects those market realities:

- tiny post-date check-in instead of a long survey
- structured comfort and follow-up intent signals instead of rating alone
- explicit suppression path when the system should learn quietly
- operator trace for explainability
