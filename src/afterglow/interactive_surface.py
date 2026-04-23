from __future__ import annotations


def build_check_in_demo_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Afterglow Check-In Demo</title>
  <style>
    :root {
      --ink: #18243f;
      --paper: rgba(255, 252, 247, 0.9);
      --line: rgba(24, 36, 63, 0.12);
      --accent: #ef6c3d;
      --teal: #0e7c7b;
      --blue: #2f5d9f;
      --shadow: 0 24px 54px rgba(24, 36, 63, 0.14);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 10% 10%, rgba(239, 108, 61, 0.18), transparent 26%),
        radial-gradient(circle at 90% 0%, rgba(14, 124, 123, 0.16), transparent 22%),
        linear-gradient(180deg, #fffaf3 0%, #f4ecdf 100%);
    }
    .shell { max-width: 1200px; margin: 0 auto; padding: 32px 18px 72px; }
    .hero, .card, .phone {
      background: var(--paper);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }
    .hero { border-radius: 28px; padding: 28px; }
    .grid {
      display: grid;
      grid-template-columns: 400px minmax(0, 1fr);
      gap: 20px;
      margin-top: 24px;
      align-items: start;
    }
    .phone { border-radius: 34px; padding: 18px; position: sticky; top: 20px; }
    .screen {
      background: linear-gradient(180deg, #fffdfa 0%, #fbf3e8 100%);
      border-radius: 24px;
      padding: 18px;
      border: 1px solid rgba(24, 36, 63, 0.08);
    }
    .eyebrow {
      display: inline-flex;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(14, 124, 123, 0.08);
      color: var(--teal);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    h1, h2 { margin: 0; font-family: Georgia, "Times New Roman", serif; line-height: 1.05; }
    h1 { margin-top: 14px; font-size: clamp(2.2rem, 6vw, 4.2rem); max-width: 12ch; }
    p { line-height: 1.6; }
    .lede { max-width: 68ch; margin-top: 16px; font-size: 1.05rem; }
    .stats, .choice-row, .actions, .link-row { display: flex; flex-wrap: wrap; gap: 10px; }
    .topline { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .bubble, .stat, .pill { background: white; border: 1px solid var(--line); }
    .bubble { padding: 14px; border-radius: 20px 20px 20px 8px; font-size: 0.98rem; }
    .stat { display: inline-flex; align-items: center; padding: 8px 10px; border-radius: 999px; font-size: 0.9rem; font-weight: 600; }
    .cards { display: grid; gap: 20px; }
    .card { border-radius: 26px; padding: 22px; }
    .card h2 { font-size: 1.8rem; margin-bottom: 10px; }
    .subtle { color: rgba(24, 36, 63, 0.72); margin-top: 8px; }
    .pill { padding: 10px 12px; border-radius: 16px; font-size: 0.92rem; font-weight: 600; cursor: pointer; }
    .pill.active { background: rgba(239, 108, 61, 0.12); border-color: rgba(239, 108, 61, 0.35); color: #8d3d19; }
    label { display: block; margin-top: 18px; margin-bottom: 8px; font-size: 0.95rem; font-weight: 700; }
    textarea {
      width: 100%;
      min-height: 88px;
      padding: 12px 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      resize: vertical;
      font: inherit;
      background: #fffdfa;
    }
    button { border: 0; border-radius: 16px; padding: 12px 16px; font: inherit; font-weight: 700; cursor: pointer; }
    .primary { background: var(--accent); color: white; }
    .secondary { background: rgba(24, 36, 63, 0.08); color: var(--ink); }
    pre {
      margin: 0;
      padding: 16px;
      overflow: auto;
      border-radius: 18px;
      background: #17243b;
      color: #edf4ff;
      font-size: 0.86rem;
      line-height: 1.5;
    }
    .result {
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(14, 124, 123, 0.08);
      border: 1px solid rgba(14, 124, 123, 0.16);
    }
    .result.pending { background: rgba(239, 108, 61, 0.08); border-color: rgba(239, 108, 61, 0.16); }
    .result strong { display: block; margin-bottom: 6px; }
    .tiny { font-size: 0.9rem; color: rgba(24, 36, 63, 0.74); }
    .link-row a { color: var(--blue); text-decoration: none; font-weight: 700; margin-right: 12px; }
    @media (max-width: 920px) {
      .grid { grid-template-columns: 1fr; }
      .phone { position: static; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <span class="eyebrow">End-User Product Demo</span>
      <h1>A tiny check-in the user can actually complete.</h1>
      <p class="lede">
        This demo creates a fresh match through the live API, lets you submit post-date feedback,
        and shows how the system moves from one user's response to a finalized second-date decision.
      </p>
      <div class="stats" style="margin-top:18px;">
        <div class="stat">Interactive mobile-first check-in</div>
        <div class="stat">Live API submissions</div>
        <div class="stat">Operator snapshot</div>
      </div>
    </section>
    <div class="grid">
      <aside class="phone">
        <div class="screen">
          <div class="topline">
            <strong>Afterglow</strong>
            <span id="sessionState" class="tiny">Creating demo session…</span>
          </div>
          <div class="bubble">Quick check-in. How did the date feel? This should take less than 20 seconds.</div>
          <label>Participant</label>
          <div id="userChoices" class="choice-row"></div>
          <label>Rate the date</label>
          <div id="ratingChoices" class="choice-row"></div>
          <label>Energy</label>
          <div id="energyChoices" class="choice-row"></div>
          <label>Curiosity</label>
          <div id="curiosityChoices" class="choice-row"></div>
          <label>Comfort</label>
          <div id="comfortChoices" class="choice-row"></div>
          <label>Would a date-two nudge feel welcome?</label>
          <div id="followChoices" class="choice-row"></div>
          <label for="note">Optional note</label>
          <textarea id="note" placeholder="Anything the system should remember about the vibe?"></textarea>
          <div class="actions" style="margin-top:18px;">
            <button id="submitButton" class="primary" type="button">Submit Check-In</button>
            <button id="resetButton" class="secondary" type="button">Start Fresh Demo</button>
          </div>
          <div class="actions" style="margin-top:12px;">
            <button id="presetGood" class="secondary" type="button">Load Strong-Date Preset</button>
            <button id="presetMixed" class="secondary" type="button">Load Mixed-Date Preset</button>
          </div>
        </div>
      </aside>
      <section class="cards">
        <article class="card">
          <h2>Live session</h2>
          <p class="subtle">
            The page seeds a new match through the API so the reviewer can see the user flow without
            leaving the browser or hand-editing payloads.
          </p>
          <div id="sessionChips" class="stats"></div>
          <div class="link-row" style="margin-top:16px;">
            <a href="/demo/founder-surface">Founder framing</a>
            <a href="/operator/outcomes" target="_blank" rel="noreferrer">Operator outcomes JSON</a>
          </div>
        </article>
        <article class="card">
          <h2>Submission result</h2>
          <div id="resultCard" class="result pending">
            <strong>Waiting for the first submission</strong>
            <div class="tiny">Submit one check-in to watch the system move into pending state.</div>
          </div>
        </article>
        <article class="card">
          <h2>API payload</h2>
          <pre id="payloadPreview">{}</pre>
        </article>
        <article class="card">
          <h2>Operator snapshot</h2>
          <pre id="operatorPreview">{}</pre>
        </article>
      </section>
    </div>
  </div>
  <script>
    const state = { matchId: "", selectedUser: "avery", rating: 5, energy: "charged", curiosity: "interested", comfort: "open", followUpIntent: "yes" };
    const options = {
      users: [{ label: "Avery", value: "avery" }, { label: "Lena", value: "lena" }],
      rating: ["1", "2", "3", "4", "5"],
      energy: ["drained", "steady", "charged"],
      curiosity: ["flat", "interested", "obsessed"],
      comfort: ["guarded", "open", "fully-safe"],
      followUpIntent: ["no", "maybe", "yes"],
    };
    function renderChoices(containerId, values, currentValue, onPick) {
      const container = document.getElementById(containerId);
      container.innerHTML = "";
      values.forEach((item) => {
        const value = typeof item === "string" ? item : item.value;
        const label = typeof item === "string" ? item : item.label;
        const button = document.createElement("button");
        button.type = "button";
        button.className = "pill" + (value === currentValue ? " active" : "");
        button.textContent = label;
        button.addEventListener("click", () => onPick(value));
        container.appendChild(button);
      });
    }
    function buildPayload() {
      return {
        match_id: state.matchId,
        user_id: state.selectedUser,
        date_rating: Number(state.rating),
        energy: state.energy,
        curiosity: state.curiosity,
        comfort: state.comfort,
        follow_up_intent: state.followUpIntent,
        note: document.getElementById("note").value.trim(),
      };
    }
    function refreshUI() {
      renderChoices("userChoices", options.users, state.selectedUser, (value) => { state.selectedUser = value; refreshUI(); });
      renderChoices("ratingChoices", options.rating, String(state.rating), (value) => { state.rating = Number(value); refreshUI(); });
      renderChoices("energyChoices", options.energy, state.energy, (value) => { state.energy = value; refreshUI(); });
      renderChoices("curiosityChoices", options.curiosity, state.curiosity, (value) => { state.curiosity = value; refreshUI(); });
      renderChoices("comfortChoices", options.comfort, state.comfort, (value) => { state.comfort = value; refreshUI(); });
      renderChoices("followChoices", options.followUpIntent, state.followUpIntent, (value) => { state.followUpIntent = value; refreshUI(); });
      document.getElementById("payloadPreview").textContent = JSON.stringify(buildPayload(), null, 2);
      document.getElementById("sessionChips").innerHTML =
        '<div class="stat">match_id: ' + state.matchId + '</div>' +
        '<div class="stat">participants: avery + lena</div>' +
        '<div class="stat">API route: POST /debriefs</div>';
    }
    function setResult(title, detail, pending) {
      const card = document.getElementById("resultCard");
      card.className = "result" + (pending ? " pending" : "");
      card.innerHTML = "<strong>" + title + "</strong><div class='tiny'>" + detail + "</div>";
    }
    async function fetchOperatorSnapshot() {
      if (!state.matchId) return;
      const summary = await fetch("/operator/matches/" + state.matchId).then((response) => response.json());
      const trace = await fetch("/operator/matches/" + state.matchId + "/trace").then((response) => response.json());
      document.getElementById("operatorPreview").textContent = JSON.stringify({ summary, trace }, null, 2);
    }
    async function createDemoSession() {
      document.getElementById("sessionState").textContent = "Creating demo session…";
      const session = await fetch("/demo/check-in/session", { method: "POST" }).then((response) => response.json());
      state.matchId = session.match_id;
      state.selectedUser = session.user_ids[0];
      document.getElementById("note").value = "";
      document.getElementById("sessionState").textContent = "Ready";
      refreshUI();
      await fetchOperatorSnapshot();
      setResult("Fresh demo session ready", "Submit one check-in to move the match into pending, then submit the second user to finalize it.", true);
    }
    async function submitCheckIn() {
      document.getElementById("sessionState").textContent = "Submitting…";
      const response = await fetch("/debriefs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildPayload()),
      });
      const result = await response.json();
      document.getElementById("sessionState").textContent = "Ready";
      document.getElementById("payloadPreview").textContent =
        JSON.stringify(buildPayload(), null, 2) + "\\n\\n// response\\n" + JSON.stringify(result, null, 2);
      if (result.status === "pending" || result.status === "duplicate-ignored") {
        setResult("One side has checked in", result.message || "The system is waiting for the second participant.", true);
      } else {
        setResult("Outcome finalized", "Follow-up action: " + (result.follow_up_action || "quiet-learn") + ". Match score: " + result.match_update_score, false);
      }
      await fetchOperatorSnapshot();
    }
    function presetGood() {
      state.rating = 5;
      state.energy = "charged";
      state.curiosity = "obsessed";
      state.comfort = "open";
      state.followUpIntent = "yes";
      document.getElementById("note").value = "Strong momentum. Easy conversation and felt natural.";
      refreshUI();
    }
    function presetMixed() {
      state.rating = 3;
      state.energy = "steady";
      state.curiosity = "interested";
      state.comfort = "guarded";
      state.followUpIntent = "maybe";
      document.getElementById("note").value = "Pleasant enough, but the chemistry felt uncertain.";
      refreshUI();
    }
    document.getElementById("submitButton").addEventListener("click", submitCheckIn);
    document.getElementById("resetButton").addEventListener("click", createDemoSession);
    document.getElementById("presetGood").addEventListener("click", presetGood);
    document.getElementById("presetMixed").addEventListener("click", presetMixed);
    refreshUI();
    createDemoSession();
  </script>
</body>
</html>
"""
