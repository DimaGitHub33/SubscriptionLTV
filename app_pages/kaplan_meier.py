"""Page 2: lifetime value from a Kaplan–Meier survival curve."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import loaders
from charts import (
    CHART_CONFIG, HORIZON_YEARS, MAX_TENURE, add_area, add_curve, add_marker_line, add_today, survival_chart,
)
from data import PLANS
from survival import HORIZON_MONTHS, curve_window
from ui import PALETTE, callout, dollars, remaining_months_tiles, section


def lifetime_chart(curve: pd.Series) -> go.Figure:
    """The survival curve, with the area under its first years shaded."""
    fig = survival_chart()
    add_area(fig, curve_window(curve, 0), decimals=1)
    add_curve(fig, curve, PALETTE["pink"], 4)
    add_marker_line(fig, HORIZON_MONTHS, f"{HORIZON_YEARS} years", "dot")
    return fig


def remaining_chart(curve: pd.Series, window: pd.Series) -> go.Figure:
    """The two numbers behind the remaining months: the area ahead, and the share still here today."""
    fig = survival_chart()
    add_area(fig, window, decimals=2)
    add_curve(fig, curve, PALETTE["pink"], 4)
    add_today(fig, window)
    return fig


curve = loaders.kaplan_meier_curve()
subscriber_count = len(loaders.subscribers())

st.html(
    """
    <div class="hero">
        <div class="eyebrow">The baseline</div>
        <h1>Kaplan–Meier: one survival curve for everyone</h1>
        <p>Count who is still subscribed, month after month.
        The area under that curve is how long subscribers stay.</p>
    </div>
    """
)

section(
    "1 · How long do subscribers stay?",
    "The curve is the share still subscribed. The area under it is the expected time subscribed.",
)
with st.container(border=True):
    st.plotly_chart(lifetime_chart(curve), width="stretch", config=CHART_CONFIG)
st.html(f'<div class="note">Kaplan–Meier estimate from {subscriber_count:,} synthetic subscribers</div>')

section(
    "2 · Already subscribed? Count only the months ahead.",
    f"Take the area under the next {HORIZON_YEARS} years of the curve, "
    "then divide by the share of subscribers who are still here today.",
)
tenure = st.slider("Months already subscribed", 0, MAX_TENURE, 12)
window = curve_window(curve, tenure)
with st.container(border=True):
    st.plotly_chart(remaining_chart(curve, window), width="stretch", config=CHART_CONFIG)
months = remaining_months_tiles(window)
st.html(
    '<div class="note">The area is an average over everyone who joined. '
    "Dividing by the share still here turns it into an average over those who remain.</div>"
)

section("3 · Turn months into value")
plan = st.radio(
    "Plan", list(PLANS), index=1, horizontal=True,
    format_func=lambda name: f"{name} · \\${PLANS[name]}",
)
subscriber = "for a new subscriber" if tenure == 0 else f"after {tenure} months subscribed"
st.html(
    f"""
    <div class="equation">
        <div class="term" style="--accent: {PALETTE['blue']}">
            <span class="tag">Monthly revenue</span>
            <div class="value">${PLANS[plan]}</div>
            <div class="hint">{plan} plan</div>
        </div>
        <div class="operator">×</div>
        <div class="term" style="--accent: {PALETTE['orange']}">
            <span class="tag">Remaining months</span>
            <div class="value">{months:.1f}</div>
            <div class="hint">{subscriber}</div>
        </div>
        <div class="operator">=</div>
        <div class="term" style="--accent: {PALETTE['green']}">
            <span class="tag">Lifetime value</span>
            <div class="value">{dollars(PLANS[plan] * months)}</div>
            <div class="hint">over the next {HORIZON_YEARS} years</div>
        </div>
    </div>
    """
)

callout(
    "🧩",
    "The limit",
    "Same tenure, same curve, whoever the subscriber is. The Cox model makes it personal.",
)
