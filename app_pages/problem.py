"""Page 1: the problem this project sets out to solve."""

import plotly.graph_objects as go
import streamlit as st

from survival import HORIZON_MONTHS
from ui import PALETTE, callout, section

# Illustrative subscribers: (name, months since joining, months since cancelling or None if active).
SUBSCRIBERS = [
    ("Subscriber A", 28, None),
    ("Subscriber B", 26, 9),
    ("Subscriber C", 21, None),
    ("Subscriber D", 17, 12),
    ("Subscriber E", 10, None),
    ("Subscriber F", 4, None),
]


def subscriber_timeline() -> go.Figure:
    """Known subscription history up to today, and the unknown months after it."""
    active_x, active_y = [], []
    cancelled_x, cancelled_y = [], []
    future_x, future_y = [], []
    for name, joined, cancelled in SUBSCRIBERS:
        if cancelled is None:
            active_x += [-joined, 0, None]
            active_y += [name, name, None]
            future_x += [0, HORIZON_MONTHS, None]
            future_y += [name, name, None]
        else:
            cancelled_x += [-joined, -cancelled, None]
            cancelled_y += [name, name, None]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=active_x, y=active_y, mode="lines", name="Subscribed",
        line={"color": PALETTE["blue"], "width": 14}, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=cancelled_x, y=cancelled_y, mode="lines", name="Cancelled",
        line={"color": PALETTE["faint"], "width": 14}, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=future_x, y=future_y, mode="lines", name="Unknown",
        line={"color": PALETTE["orange"], "width": 3, "dash": "dot"}, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=[-cancelled for _, _, cancelled in SUBSCRIBERS if cancelled is not None],
        y=[name for name, _, cancelled in SUBSCRIBERS if cancelled is not None],
        mode="markers", showlegend=False, hoverinfo="skip",
        marker={"symbol": "x", "size": 13, "color": PALETTE["red"],
                "line": {"color": "#FFFFFF", "width": 1}},
    ))

    for name, _, cancelled in SUBSCRIBERS:
        if cancelled is None:
            fig.add_annotation(
                x=HORIZON_MONTHS / 2, y=name, text="<b>?</b>", showarrow=False,
                font={"size": 20, "color": PALETTE["orange"]}, bgcolor="#FFF7ED", borderpad=3,
            )

    fig.add_vrect(x0=0, x1=HORIZON_MONTHS, fillcolor=PALETTE["orange"], opacity=0.07, line_width=0)
    fig.add_vline(x=0, line_color=PALETTE["ink"], line_width=2)
    headings = [
        (-15, "<b>The past</b> · known", PALETTE["blue"]),
        (HORIZON_MONTHS / 2, "<b>The next 3 years</b> · unknown", PALETTE["orange"]),
    ]
    for x, text, color in headings:
        fig.add_annotation(
            x=x, y=1.12, yref="paper", text=text, showarrow=False,
            font={"size": 16, "color": color},
        )

    fig.update_xaxes(
        range=[-31, HORIZON_MONTHS + 5],
        tickvals=[-24, -12, 0, 12, 24, 36],
        ticktext=["2 years ago", "1 year ago", "<b>Today</b>", "+1 year", "+2 years", "+3 years"],
        showgrid=True, gridcolor=PALETTE["line"], zeroline=False, fixedrange=True,
        tickfont={"size": 15, "color": PALETTE["muted"]},
    )
    fig.update_yaxes(
        categoryorder="array", categoryarray=[name for name, _, _ in SUBSCRIBERS],
        autorange="reversed", showgrid=False, fixedrange=True, ticksuffix="  ",
        tickfont={"size": 15, "color": PALETTE["ink"]},
    )
    fig.update_layout(
        height=400,
        margin={"l": 10, "r": 10, "t": 60, "b": 10},
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        legend={"orientation": "h", "x": 0.5, "xanchor": "center", "y": -0.16, "yanchor": "top",
                "font": {"size": 15, "color": PALETTE["ink"]}},
    )
    return fig


st.html(
    """
    <div class="hero">
        <div class="eyebrow">The problem</div>
        <h1>Predicting the lifetime value of every subscriber</h1>
        <p>A subscription earns money only while the customer stays.
        Know how long they will stay, and you know their value.</p>
    </div>
    """
)

section("The idea", "Future value is what a subscriber pays each month, times the months they still stay.")
st.html(
    f"""
    <div class="equation">
        <div class="term" style="--accent: {PALETTE['blue']}">
            <span class="tag">Known</span>
            <div class="icon">💳</div>
            <div class="name">Monthly revenue</div>
            <div class="hint">What they pay</div>
        </div>
        <div class="operator">×</div>
        <div class="term" style="--accent: {PALETTE['orange']}">
            <span class="tag">Unknown</span>
            <div class="icon">⏳</div>
            <div class="name">Remaining months</div>
            <div class="hint">How long they still stay</div>
        </div>
        <div class="operator">=</div>
        <div class="term" style="--accent: {PALETTE['green']}">
            <span class="tag">The answer</span>
            <div class="icon">💰</div>
            <div class="name">Lifetime value</div>
            <div class="hint">What they are still worth</div>
        </div>
    </div>
    """
)

section("The catch", "We can see how long each subscriber has stayed so far. We cannot see how much longer they will.")
with st.container(border=True):
    st.plotly_chart(
        subscriber_timeline(),
        width="stretch",
        config={"displayModeBar": False, "staticPlot": True},
    )
st.html('<div class="note">Illustrative subscribers</div>')

callout(
    "🎯",
    "The goal",
    f"Predict the remaining months of every active subscriber over the next {HORIZON_MONTHS} months, "
    "and turn them into value.",
)
