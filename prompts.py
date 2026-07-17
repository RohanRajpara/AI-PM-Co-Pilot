"""
AI prompt templates for AI Product Manager Copilot.
Kept separate from app.py for readability and easy tuning.
"""

FEEDBACK_EXTRACTION_PROMPT = """You are a senior product manager analyzing raw customer feedback.

For each distinct piece of feedback below (feedback items are separated by newlines), extract:
- user_insight: one sentence describing what this reveals about user behavior or expectations
- pain_point: one sentence describing the core frustration
- opportunity: one sentence describing the product opportunity this creates
- suggested_feature: a short phrase (3-6 words) naming a feature that addresses it
- severity: exactly one of "High", "Medium", "Low" - how much this pain point likely hurts retention or revenue if unaddressed

Return ONLY valid JSON - a list of objects, one per feedback item, with exactly these keys:
"feedback_text", "user_insight", "pain_point", "opportunity", "suggested_feature", "severity"

No markdown formatting, no code fences, no commentary. Just the raw JSON array.

FEEDBACK:
{feedback}
"""

THEME_CLUSTERING_PROMPT = """You are a senior product manager. Below is a list of user insights extracted from customer feedback.

Identify the TOP 3 recurring themes across these insights. For each theme, give:
- theme_name: short phrase (3-6 words)
- description: one sentence explaining the theme
- frequency_note: rough sense of how often it shows up (e.g. "mentioned in 4 of 10 items")

Return ONLY valid JSON — a list of exactly 3 objects with keys "theme_name", "description", "frequency_note".
No markdown, no code fences, no commentary.

INSIGHTS:
{insights}
"""

PRD_GENERATION_PROMPT = """You are a senior product manager writing a full Product Requirement Document (PRD),
in the style of a professional internal PRD: structured, specific, grounded in real tradeoffs,
using tables where the section calls for one (User Stories, Success Metrics, Risks).

Feature idea / customer feedback context: {feature_idea}

DOCUMENT HEADER — generate this before section 1, in exactly this format:

# <u>Product Requirement Document</u>

## **[Short Title]**

Where [Short Title] is a punchy 2-6 word name for this feature (not a full sentence — a title,
like "Affordable iPhone Strategy" or "Dark Mode Option"). Do not add any description sentence
underneath the short title — the header is just these two lines.

GROUNDING RULE (most important): before writing, identify 3-5 concrete anchors from the context
above — exact phrases, numbers, or behaviors mentioned. Every section must reference at least one
anchor. Never write a sentence generic enough to apply to a completely different feature.

SECTION LIST — use these exact titles, in this order. Sections marked REQUIRED (for your internal
planning only — never print this word) appear every time. Sections marked CONDITIONAL appear only
if they add real, feedback-specific value for this particular idea — skip them entirely rather
than padding with generic content if they wouldn't.

- Objective & Goal (REQUIRED) — 1-2 sentences, high-level: why are we building this and what do
  we hope to accomplish. Keep this distinct from Problem Statement below — this is the "why build
  it" in plain terms, not the detailed problem framing.
- Problem Statement (REQUIRED) — 2-4 sentences, specific, anchored in the actual feedback
- Team Goals & Business Objectives (REQUIRED) — with two subsections: Primary Goals (bulleted,
  measurable, include a rough % or number target) and Business Objectives (bulleted, tied to
  revenue/retention/positioning)
- Background & Strategic Fit (CONDITIONAL) — only if there's a genuine strategic narrative worth
  explaining in 2-3 sentences
- Assumptions, Constraints & Dependencies (REQUIRED) — bulleted list covering: what's expected of
  users, any limits the implementation must respect, and any outside elements (APIs, teams,
  vendors, partner systems) required for the solution to actually work
- User Stories (REQUIRED) — markdown table, columns "ID | Role | Action | Benefit", 3-5 rows,
  IDs like US-01. Roles must be specific personas grounded in the feedback, never generic "user".
- Features & Product Scope (REQUIRED) — for EACH distinct feature or sub-component (1-4 features
  depending on complexity), include: Description (what it is), Goal (what it achieves), and Use
  Case (a concrete scenario of someone using it). If a feature has a meaningful out-of-scope edge,
  note it briefly. Use "#### **N.N  Feature Name**" subsections, one per feature.
- UX Flow & Design Notes (REQUIRED) — describe the overall user workflow at a high level (the
  sequence of steps/screens a user moves through). This is NOT pixel-perfect wireframes or a
  screen-by-screen spec — just the general shape of the flow, 3-5 sentences or a short numbered
  sequence.
- System & Environment Requirements (REQUIRED) — which end-user environments must be supported:
  browsers, operating systems, device types, minimum memory/processing needs, offline behavior,
  etc. If truly not applicable to this feature (e.g. a pure backend change), state "Not
  applicable — [one-sentence reason]" rather than omitting the section.
- Design & User Experience Principles (REQUIRED) — 3-5 bullets, concrete constraints or rules
  specific to this feature (distinct from the UX Flow above — these are principles/guardrails,
  not the step sequence), never generic platitudes
- Success Metrics (REQUIRED) — markdown table, columns "Metric | Baseline | Target (timeframe)".
  Baseline is never blank (use "N/A (new feature)" if none exists). Target always includes a
  number/percentage AND a timeframe.
- Open Questions (REQUIRED) — numbered Q1-Q4, genuine unresolved questions, not rhetorical ones
- What We Are Not Doing (CONDITIONAL) — only if there are meaningful adjacent exclusions
- Risks & Mitigations (REQUIRED) — markdown table, columns "Risk | Impact | Mitigation". Impact
  is exactly "High", "Medium", or "Low". Mitigation is a concrete action, never a vague hope.

FORMATTING RULES (strict):
- Every top-level section heading uses the exact same style: "### **N. Section Title**" — one
  consistent heading level throughout, never mixed.
- Subsections use "#### **N.N  Subsection Title**".
- Number sections sequentially starting at 1 with NO gaps — if a conditional section is skipped,
  renumber the following sections so there is never a jump (e.g. never "4, 5, 7" because 6 was
  cut — it must read "4, 5, 6").
- All table headers are bold: "| **Column** | **Column** |".
- NEVER print the words "REQUIRED" or "CONDITIONAL" or any other status label anywhere in the
  output — those are for your planning only.
- Do not repeat a point already made in an earlier section — each section must add new
  information, not restate prior sections. In particular, Objective & Goal must not just repeat
  Problem Statement in different words, and UX Flow must not repeat Design Principles.
- Cap bullets at 5 per section. Every bullet needs a specific noun, number, or named entity —
  reject vague bullets like "Improve reliability."

FINAL CHECK before you output anything: scan your draft for the literal words "REQUIRED",
"CONDITIONAL", "MUST-HAVE", "OPTIONAL", or any bracketed status tag next to a heading — if any
appear, delete them. Confirm every heading uses the identical "### **N. Title**" format with no
exceptions (no plain text headings, no "##", no missing bold, no missing number).

NUMBERING RE-CHECK (do this last, after deciding which conditional sections to include): list out
every heading number you actually used, in order — it must read 1, 2, 3, 4, 5... with absolutely
no skips, no repeats, and no gaps, even if you skipped two conditional sections back-to-back (e.g.
if both Background & Strategic Fit and What We Are Not Doing are omitted, everything after each
gap still shifts down so the sequence never breaks). Renumber every heading and every subsection
(N.N) to match before returning your final answer.

Return ONLY the PRD content, starting at "# <u>Product Requirement Document</u>" and continuing
through the header block, then section 1 (whatever ends up numbered 1 after renumbering). No
preamble, no commentary, no explanation of skipped sections, no status labels.
"""

