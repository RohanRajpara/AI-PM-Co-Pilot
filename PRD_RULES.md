# PRD Generation Rules

Use these rules whenever generating a Product Requirement Document (PRD) from user feedback,
a feature idea, or a research insight. These rules exist to fix three recurring failure modes:
**vague/generic content, padded sections, and inconsistent tables.** Follow them strictly.

---

## 0. Non-negotiable grounding rule

Before writing anything, extract 3-5 concrete "anchors" from the input: exact phrases, numbers,
behaviors, or complaints the user/feedback actually mentioned. Every section of the PRD must
reference at least one of these anchors explicitly (by paraphrase, not necessarily verbatim).

**If a sentence could be copy-pasted into a PRD for a completely different feature and still make
sense, delete it and rewrite it using an anchor.** This is the single biggest quality filter.

Bad (generic, no anchor):
> "Users want a better experience when navigating the app."

Good (grounded in an anchor):
> "Users report the app gives wrong routes and inaccurate traffic predictions, undermining trust
> in real-time navigation during active trips."

---

## 1. Section structure — must-haves vs optional

Always use this exact set of section titles, in this order. Sections marked **REQUIRED** in this
rules doc appear every time. Sections marked **CONDITIONAL** appear only if they add
feedback-specific value — never as filler to look thorough.

**Important: "REQUIRED" / "CONDITIONAL" are internal planning labels for whoever is writing the
PRD. They must NEVER appear in the actual output document — no status tags, no brackets, no
"(must-have)" next to a heading. The final PRD should read exactly like the reference template
in Section 1a below, with nothing but the section title itself.**

| Section title | Status |
|---|---|
| Objective & Goal | REQUIRED |
| Problem Statement | REQUIRED |
| Team Goals & Business Objectives (with Primary Goals / Business Objectives subsections) | REQUIRED |
| Background & Strategic Fit | CONDITIONAL |
| Assumptions, Constraints & Dependencies | REQUIRED |
| User Stories | REQUIRED |
| Features & Product Scope (Description / Goal / Use Case per feature) | REQUIRED |
| UX Flow & Design Notes | REQUIRED |
| System & Environment Requirements | REQUIRED |
| Design & User Experience Principles | REQUIRED |
| Success Metrics | REQUIRED |
| Open Questions | REQUIRED |
| What We Are Not Doing | CONDITIONAL |
| Risks & Mitigations | REQUIRED |

**Rule for conditional sections**: before including one, ask "does this section say something that
is only true because of THIS specific feedback?" If the answer is no, cut the section entirely.
A PRD with 10 sharp sections beats one with 14 where 4 are filler.

**Section-specific content rules for the new additions:**

- **Objective & Goal**: 1-2 sentences, high-level "why build this." Must NOT just restate the
  Problem Statement in different words — this is the plain-terms motivation, Problem Statement is
  the detailed framing.
- **Assumptions, Constraints & Dependencies**: three distinct categories in one section — what's
  expected of users, hard limits the implementation must respect, and outside dependencies
  (APIs, partner teams, vendors) required for the solution to function. Cover all three whenever
  relevant, don't just default to one.
- **Features & Product Scope**: for each feature (1-4 depending on complexity), give Description,
  Goal, and Use Case at minimum, as `#### **N.N  Feature Name**` subsections. Add out-of-scope
  notes only where a feature has a genuine edge worth flagging.
- **UX Flow & Design Notes**: describes the overall user workflow/sequence at a high level — NOT
  pixel-perfect wireframes or a screen-by-screen spec. 3-5 sentences or a short numbered sequence
  is enough. Must not duplicate the Design & UX Principles section (that section covers rules/
  constraints; this one covers the flow itself).
- **System & Environment Requirements**: browsers, operating systems, device types, memory/
  processing needs, offline behavior, etc. If genuinely not applicable (e.g. a backend-only
  change), write "Not applicable — [one-sentence reason]" rather than omitting the section
  entirely — never leave a required section blank.

### 1a. Heading format and numbering — matches the reference template exactly

- Use ONE consistent heading style for every top-level section: `### **N. Section Title**`
  (heading level 3, bold text, number + period before the title). Do not mix heading levels —
  never use `##` for one section and `###` for another.
- Subsections (like Primary Goals / Business Objectives under Team Goals, or feature groupings
  under Features & Product Scope) use `#### **N.N  Subsection Title**` — one level deeper, same
  bold style, decimal numbering tied to their parent section.
- **Numbers must always run sequentially starting at 1, with no gaps and no skipped numbers** —
  even though some sections are conditional and get skipped depending on the feedback. If
  Background & Strategic Fit (a conditional section) is omitted, the section after it is
  renumbered to fill the gap. Never output "2, 3, 5, 6" because section 4 was cut — renumber to
  "2, 3, 4, 5".
