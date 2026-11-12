"""Page 3: how the conditional expectation is computed, shown on a small example."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from survival import expected_months, rebased_curve
from ui import PALETTE, callout, section

# Subscribers still here at the start of each month, out of 100 who joined.
STILL_HERE = [100, 70, 50, 40, 30, 25, 20]
TODAY = 2
MONTHS_AHEAD = 4

BAR_FILL = "rgba(234, 88, 12, 0.22)"
PAST_FILL = "#E2E8F0"
CHART_CONFIG = {"displayModeBar": False, "staticPlot": True}


def bar_chart(x_title: str, y_title: str, x_range: list[float], x_ticks: list[int]) -> go.Figure:
    """Empty chart with the shared look of this page."""
    axis_font = {"size": 15, "color": PALETTE["muted"]}
    fig = go.Figure()
    fig.update_xaxes(
        title_text=x_title, range=x_range, tickvals=x_ticks,
        showgrid=False, zeroline=False, tickfont=axis_font, title_font=axis_font,
    )
    fig.update_yaxes(
        title_text=y_title, showgrid=True, gridcolor=PALETTE["line"], zeroline=False,
        tickfont=axis_font, title_font=axis_font,
        # A fixed left margin keeps "Today" at the same place in every chart.
        automargin=False,
    )
    fig.update_layout(
        height=340,
        margin={"l": 85, "r": 10, "t": 45, "b": 10},
        showlegend=False,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        uniformtext={"minsize": 19, "mode": "show"},
    )
    return fig


def add_bars(fig: go.Figure, starts: list[int], heights: list[float], labels: list[str],
             fill: str, text_color: str) -> None:
    """One bar per month, each starting at `starts` and one month wide."""
    fig.add_trace(go.Bar(
        x=[start + 0.5 for start in starts], y=heights, width=1, hoverinfo="skip",
        text=labels, textposition="inside", insidetextanchor="middle", textangle=0,
        textfont={"size": 19, "color": text_color},
        marker={"color": fill, "line": {"color": "#FFFFFF", "width": 3}},
    ))


def add_curve(fig: go.Figure, starts: list[int], heights: list[float]) -> None:
    """The survival curve that runs along the top of the bars."""
    fig.add_trace(go.Scatter(
        x=[*starts, starts[-1] + 1], y=[*heights, heights[-1]], mode="lines", hoverinfo="skip",
        line={"color": PALETTE["pink"], "width": 4, "shape": "hv"},
    ))


def add_today(fig: go.Figure, month: int) -> None:
    fig.add_vline(x=month, line_color=PALETTE["ink"], line_width=2)
    fig.add_annotation(
        x=month, y=1.1, yref="paper", text="<b>Today</b>", showarrow=False,
        font={"size": 15, "color": PALETTE["ink"]},
    )


def count_chart(highlight_from: int) -> go.Figure:
    """Subscribers still here each month. Months before `highlight_from` are greyed out."""
    months = list(range(len(STILL_HERE) - 1))
    counts = STILL_HERE[:-1]
    fig = bar_chart("Months since joining", "Subscribers still here", [-0.3, len(months) + 0.3],
                    list(range(len(STILL_HERE))))
    fig.update_yaxes(range=[0, 108], tickvals=[0, 25, 50, 75, 100])
    if highlight_from:
        add_bars(fig, months[:highlight_from], counts[:highlight_from],
                 [str(count) for count in counts[:highlight_from]], PAST_FILL, PALETTE["faint"])
    add_bars(fig, months[highlight_from:], counts[highlight_from:],
             [f"<b>{count}</b>" for count in counts[highlight_from:]], BAR_FILL, PALETTE["ink"])
    add_curve(fig, months[highlight_from:], counts[highlight_from:])
    if highlight_from:
        add_today(fig, highlight_from)
    return fig


def share_chart(shares: list[float], reached: int) -> go.Figure:
    """The same bars after dividing by the subscribers who reached today."""
    months = list(range(len(shares)))
    # The x-axis keeps the width of the charts above, so today stays in the same place.
    fig = bar_chart("Months from today", "Still subscribed", [-TODAY - 0.3, len(months) + 0.3],
                    list(range(len(months) + 1)))
    fig.update_yaxes(range=[0, 1.3], tickvals=[0, 0.25, 0.5, 0.75, 1], tickformat=".0%")
    add_bars(fig, months, shares, [f"<b>{share:.0%}</b>" for share in shares], BAR_FILL, PALETTE["ink"])
    add_curve(fig, months, shares)
    for month, share in zip(months, shares):
        fig.add_annotation(
            x=month + 0.5, y=share + 0.1, showarrow=False,
            text=f"{round(share * reached)} ÷ {reached}",
            font={"size": 17, "color": PALETTE["orange"]},
        )
    add_today(fig, 0)
    return fig


curve = pd.Series(STILL_HERE, index=range(len(STILL_HERE))) / STILL_HERE[0]
window = rebased_curve(curve, TODAY, MONTHS_AHEAD)
shares = window.iloc[:-1].tolist()
remaining = expected_months(window)
reached = STILL_HERE[TODAY]

st.html(
    f"""
    <div class="hero">
        <div class="eyebrow">Step by step</div>
        <h1>How long will they stay, given they are still here?</h1>
        <p>The whole calculation, on a small example with {STILL_HERE[0]} subscribers.</p>
    </div>
    """
)

section(
    "1 · Start with the survival curve",
    f"{STILL_HERE[0]} subscribers join. Each bar is how many are still here in that month.",
)
with st.container(border=True):
    st.plotly_chart(count_chart(0), width="stretch", config=CHART_CONFIG)

section(
    "2 · Keep only who is still here today",
    f"Today is month {TODAY}. {reached} subscribers made it this far, and only their future matters.",
)
with st.container(border=True):
    st.plotly_chart(count_chart(TODAY), width="stretch", config=CHART_CONFIG)

section(
    "3 · Make today the new 100%",
    f"Those {reached} are now the whole group. Divide every bar by {reached}.",
)
with st.container(border=True):
    st.plotly_chart(share_chart(shares, reached), width="stretch", config=CHART_CONFIG)

section(
    "4 · Add up the bars",
    f"Each bar is one month wide, so a bar at {shares[1]:.0%} adds {shares[1]:.1f} months.",
)
terms = '<div class="operator">+</div>'.join(
    f"""
    <div class="term soft">
        <span class="tag">Month {month}</span>
        <div class="value">{share:.1f}</div>
        <div class="hint">{share:.0%} of a month</div>
    </div>
    """
    for month, share in enumerate(shares, start=1)
)
st.html(
    f"""
    <div class="equation compact">
        {terms}
        <div class="operator">=</div>
        <div class="term" style="--accent: {PALETTE['orange']}">
            <span class="tag">Total</span>
            <div class="value">{remaining:.1f}</div>
            <div class="hint">months remaining</div>
        </div>
    </div>
    """
)

callout(
    "🧮",
    "In one line",
    "Remaining months = area under the curve after today ÷ share still here today.",
)
