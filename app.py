"""
AI Product Manager Copilot
Modern SaaS dashboard MVP: Feedback Analyzer -> PRD Generator -> RICE Prioritization -> Insights Dashboard
"""

import os
import json
import time
from datetime import datetime
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import markdown as md_lib
from xhtml2pdf import pisa

load_dotenv()

from prompts import (
    FEEDBACK_EXTRACTION_PROMPT,
    THEME_CLUSTERING_PROMPT,
    PRD_GENERATION_PROMPT,
    RICE_RECOMMENDATION_PROMPT,
    MOSCOW_KANO_PROMPT,
    FINAL_RECOMMENDATION_PROMPT,
    SAMPLE_FEEDBACK,
)

MODEL = "openai/gpt-4o-mini"

st.set_page_config(page_title="AI Product Manager Copilot", page_icon="🧠", layout="wide")

SEVERITY_COLORS = {
    "High": {"bg": "#4A1B0C", "text": "#F0997B"},
    "Medium": {"bg": "#412402", "text": "#EF9F27"},
    "Low": {"bg": "#04342C", "text": "#5DCAA5"},
}

st.markdown(
    """
    <style>
    .stApp { background-color: #0d0d17; color: #ffffff; }
    section[data-testid="stSidebar"] { background-color: #0d0d17; }

    .metric-card {
        background: #171728;
        border: 1px solid #2a2a3d;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 8px;
    }
    .metric-label { font-size: 13px; color: #9d9db0; margin: 0 0 4px 0; }
    .metric-value { font-size: 26px; font-weight: 600; margin: 0; color: #ffffff; }

    .insight-card {
        background: #171728;
        border: 1px solid #2a2a3d;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .insight-feedback { font-size: 13px; color: #9d9db0; font-style: italic; margin-bottom: 8px; }
    .insight-row { font-size: 14px; margin: 4px 0; }
    .insight-label { color: #9d9db0; font-weight: 500; }

    .badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 8px;
    }

    .theme-card {
        background: #171728;
        border-left: 3px solid #7F77DD;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }

    .prd-doc, .prd-doc p, .prd-doc li, .prd-doc td, .prd-doc th, .prd-doc h4 {
        font-family: "Times New Roman", Times, serif !important;
        font-size: 15px !important;
    }
    .prd-doc h3 {
        font-family: "Times New Roman", Times, serif !important;
        font-size: 18px !important;
    }
    .prd-doc h1 {
        font-family: "Times New Roman", Times, serif !important;
        font-size: 26px !important;
        text-align: center;
    }
    .prd-doc h2 {
        font-family: "Times New Roman", Times, serif !important;
        font-size: 20px !important;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_client():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")


def call_ai(prompt: str) -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is not set.")
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
        extra_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "AI Product Manager Copilot",
        },
    )
    return response.choices[0].message.content


def safe_json_parse(text: str):
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


def markdown_to_pdf_bytes(markdown_text: str) -> bytes:
    """Convert PRD markdown (including tables and inline HTML like <u>) into a styled PDF,
    matching the on-screen font sizing: 26px title / 20px sub-heading / 18px section headings /
    15px body text, all in Times New Roman."""
    html_body = md_lib.markdown(markdown_text, extensions=["tables"])
    html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: "Times New Roman", Times, serif; font-size: 15px; line-height: 1.4; }}
        h1 {{ font-size: 26px; text-align: center; }}
        h2 {{ font-size: 20px; text-align: center; }}
        h3 {{ font-size: 18px; margin-top: 18px; }}
        h4 {{ font-size: 16px; margin-top: 12px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0 16px 0; }}
        th, td {{ border: 1px solid #444; padding: 6px 8px; font-size: 13px; text-align: left; }}
        th {{ background-color: #e8e8e8; }}
        li {{ margin-bottom: 4px; }}
    </style>
    </head>
    <body>
    {html_body}
    </body>
    </html>
    """
    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    return buffer.getvalue()


def staged_progress(container, stages: list[str]):
    """Show a progress bar that steps through labeled stages. Returns the bar/text placeholders
    so the caller can advance them, or just use as a quick visual before a real call."""
    bar = container.progress(0, text=stages[0])
    return bar


def log_history(kind: str, summary: str):
    st.session_state.history.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "kind": kind,
        "summary": summary,
    })
    st.session_state.history = st.session_state.history[:10]