- Do not add a numbered "0" section or start numbering at anything other than 1.
- The document title itself (e.g. "Product Requirement Document" + feature name) is NOT numbered
  and uses a single top-level heading (`# <u>Product Requirement Document</u>` followed by
  `## **Feature Name**` as a subtitle) — numbering starts only at the first real section
  (Problem Statement = section 1... note the reference template starts Problem Statement at
  section 2 because it has a "Project Specifics" table first; if you include a Project Specifics
  table, it is unnumbered section 1 and Problem Statement becomes section 2 — otherwise Problem
  Statement is section 1).

---

## 2. Anti-padding rules (fixes repetitive/padded sections)

- **No section may restate a point already made in an earlier section.** If the Problem Statement
  already said the app crashes on save, the Assumptions section may not re-explain that the app
  crashes on save — it can only add a *new* assumption building on that fact.
- **Every bullet must contain at least one specific noun, number, or named entity.** Reject bullets
  like "Improve reliability" — rewrite as "Reduce offline-map save failures below 1% of attempts."
- **Cap bullet count per section at 5.** If you have more than 5 genuinely distinct points, the
  section is trying to do too much — split it or cut the weakest points.
- **One idea per sentence.** Long compound sentences stacking three vague claims together are a
  padding signal — break them apart or cut two of the three claims.
- **Never write a sentence whose only job is to introduce the next sentence** (e.g. "There are
  several important considerations here." — delete, go straight to the considerations).

---

## 3. Table formatting rules (fixes inconsistent tables)

All required tables (User Stories, Success Metrics, Risks & Mitigations) must follow these exact
specs — no deviation in column names, order, or row count ranges. Use standard markdown pipe
tables with a bold header row, matching the reference template style.

### User Stories table
```
| **ID** | **Role** | **Action** | **Benefit** |
|---|---|---|---|
| US-01 | [specific persona, not "user"] | [single concrete action] | [outcome tied to an anchor] |
```
- 3-5 rows, IDs sequential starting at US-01.
- **Role must be a specific persona** derived from the feedback context (e.g. "frequent traveler
  who saves offline maps", not "user" or "customer").
- No two rows may have near-duplicate Actions — each row must cover a genuinely different
  behavior.

### Success Metrics table
```
| **Metric** | **Baseline** | **Target (timeframe)** |
|---|---|---|
| [name] | [current value or "N/A (new feature)"] | [number + timeframe, e.g. "+15% in 6 months"] |
```
- 3-5 rows.
- Baseline must never be left blank — use "N/A (new feature)" explicitly if there's no existing
  baseline, never omit the cell.
- Target must always include both a number/percentage AND a timeframe. "Improve retention" is not
  a valid target; "Increase 30-day retention by 10% within 2 quarters" is.

### Risks & Mitigations table
```
| **Risk** | **Impact** | **Mitigation** |
|---|---|---|
| [specific risk tied to this feature] | High / Medium / Low | [concrete action, owner if relevant] |
```
- 3-4 rows.
- Impact column values must be exactly "High", "Medium", or "Low" — no other wording.
- Mitigation must be an action ("Cap storage at 128GB to protect margin"), never a vague hope
  ("Monitor the situation closely").

### General table rules
- Never use merged cells, nested tables, or multi-line cell content beyond a single `<br>`-style
  line break where the reference template uses one — keep cells short and scannable.
- Column headers must be bold (`**Header**`) and match exactly what's specified above — do not
  rename, reorder, or add extra columns.
- Do not add a table where a bulleted list was specified (Open Questions may use either a table
  or a numbered list — pick one and be consistent within the document), or vice versa for the
  three required tables above.

---

## 4. Tone and specificity checklist (run before finalizing)

Before outputting the PRD, verify:

- [ ] Every section references at least one concrete anchor from the input (Rule 0)
- [ ] No sentence is generic enough to apply to an unrelated feature (Rule 0)
- [ ] No conditional section was included without a feedback-specific reason (Rule 1)
- [ ] Section numbers run sequentially with no gaps, regardless of which conditional sections were skipped (Rule 1a)
- [ ] Every heading uses the same `### **N. Title**` style — no mixed heading levels (Rule 1a)
- [ ] No point is repeated across two sections (Rule 2)
- [ ] Every bullet has a specific noun/number/entity (Rule 2)
- [ ] All required tables match the exact column specs and bold header style (Rule 3)
- [ ] Success Metrics targets all include a number and a timeframe (Rule 3)
- [ ] Risk Impact values are only High/Medium/Low (Rule 3)
- [ ] No internal status labels ("REQUIRED", "CONDITIONAL", "MUST-HAVE", etc.) appear anywhere in the output (Rule 1)

If any box fails, revise before returning the PRD — do not return a draft that fails this checklist.

---

## 5. Output format

Return only the PRD content itself, starting at the document title. No preamble, no meta-
commentary about which conditional sections were skipped, no summary after the PRD, and no status
labels of any kind next to headings. The document should read exactly like the reference Apple
PRD template in tone and formatting — a real internal PM document, not an AI-generated explanation
of one.