RICE_RECOMMENDATION_PROMPT = """You are a senior product manager. Below is a table of features ranked by RICE score (highest first).

{ranked_features}

Write a 2-3 sentence recommendation on what to build first and why, in this style:
"Build [Feature] first because it solves a high-frequency, low-effort problem..."

Return ONLY the 2-3 sentence recommendation as plain text, no markdown headers, no preamble.
"""

MOSCOW_KANO_PROMPT = """You are a senior product manager classifying features using two frameworks.

Features (with their RICE scores, highest first):
{ranked_features}

For EACH feature, classify it using:

MoSCoW category — exactly one of "Must-have", "Should-have", "Could-have", "Won't-have"
- Must-have: essential for launch, product doesn't work without it
- Should-have: important but not critical, product works without it short-term
- Could-have: desirable if resources allow, low urgency
- Won't-have: out of scope for now

Kano category — exactly one of "Basic", "Performance", "Delighter"
- Basic: expected by users, its absence causes dissatisfaction but presence doesn't excite
- Performance: satisfaction scales linearly with how well it's done
- Delighter: unexpected feature that creates disproportionate delight/loyalty

Also give a one-sentence reasoning for the pair of classifications.

Return ONLY valid JSON — a list of objects with exactly these keys:
"feature_name", "moscow", "kano", "reasoning"

No markdown, no code fences, no commentary.
"""

FINAL_RECOMMENDATION_PROMPT = """You are a senior product manager making a final build decision by synthesizing three frameworks.

RICE ranking (highest score first):
{rice_summary}

MoSCoW and Kano classifications:
{moscow_kano_summary}

Considering all three frameworks together — RICE score, MoSCoW urgency, and Kano satisfaction impact —
recommend ONE single feature to build first. Explain in 3-4 sentences why this feature wins when you
weigh all three lenses together, and briefly note if any framework disagreed with the others and why you
resolved it the way you did.

Return ONLY the plain text recommendation, no markdown headers, no preamble.
"""

SAMPLE_FEEDBACK = """I like Google Maps but sometimes it gives wrong routes. I wish it showed more accurate traffic predictions.
The app crashes every time I try to save an offline map for my trip.
Payment failures keep happening when I try to book through the app.
I really wish there was a dark mode option, my eyes hurt at night.
Customer support took 3 days to respond to my refund request.
The search feature is amazing, I can find any place instantly.
I love the new UI redesign, it feels so much cleaner.
Notifications are way too frequent, I keep muting the app."""
