"""Page 2: lifetime value from a Kaplan–Meier survival curve."""

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import PLANS, generate_subscribers
from survival import HORIZON_MONTHS, expected_months, kaplan_meier, rebased_curve, survival_at
from ui import PALETTE, callout, section

CHART_MONTHS = 72
# Beyond this tenure the horizon would reach past the part of the curve shown here.
MAX_TENURE = CHART_MONTHS - HORIZON_MONTHS
HORIZON_YEARS = HORIZON_MONTHS // 12
AREA_FILL = "rgba(234, 88, 12, 0.20)"
CHART_CONFIG = {"displayModeBar": False, "staticPlot": True}


@st.cache_data
def load_curve() -> tuple[pd.Series, int]:
    """Kaplan–Meier curve of the synthetic subscribers, and how many there are."""
    subscribers = generate_subscribers()
    return kaplan_meier(subscribers), len(subscribers)


def survival_chart() -> go.Figure:
    """Empty chart with the shared survival axes."""
    fig = go.Figure()
    fig.update_xaxes(
        title_text="Months since joining", range=[-1.5, CHART_MONTHS + 3],
        tickvals=list(range(0, CHART_MONTHS + 1, 12)),
        showgrid=True, gridcolor=PALETTE["line"], zeroline=False,
        tickfont={"size": 15, "color": PALETTE["muted"]},
        title_font={"size": 15, "color": PALETTE["muted"]},
    )
    fig.update_yaxes(
        title_text="Still subscribed", range=[0, 1.06],
        tickvals=[0, 0.25, 0.5, 0.75, 1], tickformat=".0%",
        showgrid=True, gridcolor=PALETTE["line"], zeroline=False,
        tickfont={"size": 15, "color": PALETTE["muted"]},
        title_font={"size": 15, "color": PALETTE["muted"]},
    )
    fig.update_layout(
        height=430,
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
        showlegend=False,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig


def add_curve(fig: go.Figure, curve: pd.Series, color: str, width: int) -> None:
    fig.add_trace(go.Scatter(
        x=curve.index, y=curve, mode="lines", hoverinfo="skip",
        line={"color": color, "width": width, "shape": "hv"},
    ))


def add_area(fig: go.Figure, window: pd.Series, caption: str) -> None:
    """Shade the area under a curve and label it with the months it adds up to."""
    fig.add_trace(go.Scatter(
        x=window.index, y=window, mode="lines", hoverinfo="skip",
        line={"width": 0, "shape": "hv"}, fill="tozeroy", fillcolor=AREA_FILL,
    ))
    fig.add_annotation(
        x=(window.index[0] + window.index[-1]) / 2, y=0.22, showarrow=False,
        text=f"<b>{expected_months(window):.1f} months</b><br>{caption}",
        font={"size": 19, "color": PALETTE["orange"]},
    )


def add_marker_line(fig: go.Figure, month: float, label: str, dash: str) -> None:
    fig.add_vline(x=month, line_color=PALETTE["ink"], line_width=2, line_dash=dash)
    fig.add_annotation(
        x=month, y=1.09, yref="paper", text=label, showarrow=False,
        font={"size": 15, "color": PALETTE["ink"]},
    )


def lifetime_chart(curve: pd.Series) -> go.Figure:
    """The survival curve, with the area under its first years shaded."""
    fig = survival_chart()
    add_area(fig, rebased_curve(curve, 0), "area under the curve")
    add_curve(fig, curve, PALETTE["pink"], 4)
    add_marker_line(fig, HORIZON_MONTHS, f"{HORIZON_YEARS} years", "dot")
    return fig


def remaining_chart(curve: pd.Series, tenure: int) -> go.Figure:
    """The same curve, restarted at 100% for a subscriber who has reached `tenure`."""
    window = rebased_curve(curve, tenure)
    fig = survival_chart()
    add_curve(fig, curve, PALETTE["faint"], 3)
    add_area(fig, window, "expected remaining")
    add_curve(fig, window, PALETTE["pink"], 4)
    fig.add_trace(go.Scatter(
        x=[tenure, tenure], y=[survival_at(curve, tenure), 1], mode="markers", hoverinfo="skip",
        marker={"size": 13, "color": [PALETTE["faint"], PALETTE["pink"]],
                "line": {"color": "#FFFFFF", "width": 2}},
    ))
    add_marker_line(fig, tenure, "<b>Today</b>", "solid")
    add_marker_line(fig, tenure + HORIZON_MONTHS, f"+{HORIZON_YEARS} years", "dot")
    return fig


curve, subscriber_count = load_curve()

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

heading = st.container()
tenure = st.slider("Months already subscribed", 0, MAX_TENURE, 12)
with heading:
    if tenure == 0:
        reached = "A new subscriber starts at 100%."
    else:
        reached = (
            f"{survival_at(curve, tenure):.0%} of subscribers reach month {tenure}. "
            "For them, the curve restarts at 100%."
        )
    section("2 · Already subscribed? Start from today.", reached)
with st.container(border=True):
    st.plotly_chart(remaining_chart(curve, tenure), width="stretch", config=CHART_CONFIG)

section("3 · Turn months into value")
plan = st.radio(
    "Plan", list(PLANS), index=1, horizontal=True,
    format_func=lambda name: f"{name} · \\${PLANS[name]}",
)
# Value is computed from the rounded months so the three tiles multiply out exactly as shown.
months = round(expected_months(rebased_curve(curve, tenure)), 1)
lifetime_value = math.floor(PLANS[plan] * months + 0.5)
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
            <div class="value">${lifetime_value:,}</div>
            <div class="hint">over the next {HORIZON_YEARS} years</div>
        </div>
    </div>
    """
)

callout(
    "🧩",
    "The limit",
    "Same tenure, same curve, whoever the subscriber is. The Cox model will make it personal.",
)
