"""Shared look and feel for every page of the app."""

import math

import pandas as pd
import streamlit as st

from survival import area_under

PALETTE = {
    "blue": "#2563EB",
    "pink": "#DB2777",
    "purple": "#7C3AED",
    "orange": "#EA580C",
    "green": "#16A34A",
    "red": "#DC2626",
    "ink": "#0F172A",
    "muted": "#64748B",
    "faint": "#94A3B8",
    "line": "#E2E8F0",
}

_CSS = """
[data-testid="stMainBlockContainer"] {
    max-width: 1080px;
    padding-top: 4.5rem;
    padding-bottom: 4rem;
}

.hero {
    background: linear-gradient(135deg, var(--blue) 0%, var(--purple) 55%, var(--pink) 100%);
    border-radius: 28px;
    padding: 60px 52px;
    color: #FFFFFF;
    box-shadow: 0 24px 48px -24px rgba(124, 58, 237, 0.55);
}
.hero .eyebrow {
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    opacity: 0.85;
}
.hero h1 {
    font-size: 3.1rem;
    font-weight: 800;
    line-height: 1.1;
    color: #FFFFFF;
    margin: 0.6rem 0 1rem;
    padding: 0;
}
.hero p {
    font-size: 1.25rem;
    line-height: 1.5;
    max-width: 640px;
    margin: 0;
    opacity: 0.95;
}

.section { margin: 2.4rem 0 0.6rem; }
.section h2 {
    font-size: 1.75rem;
    font-weight: 800;
    color: var(--ink);
    margin: 0;
    padding: 0;
}
.section p {
    font-size: 1.1rem;
    color: var(--muted);
    margin: 0.35rem 0 0;
    max-width: 720px;
}

.equation { display: flex; align-items: stretch; gap: 14px; }
.term {
    flex: 1;
    background: var(--accent);
    border-radius: 22px;
    padding: 28px 22px;
    text-align: center;
    color: #FFFFFF;
    box-shadow: 0 18px 32px -20px var(--accent);
}
.term .tag {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.24);
}
.term .icon { font-size: 2.2rem; line-height: 1; margin-top: 0.9rem; }
.term .name { font-size: 1.4rem; font-weight: 800; margin-top: 0.6rem; }
.term .value { font-size: 2.8rem; font-weight: 800; line-height: 1.1; margin-top: 0.8rem; }
.term .hint { font-size: 1rem; margin-top: 0.2rem; opacity: 0.92; }
.operator {
    align-self: center;
    font-size: 2.6rem;
    font-weight: 300;
    color: var(--faint);
}
.equation.compact { gap: 10px; }
.equation.compact .term { padding: 22px 10px; }
.equation.compact .value { font-size: 2.3rem; }
.equation.compact .hint { font-size: 0.92rem; }
.equation.compact .operator { font-size: 2rem; }
.term.soft {
    background: #FFF7ED;
    border: 2px solid #FED7AA;
    color: var(--orange);
    box-shadow: none;
}
.term.soft .tag { background: #FFEDD5; }

.callout {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-top: 2.4rem;
    padding: 28px 32px;
    border-radius: 22px;
    border: 1px solid #DDD6FE;
    background: linear-gradient(135deg, #EFF6FF 0%, #F5F3FF 55%, #FDF2F8 100%);
}
.callout .icon { font-size: 2.6rem; line-height: 1; }
.callout .label {
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--purple);
}
.callout .text {
    font-size: 1.35rem;
    font-weight: 700;
    line-height: 1.35;
    color: var(--ink);
    margin-top: 0.2rem;
}

.note { font-size: 0.9rem; color: var(--faint); text-align: center; }

.chip-row { text-align: center; }
.chip {
    display: inline-block;
    padding: 8px 20px;
    border-radius: 999px;
    border: 2px solid var(--accent);
    color: var(--accent);
    font-size: 1.1rem;
}

@media (max-width: 760px) {
    .hero { padding: 40px 28px; }
    .hero h1 { font-size: 2.2rem; }
    .equation { flex-direction: column; }
}
"""


def apply_theme() -> None:
    """Inject the shared stylesheet. Call once per run from the entry point."""
    variables = "".join(f"--{name}: {value};" for name, value in PALETTE.items())
    st.html(f"<style>:root {{{variables}}}{_CSS}</style>")


def section(title: str, subtitle: str = "") -> None:
    """Render a section heading with an optional one-line explanation."""
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.html(f'<div class="section"><h2>{title}</h2>{sub}</div>')


def callout(icon: str, label: str, text: str) -> None:
    """Render the highlighted takeaway box that closes a page."""
    st.html(
        f"""
        <div class="callout">
            <div class="icon">{icon}</div>
            <div>
                <div class="label">{label}</div>
                <div class="text">{text}</div>
            </div>
        </div>
        """
    )


def round_half_up(amount: float) -> int:
    return math.floor(amount + 0.5)


def dollars(amount: float) -> str:
    """Whole dollars, with halves rounded up."""
    return f"${round_half_up(amount):,}"


def displayed_remaining(window: pd.Series) -> tuple[float, float, float]:
    """Area ahead, share still here today, and the remaining months they give.

    The months are computed from the other two as rounded for display,
    so the figures on screen divide out exactly as shown.
    """
    area = round(area_under(window), 2)
    still_here = round(window.iloc[0], 4)
    return area, still_here, round(area / still_here, 1)


def remaining_months_tiles(window: pd.Series) -> float:
    """Show area ÷ share still here = remaining months for a stretch of a survival curve, and return the months."""
    start, end = window.index[0], window.index[-1]
    area, still_here, months = displayed_remaining(window)
    reach = "everyone starts here" if start == 0 else f"reach month {start:g}"
    st.html(
        f"""
        <div class="equation">
            <div class="term soft">
                <span class="tag">Area under the curve</span>
                <div class="value">{area:.2f}</div>
                <div class="hint">months, from month {start:g} to {end:g}</div>
            </div>
            <div class="operator">÷</div>
            <div class="term" style="--accent: {PALETTE['purple']}">
                <span class="tag">Still here today</span>
                <div class="value">{still_here:.2%}</div>
                <div class="hint">{reach}</div>
            </div>
            <div class="operator">=</div>
            <div class="term" style="--accent: {PALETTE['orange']}">
                <span class="tag">Remaining months</span>
                <div class="value">{months:.1f}</div>
                <div class="hint">expected, for those still here</div>
            </div>
        </div>
        """
    )
    return months