STATE_FILE = "app_state.json"


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state():
    try:
        data = {
            "feedback_insights": st.session_state.feedback_insights,
            "themes": st.session_state.themes,
            "prds_generated": st.session_state.prds_generated,
            "history": st.session_state.history,
            "moscow_kano": st.session_state.moscow_kano,
            "final_recommendation": st.session_state.final_recommendation,
            "rice_table": st.session_state.rice_table.to_dict(orient="records"),
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass 

_saved = load_state()

defaults = {
    "feedback_insights": _saved.get("feedback_insights", []),
    "themes": _saved.get("themes", []),
    "prds_generated": _saved.get("prds_generated", []),
    "history": _saved.get("history", []),
    "moscow_kano": _saved.get("moscow_kano", []),
    "final_recommendation": _saved.get("final_recommendation", ""),
    "rice_table": pd.DataFrame(_saved["rice_table"]) if _saved.get("rice_table") else pd.DataFrame(
        [
            {"Feature Name": "Offline Maps", "Reach": 8000, "Impact": 3, "Confidence": 0.8, "Effort": 5},
            {"Feature Name": "Dark Mode", "Reach": 3000, "Impact": 1, "Confidence": 0.9, "Effort": 2},
        ]
    ),
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

st.title("🧠 AI Product Manager Copilot")

if not os.environ.get("OPENROUTER_API_KEY"):
    st.warning(
        "OPENROUTER_API_KEY is not set. Create a `.env` file in this folder with:\n\n"
        "`OPENROUTER_API_KEY=sk-or-...`",
        icon="⚠️",
    )


with st.sidebar:
    st.markdown("### Session history")
    if st.session_state.history:
        for h in st.session_state.history:
            st.markdown(f"**{h['time']}** · {h['kind']}  \n<span style='color:#9d9db0; font-size:13px;'>{h['summary']}</span>", unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.caption("Nothing yet — actions you take will show up here.")

tab_insights, tab_feedback, tab_prd, tab_rice = st.tabs(
    ["🏠 Insights Dashboard", "💬 Feedback Analyzer", "📄 PRD Generator", "📊 RICE Prioritization"]
)

with tab_insights:
    st.subheader("Session overview")

    has_data = st.session_state.feedback_insights or st.session_state.prds_generated

    if has_data:
        top_feature = "—"
        top_score = None
        if not st.session_state.rice_table.empty and "RICE Score" in st.session_state.rice_table.columns:
            top_row = st.session_state.rice_table.sort_values("RICE Score", ascending=False).iloc[0]
            top_feature = top_row["Feature Name"]
            top_score = top_row["RICE Score"]

        high_severity = sum(1 for i in st.session_state.feedback_insights if i.get("severity") == "High")

        c1, c2, c3, c4 = st.columns(4)
        for col, label, value in zip(
            [c1, c2, c3, c4],
            ["Feedback analyzed", "PRDs generated", "High-severity issues", "Top priority feature"],
            [len(st.session_state.feedback_insights), len(st.session_state.prds_generated), high_severity, top_feature],
        ):
            col.markdown(
                f"<div class='metric-card'><p class='metric-label'>{label}</p>"
                f"<p class='metric-value'>{value}</p></div>",
                unsafe_allow_html=True,
            )

        if st.session_state.themes:
            st.markdown("### Top recurring themes")
            for theme in st.session_state.themes:
                st.markdown(
                    f"<div class='theme-card'><b>{theme['theme_name']}</b><br>"
                    f"<span style='color:#c8c8d8;'>{theme['description']}</span><br>"
                    f"<span style='color:#9d9db0; font-size:12px;'>{theme['frequency_note']}</span></div>",
                    unsafe_allow_html=True,
                )

        if not st.session_state.rice_table.empty and "RICE Score" in st.session_state.rice_table.columns:
            st.markdown("### Feature priority snapshot")
            df = st.session_state.rice_table.sort_values("RICE Score", ascending=True)
            fig = go.Figure(go.Bar(
                x=df["RICE Score"], y=df["Feature Name"], orientation="h",
                marker_color="#7F77DD",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#ffffff", height=280, margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(gridcolor="#2a2a3d"), yaxis=dict(gridcolor="#2a2a3d"),
            )
            st.plotly_chart(fig, use_container_width=True, key="insights_dashboard_chart")
    else:
        st.info(
            "No data yet this session. Head to **Feedback Analyzer** and try the sample data button "
            "to see the whole pipeline in action.",
            icon="👋",
        )

with tab_feedback:
    st.subheader("Paste customer feedback here")
    st.caption("One piece of feedback per line — reviews, interview notes, support tickets, etc.")

    col_a, col_b = st.columns([5, 1])
    with col_b:
        use_sample = st.button("Try sample data")

    default_text = SAMPLE_FEEDBACK if use_sample else ""
    feedback_input = st.text_area("Feedback", value=default_text, height=200, label_visibility="collapsed")

    if st.button("Analyze", type="primary"):
        if not feedback_input.strip():
            st.error("Please paste some feedback first, or click 'Try sample data'.")
        else:
            progress = st.progress(0, text="Extracting insights...")
            try:
                prompt = FEEDBACK_EXTRACTION_PROMPT.format(feedback=feedback_input)
                raw = call_ai(prompt)
                insights = safe_json_parse(raw)
                st.session_state.feedback_insights = insights
                progress.progress(60, text="Clustering recurring themes...")

                insight_summaries = "\n".join(f"- {item['user_insight']}" for item in insights)
                theme_prompt = THEME_CLUSTERING_PROMPT.format(insights=insight_summaries)
                raw_themes = call_ai(theme_prompt)
                st.session_state.themes = safe_json_parse(raw_themes)
                progress.progress(100, text="Done")
                time.sleep(0.3)
                progress.empty()

                log_history("Feedback analyzed", f"{len(insights)} item(s)")
                save_state()
                st.success(f"Analyzed {len(insights)} feedback item(s).")
            except json.JSONDecodeError:
                progress.empty()
                st.error("The AI response wasn't valid JSON. Try again, or simplify the input.")
            except Exception as e:
                progress.empty()
                st.error(f"Something went wrong: {e}")

    if st.session_state.feedback_insights:
        st.markdown("### Extracted insights")
        for item in st.session_state.feedback_insights:
            sev = item.get("severity", "Medium")
            colors = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["Medium"])
            st.markdown(
                f"""<div class='insight-card'>
                <span class='badge' style='background:{colors['bg']}; color:{colors['text']};'>{sev} severity</span>
                <div class='insight-feedback'>"{item['feedback_text']}"</div>
                <div class='insight-row'><span class='insight-label'>Insight:</span> {item['user_insight']}</div>
                <div class='insight-row'><span class='insight-label'>Pain point:</span> {item['pain_point']}</div>
                <div class='insight-row'><span class='insight-label'>Opportunity:</span> {item['opportunity']}</div>
                <div class='insight-row'><span class='insight-label'>Suggested feature:</span> {item['suggested_feature']}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            

        if st.session_state.themes:
            st.markdown("### Top 3 recurring themes")
            for theme in st.session_state.themes:
                st.markdown(
                    f"<div class='theme-card'><b>{theme['theme_name']}</b><br>"
                    f"<span style='color:#c8c8d8;'>{theme['description']}</span><br>"
                    f"<span style='color:#9d9db0; font-size:12px;'>{theme['frequency_note']}</span></div>",
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------------------------
# TAB 3: PRD GENERATOR
# ---------------------------------------------------------------------------
with tab_prd:
    st.subheader("Generate a PRD")

    source = st.radio("Feature source", ["Write my own idea", "Pick from extracted suggestions"], horizontal=True)

    feature_idea = ""
    feature_context = ""
    if source == "Write my own idea":
        feature_idea = st.text_input("Describe the feature idea", placeholder="e.g. Build a feature that allows users to share live location")
        feature_context = feature_idea
    else:
        suggestions = [item["suggested_feature"] for item in st.session_state.feedback_insights]
        if suggestions:
            feature_idea = st.selectbox("Pick a suggested feature", suggestions)
            matching = next((i for i in st.session_state.feedback_insights if i["suggested_feature"] == feature_idea), None)
            if matching:
                feature_context = (
                    f"Feature: {feature_idea}\n"
                    f"Originating user insight: {matching['user_insight']}\n"
                    f"Pain point: {matching['pain_point']}\n"
                    f"Opportunity: {matching['opportunity']}\n"
                    f"Severity: {matching.get('severity', 'Medium')}"
                )
            else:
                feature_context = feature_idea
        else:
            st.info("No suggested features yet — analyze some feedback in the Feedback Analyzer tab first.")

    if st.button("Generate PRD", type="primary"):
        if not feature_idea.strip():
            st.error("Please provide or select a feature idea first.")
        else:
            progress = st.progress(0, text="Drafting PRD...")
            try:
                prompt = PRD_GENERATION_PROMPT.format(feature_idea=feature_context)
                prd_markdown = call_ai(prompt)
                prd_markdown = prd_markdown.strip()
                if prd_markdown.startswith("```"):
                    prd_markdown = prd_markdown.split("\n", 1)[1] if "\n" in prd_markdown else prd_markdown
                    prd_markdown = prd_markdown.removeprefix("markdown").strip()
                    if prd_markdown.endswith("```"):
                        prd_markdown = prd_markdown[:-3].strip()
                progress.progress(100, text="Done")
                time.sleep(0.3)
                progress.empty()
                st.session_state.prds_generated.append({"feature": feature_idea, "content": prd_markdown})
                log_history("PRD generated", feature_idea)
                save_state()
                st.success("PRD generated below.")
            except Exception as e:
                progress.empty()
                st.error(f"Something went wrong: {e}")

    if st.session_state.prds_generated:
        latest = st.session_state.prds_generated[-1]
        st.markdown("---")
        with st.container(border=True):
            st.markdown(f"<div class='prd-doc'>\n\n{latest['content']}\n\n</div>", unsafe_allow_html=True)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "Download as .md",
                data=latest["content"],
                file_name=f"PRD_{latest['feature'][:30].replace(' ', '_')}.md",
                mime="text/markdown",
            )
        with col_dl2:
            try:
                pdf_bytes = markdown_to_pdf_bytes(latest["content"])
                st.download_button(
                    "Download as PDF",
                    data=pdf_bytes,
                    file_name=f"PRD_{latest['feature'][:30].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.caption(f"PDF export unavailable: {e}")

# ---------------------------------------------------------------------------
# TAB 4: RICE PRIORITIZATION
# ---------------------------------------------------------------------------
with tab_rice:
    st.subheader("Prioritize features (RICE framework)")
    st.caption("Priority score = (Reach × Impact × Confidence) / Effort")

    edited_df = st.data_editor(
        st.session_state.rice_table,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Impact": st.column_config.NumberColumn(min_value=1, max_value=3, step=1),
            "Confidence": st.column_config.NumberColumn(min_value=0.0, max_value=1.0, step=0.05),
            "Effort": st.column_config.NumberColumn(min_value=0.1, step=0.5),
        },
    )

    if not edited_df.empty:
        edited_df = edited_df.copy()
        edited_df["RICE Score"] = (
            edited_df["Reach"] * edited_df["Impact"] * edited_df["Confidence"] / edited_df["Effort"]
        ).round(1)
        edited_df = edited_df.sort_values("RICE Score", ascending=False).reset_index(drop=True)
        st.session_state.rice_table = edited_df
        save_state()

        col_table, col_chart = st.columns([1, 1])
        with col_table:
            st.markdown("### Ranked features")
            st.dataframe(edited_df, use_container_width=True)
        with col_chart:
            st.markdown("### Score comparison")
            chart_df = edited_df.sort_values("RICE Score", ascending=True)
            fig = go.Figure(go.Bar(
                x=chart_df["RICE Score"], y=chart_df["Feature Name"], orientation="h",
                marker_color="#7F77DD",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#ffffff", height=280, margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(gridcolor="#2a2a3d"), yaxis=dict(gridcolor="#2a2a3d"),
            )
            st.plotly_chart(fig, use_container_width=True, key="rice_tab_chart")
            progress = st.progress(0, text="Weighing tradeoffs...")
            try:
                ranked_text = edited_df.to_string(index=False)
                prompt = RICE_RECOMMENDATION_PROMPT.format(ranked_features=ranked_text)
                recommendation = call_ai(prompt)
                progress.progress(100, text="Done")
                time.sleep(0.3)
                progress.empty()
                log_history("RICE recommendation", edited_df.iloc[0]["Feature Name"])
                st.markdown(
                    f"<div class='insight-card'><b>Recommendation</b><br><br>{recommendation}</div>",
                    unsafe_allow_html=True,
                )
            except Exception as e:
                progress.empty()
                st.error(f"Something went wrong: {e}")

        # -------------------------------------------------------------
        # Cross-framework analysis: MoSCoW + Kano + final synthesis
        # -------------------------------------------------------------
        st.markdown("---")
        st.markdown("### Cross-check with MoSCoW and Kano")
        st.caption("RICE tells you the math. These two frameworks add urgency and satisfaction lenses on top.")

        if st.button("Run MoSCoW + Kano analysis"):
            progress = st.progress(0, text="Classifying by urgency (MoSCoW)...")
            try:
                ranked_text = edited_df.to_string(index=False)
                mk_prompt = MOSCOW_KANO_PROMPT.format(ranked_features=ranked_text)
                raw_mk = call_ai(mk_prompt)
                classifications = safe_json_parse(raw_mk)
                st.session_state.moscow_kano = classifications
                progress.progress(55, text="Synthesizing final recommendation...")

                mk_summary = "\n".join(
                    f"- {c['feature_name']}: MoSCoW={c['moscow']}, Kano={c['kano']} ({c['reasoning']})"
                    for c in classifications
                )
                final_prompt = FINAL_RECOMMENDATION_PROMPT.format(
                    rice_summary=ranked_text, moscow_kano_summary=mk_summary
                )
                final_rec = call_ai(final_prompt)
                st.session_state.final_recommendation = final_rec

                progress.progress(100, text="Done")
                time.sleep(0.3)
                progress.empty()
                log_history("MoSCoW + Kano analysis", f"{len(classifications)} feature(s)")
                save_state()
            except json.JSONDecodeError:
                progress.empty()
                st.error("The AI response wasn't valid JSON. Try again.")
            except Exception as e:
                progress.empty()
                st.error(f"Something went wrong: {e}")

        if st.session_state.moscow_kano:
            moscow_colors = {
                "Must-have": SEVERITY_COLORS["High"],
                "Should-have": SEVERITY_COLORS["Medium"],
                "Could-have": SEVERITY_COLORS["Low"],
                "Won't-have": {"bg": "#2a2a3d", "text": "#9d9db0"},
            }
            for c in st.session_state.moscow_kano:
                mcolor = moscow_colors.get(c["moscow"], SEVERITY_COLORS["Medium"])
                st.markdown(
                    f"""<div class='insight-card'>
                    <b>{c['feature_name']}</b><br>
                    <span class='badge' style='background:{mcolor['bg']}; color:{mcolor['text']};'>MoSCoW: {c['moscow']}</span>
                    <span class='badge' style='background:#26215C; color:#AFA9EC; margin-left:6px;'>Kano: {c['kano']}</span>
                    <div class='insight-row' style='margin-top:6px;'>{c['reasoning']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        if st.session_state.final_recommendation:
            st.markdown("### Final build recommendation")
            st.markdown(
                f"<div class='insight-card' style='border-left: 3px solid #7F77DD;'>"
                f"{st.session_state.final_recommendation}</div>",
                unsafe_allow_html=True,
            )

        # -------------------------------------------------------------
        # Methodology explainer
        # -------------------------------------------------------------
        st.markdown("---")
        with st.expander("How these scores and frameworks are calculated"):
            st.markdown(
                """
**RICE — how each input is scored**

- **Reach**: number of users or events affected in a fixed timeframe (e.g. per quarter). Pulled from
  analytics, support ticket volume, or survey response counts — a concrete number, not a guess.
- **Impact**: how much the feature moves the needle per user, usually scored on a simple scale
  (3 = massive, 2 = high, 1 = medium, 0.5 = low, 0.25 = minimal). Based on the severity of the pain
  point it solves or the upside it unlocks.
- **Confidence**: how sure you are about your Reach and Impact estimates, as a percentage (0–1).
  High confidence (0.8–1.0) means you have hard data; low confidence (0.3–0.5) means it's mostly
  a hunch.
- **Effort**: estimated person-months (or weeks) of engineering + design + QA work to ship it.

Priority Score = (Reach × Impact × Confidence) / Effort — higher score means more value for less cost.

---

**MoSCoW Method** categorizes requirements into Must-haves (essential for launch), Should-haves
(important but not critical), Could-haves (desirable if resources allow), and Won't-haves (excluded
from current scope). It is particularly effective for Agile releases and stakeholder alignment.

*How it's used here*: each feature from your RICE table is re-evaluated purely on urgency and scope —
independent of its raw score — to answer "does this need to ship now, or can it wait?"

---

**Kano Model** classifies features by their impact on customer satisfaction, distinguishing between
Basic needs (expected), Performance features (linear satisfaction), and Delighters (unexpected value).
It helps teams prioritize features that drive loyalty and competitive advantage.

*How it's used here*: each feature is classified by the kind of satisfaction it drives — fixing a Basic
need prevents churn, while a Delighter can differentiate the product even at a lower RICE score.

---

**Why run all three**: RICE is a numeric shortcut, but it can rank a "boring but essential" fix below a
flashy feature if the numbers happen to favor it. MoSCoW catches launch-blocking urgency that RICE
might underweight, and Kano catches satisfaction/loyalty effects that pure reach-and-effort math
misses. The final recommendation above weighs all three together rather than trusting one score in
isolation.
"""
            )
