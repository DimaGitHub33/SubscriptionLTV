"""Survival charts shared by the app pages."""

import pandas as pd
import plotly.graph_objects as go

from survival import HORIZON_MONTHS, area_under
from ui import PALETTE

CHART_MONTHS = 72
# Beyond this tenure the horizon would reach past the part of the curve shown in the charts.
MAX_TENURE = CHART_MONTHS - HORIZON_MONTHS
HORIZON_YEARS = HORIZON_MONTHS // 12
AREA_FILL = "rgba(234, 88, 12, 0.20)"
CHART_CONFIG = {"displayModeBar": False, "staticPlot": True}


def survival_chart() -> go.Figure:
    """Empty chart with the shared survival axes."""
    axis_font = {"size": 15, "color": PALETTE["muted"]}
    fig = go.Figure()
    fig.update_xaxes(
        title_text="Months since joining", range=[-1.5, CHART_MONTHS + 3],
        tickvals=list(range(0, CHART_MONTHS + 1, 12)),
        showgrid=True, gridcolor=PALETTE["line"], zeroline=False,
        tickfont=axis_font, title_font=axis_font,
    )
    fig.update_yaxes(
        title_text="Still subscribed", range=[0, 1.12],
        tickvals=[0, 0.25, 0.5, 0.75, 1], tickformat=".0%",
        showgrid=True, gridcolor=PALETTE["line"], zeroline=False,
        tickfont=axis_font, title_font=axis_font,
    )
    fig.update_layout(
        height=430,
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
        showlegend=False,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig


def add_curve(fig: go.Figure, curve: pd.Series, color: str, width: int,
              name: str | None = None, dash: str = "solid") -> None:
    """Draw a survival curve. A named curve also appears in the legend."""
    fig.add_trace(go.Scatter(
        x=curve.index, y=curve, mode="lines", hoverinfo="skip",
        name=name, showlegend=name is not None,
        line={"color": color, "width": width, "shape": "hv", "dash": dash},
    ))


def add_area(fig: go.Figure, window: pd.Series, decimals: int) -> None:
    """Shade the area under a stretch of the curve and label it with its size in months."""
    fig.add_trace(go.Scatter(
        x=window.index, y=window, mode="lines", hoverinfo="skip", showlegend=False,
        line={"width": 0, "shape": "hv"}, fill="tozeroy", fillcolor=AREA_FILL,
    ))
    # A thin area only has room for a one-line label.
    height = window.iloc[len(window) // 2]
    months = f"<b>{area_under(window):.{decimals}f} months</b>"
    roomy = height >= 0.34
    fig.add_annotation(
        x=(window.index[0] + window.index[-1]) / 2, y=0.17 if roomy else max(height / 2, 0.05),
        showarrow=False,
        text=f"{months}<br>area under the curve" if roomy else months,
        font={"size": 19, "color": PALETTE["orange"]},
    )


def add_marker_line(fig: go.Figure, month: float, label: str, dash: str) -> None:
    fig.add_vline(x=month, line_color=PALETTE["ink"], line_width=2, line_dash=dash)
    fig.add_annotation(
        x=month, y=1.09, yref="paper", text=label, showarrow=False,
        font={"size": 15, "color": PALETTE["ink"]},
    )


def add_today(fig: go.Figure, window: pd.Series) -> None:
    """Mark today and the end of the horizon, and the share of subscribers still here today."""
    tenure, still_here = window.index[0], window.iloc[0]
    fig.add_shape(
        type="line", x0=-1.5, x1=tenure, y0=still_here, y1=still_here,
        line={"color": PALETTE["purple"], "width": 2, "dash": "dot"},
    )
    fig.add_trace(go.Scatter(
        x=[tenure], y=[still_here], mode="markers", hoverinfo="skip", showlegend=False,
        marker={"size": 15, "color": PALETTE["purple"], "line": {"color": "#FFFFFF", "width": 2}},
    ))
    fig.add_annotation(
        x=tenure, y=still_here, ax=95, ay=-26, arrowcolor=PALETTE["purple"], arrowwidth=2,
        text=f"<b>{still_here:.2%}</b> still here", bgcolor="#FFFFFF",
        font={"size": 17, "color": PALETTE["purple"]},
    )
    add_marker_line(fig, tenure, "<b>Today</b>", "solid")
    add_marker_line(fig, window.index[-1], f"+{HORIZON_YEARS} years", "dot")
