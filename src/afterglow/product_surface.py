from __future__ import annotations


def build_founder_demo_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Afterglow Founder Surface</title>
  <style>
    :root {
      --ink: #14213d;
      --warm: #f4efe6;
      --sand: #e8dcc8;
      --accent: #ef6c3d;
      --accent-soft: #ffd8bf;
      --teal: #127475;
      --card: rgba(255, 252, 247, 0.9);
      --line: rgba(20, 33, 61, 0.12);
      --shadow: 0 28px 60px rgba(20, 33, 61, 0.12);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      color: var(--ink);
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(239, 108, 61, 0.18), transparent 28%),
        radial-gradient(circle at top right, rgba(18, 116, 117, 0.14), transparent 24%),
        linear-gradient(180deg, #fffaf3 0%, #f5eee2 100%);
    }

    main {
      max-width: 1120px;
      margin: 0 auto;
      padding: 48px 20px 80px;
    }

    .hero,
    .panel {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }

    .hero {
      padding: 36px;
      overflow: hidden;
      position: relative;
    }

    .hero::after {
      content: "";
      position: absolute;
      inset: auto -40px -50px auto;
      width: 240px;
      height: 240px;
      background: radial-gradient(circle, rgba(239, 108, 61, 0.24), transparent 68%);
      pointer-events: none;
    }

    .eyebrow {
      display: inline-flex;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(18, 116, 117, 0.1);
      color: var(--teal);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    h1, h2, h3 {
      font-family: Georgia, "Times New Roman", serif;
      line-height: 1.05;
      margin: 0;
    }

    h1 {
      margin-top: 18px;
      font-size: clamp(2.6rem, 7vw, 4.8rem);
      max-width: 12ch;
    }

    p {
      line-height: 1.6;
      font-size: 1rem;
    }

    .lede {
      max-width: 62ch;
      margin: 18px 0 0;
      font-size: 1.1rem;
    }

    .hero-grid,
    .two-up,
    .signals {
      display: grid;
      gap: 20px;
    }

    .hero-grid {
      grid-template-columns: 1.3fr 0.9fr;
      margin-top: 28px;
    }

    .two-up,
    .signals {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .stack {
      display: grid;
      gap: 20px;
      margin-top: 24px;
    }

    .panel {
      padding: 24px;
      animation: rise 420ms ease both;
    }

    .metric {
      display: inline-block;
      margin: 0 10px 10px 0;
      padding: 10px 12px;
      border-radius: 16px;
      background: white;
      border: 1px solid var(--line);
      font-size: 0.95rem;
      font-weight: 600;
    }

    .message {
      background: white;
      border: 1px solid rgba(239, 108, 61, 0.25);
      border-radius: 22px;
      padding: 18px;
    }

    .message strong {
      display: block;
      margin-bottom: 10px;
      color: var(--accent);
    }

    .signal {
      padding: 18px;
      background: white;
      border: 1px solid var(--line);
      border-radius: 22px;
    }

    .signal code {
      display: inline-block;
      margin-top: 10px;
      padding: 8px 10px;
      border-radius: 12px;
      background: #f9f1e7;
      font-size: 0.95rem;
    }

    ol {
      margin: 18px 0 0;
      padding-left: 20px;
      line-height: 1.7;
    }

    .api-list {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }

    .api-list span {
      padding: 9px 12px;
      border-radius: 999px;
      background: rgba(20, 33, 61, 0.06);
      border: 1px solid var(--line);
      font-family: "SFMono-Regular", "Menlo", monospace;
      font-size: 0.88rem;
    }

    .note {
      margin-top: 16px;
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(18, 116, 117, 0.08);
      border: 1px solid rgba(18, 116, 117, 0.12);
    }

    @keyframes rise {
      from {
        opacity: 0;
        transform: translateY(10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @media (max-width: 860px) {
      .hero-grid,
      .two-up,
      .signals {
        grid-template-columns: 1fr;
      }

      .hero,
      .panel {
        border-radius: 24px;
      }
    }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <span class="eyebrow">Founder Demo Surface</span>
      <h1>Start with the moment a real date turns into product truth.</h1>
      <p class="lede">
        Most dating products overfit on swipes, prompts, and chat volume. Afterglow starts where
        the best signal actually appears: the five minutes after a real date, when two people can
        tell you whether there was energy, curiosity, comfort, and consent for a second plan.
      </p>
      <div class="hero-grid">
        <div class="panel">
          <h2>What the user sees</h2>
          <div class="message">
            <strong>Quick Afterglow check-in</strong>
            <p>Rate the date 1-5, then share energy, curiosity, comfort, and whether Ditto should nudge date two.</p>
          </div>
          <div class="signals">
            <div class="signal">
              <h3>Fast reply path</h3>
              <p>The lightweight SMS path lowers friction enough that people will actually answer.</p>
              <code>5 charged interested open yes</code>
            </div>
            <div class="signal">
              <h3>User value</h3>
              <p>No long survey, no awkward essay. One tiny action helps future matches get better.</p>
            </div>
          </div>
        </div>
        <div class="panel">
          <h2>Why this is the first feature</h2>
          <div class="metric">Learning loop before growth loop</div>
          <div class="metric">Consent-aware second-date nudge</div>
          <div class="metric">Higher signal than profile edits</div>
          <div class="metric">Small enough for a 90 minute build</div>
          <div class="note">
            The first version should prove one thing: the platform can learn from actual chemistry,
            not just from who looked good on paper.
          </div>
        </div>
      </div>
    </section>

    <section class="stack">
      <div class="two-up">
        <article class="panel">
          <h2>What the platform learns</h2>
          <ol>
            <li>The date happened and both people were eligible for a check-in.</li>
            <li>The system captured structured signals, not just a star rating.</li>
            <li>Afterglow scored the match and decided whether to offer a second date or quietly learn.</li>
            <li>User memory, pair memory, and global ranking features updated immediately.</li>
          </ol>
        </article>
        <article class="panel">
          <h2>Customer research framing</h2>
          <ol>
            <li>Singles want better matches without more work.</li>
            <li>They will not fill out a long post-date form.</li>
            <li>A platform should only push date two when both sides signal comfort and interest.</li>
            <li>Operators need an explainable trace when a system changes ranking behavior.</li>
          </ol>
        </article>
      </div>

        <article class="panel">
          <h2>Video walkthrough spine</h2>
          <ol>
            <li>Frame the product thesis: real dates create the strongest matching signal.</li>
            <li>Show the lightweight user experience on this page, then open the interactive check-in demo.</li>
            <li>Run the terminal showcase to prove the full flow works end to end.</li>
            <li>Point to the API and infrastructure that make the feature production-shaped.</li>
            <li>Close on what you would test next with real users.</li>
          </ol>
          <div class="note">
            Next demo surface:
            <a href="/demo/check-in" style="color:#2f5d9f;font-weight:700;text-decoration:none;">/demo/check-in</a>
          </div>
          <div class="api-list">
            <span>POST /matches/register</span>
            <span>POST /matches/{match_id}/check-in</span>
            <span>POST /debriefs</span>
          <span>POST /debriefs/sms-reply</span>
          <span>GET /operator/matches/{match_id}/trace</span>
          <span>GET /operator/memory/global</span>
        </div>
      </article>
    </section>
  </main>
</body>
</html>
"""
