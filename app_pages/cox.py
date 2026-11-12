"""Page 4: predicted lifetime value of JFrog customers with a Cox model, in four steps.

Public facts about JFrog are cited in SOURCES. The companies, prices and forecasts are an illustration.
"""

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from lifelines import CoxPHFitter

from charts import CHART_CONFIG
from jfrog import ANNUAL_PRICE, ASSUMED_RISK_MULTIPLIERS, generate_companies, model_features
from survival import HORIZON_MONTHS, area_under, cox_curve, curve_window, fit_cox, relative_risk
from ui import PALETTE, callout, dollars, round_half_up, section

HORIZON_YEARS = HORIZON_MONTHS // 12

SOURCES = [
    ("JFrog, home page", "https://jfrog.com", "who uses the platform"),
    ("JFrog, pricing page", "https://jfrog.com/pricing/", "plans, list prices, products and usage-based pricing"),
    (
        "JFrog, third quarter 2026 results, 5 November 2026",
        "https://investors.jfrog.com/news/news-details/2026/"
        "JFrog-Announces-Third-Quarter-2026-Results/default.aspx",
        "the products customers adopt",
    ),
    (
        "JFrog, third quarter 2026 earnings call transcript",
        "https://s21.q4cdn.com/528621000/files/content_files/"
        "JFrog-Third-Quarter-2026-Financial-Results-Conference-Call_Transcript_Corrected.pdf",
        "gross retention",
    ),
    (
        "JFrog, Form 10-Q for the third quarter of 2026",
        "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001800667/d24cc365-8c8a-4964-b0b4-340de1e9da48.pdf",
        "cloud and self-managed subscriptions, usage-based fees",
    ),
    (
        "lifelines documentation, Survival regression",
        "https://lifelines.readthedocs.io/en/latest/Survival%20Regression.html",
        "the Cox model",
    ),
]

# The example companies of step 4. All of them are made up.
EXAMPLES = [
    {"name": "Company A", "kind": "Small team", "color": "orange",
     "plan": "Pro", "cloud": True, "large_company": False, "products": 1, "usage_falling": True},
    {"name": "Company B", "kind": "Growing scale-up", "color": "blue",
     "plan": "Enterprise X", "cloud": True, "large_company": False, "products": 2, "usage_falling": False},
    {"name": "Company C", "kind": "Large enterprise", "color": "green",
     "plan": "Enterprise+", "cloud": False, "large_company": True, "products": 3, "usage_falling": False},
    {"name": "Company D", "kind": "Enterprise at risk", "color": "purple",
     "plan": "Enterprise+", "cloud": True, "large_company": True, "products": 1, "usage_falling": True},
]

# Smallest vertical distance between two curve labels, as a share of customers.
LABEL_GAP = 0.075

PAGE_CSS = """
.disclaimer {
    margin-top: 1.2rem;
    padding: 12px 20px;
    border-radius: 16px;
    border: 1px solid #FED7AA;
    background: #FFF7ED;
    color: #9A3412;
    font-size: 1.02rem;
}
.fact {
    display: flex;
    align-items: center;
    gap: 32px;
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-left: 8px solid var(--purple);
    border-radius: 20px;
    padding: 28px 32px;
    box-shadow: 0 10px 28px -18px rgba(15, 23, 42, 0.25);
}
.fact .figure { font-size: 4.2rem; font-weight: 800; line-height: 1; color: var(--purple); }
.fact .label { font-size: 1.05rem; font-weight: 700; color: var(--ink); margin-top: 0.4rem; white-space: nowrap; }
.fact .so { font-size: 1.2rem; line-height: 1.5; color: var(--muted); }
.fact .so b { color: var(--ink); }
sup.ref { font-size: 0.7rem; font-weight: 700; color: var(--purple); }
.example-label {
    margin: 1.4rem 0 0.6rem;
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
}
.traits { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 1.05rem; }
.traits th {
    padding: 12px 16px;
    text-align: left;
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.traits th.known { color: var(--green); }
.traits th.assumed { color: var(--orange); }
.traits td { padding: 14px 16px; vertical-align: middle; color: var(--ink); border-top: 1px solid var(--line); }
.traits td.trait { font-weight: 750; white-space: nowrap; }
.traits td.assumed { background: #FFF7ED; }
.badge {
    display: inline-block;
    margin-left: 6px;
    padding: 2px 10px;
    border-radius: 999px;
    background: var(--accent);
    color: #FFFFFF;
    font-size: 0.9rem;
    font-weight: 800;
    white-space: nowrap;
}
.companies { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.company {
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-top: 7px solid var(--accent);
    border-radius: 18px;
    padding: 20px 22px;
    box-shadow: 0 10px 28px -18px rgba(15, 23, 42, 0.25);
}
.company .head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.company .name { font-size: 1.25rem; font-weight: 800; color: var(--accent); }
.company .kind { font-size: 1rem; color: var(--muted); }
.company .risk { font-size: 0.95rem; font-weight: 700; color: var(--ink); white-space: nowrap; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 0.8rem 0 1rem; }
.chips span {
    padding: 3px 11px;
    border-radius: 999px;
    background: #F1F5F9;
    color: var(--ink);
    font-size: 0.88rem;
}
.figures { display: flex; align-items: stretch; gap: 8px; }
.figures .box { flex: 1; text-align: center; padding: 10px 6px; border-radius: 12px; background: #F8FAFC; }
.figures .box.ltv { background: var(--accent); }
.figures .box.ltv * { color: #FFFFFF; }
.figures .tag { font-size: 0.72rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); }
.figures .value { font-size: 1.45rem; font-weight: 800; color: var(--ink); line-height: 1.3; }
.figures .op { align-self: center; font-size: 1.3rem; color: var(--faint); }
.sources { font-size: 0.92rem; color: var(--muted); padding-left: 1.3rem; margin: 0; }
.sources li { margin-bottom: 0.25rem; }
.sources a { color: var(--purple); }
.small-print { font-size: 0.92rem; color: var(--muted); }
@media (max-width: 760px) {
    .fact { flex-direction: column; align-items: flex-start; gap: 14px; }
    .companies { grid-template-columns: 1fr; }
}
"""


@dataclass
class Forecast:
    """What the model predicts for one example company."""

    risk: float
    curve: pd.Series
    monthly_price: int
    months: float
    lifetime_value: int


@st.cache_resource
def load_model() -> tuple[CoxPHFitter, int]:
    """Cox model fitted on the simulated companies, and how many there are."""
    companies = generate_companies()
    return fit_cox(model_features(companies), companies), len(companies)


def ref(*numbers: int) -> str:
    """Superscript pointers to entries of SOURCES."""
    return "".join(f'<sup class="ref">{number}</sup> ' for number in numbers).strip()


def multiplier(feature: str, label: str = "") -> str:
    """Badge with the assumed effect of a trait on the risk of leaving."""
    value = ASSUMED_RISK_MULTIPLIERS[feature]
    color = PALETTE["green"] if value < 1 else PALETTE["red"]
    return f'<span class="badge" style="--accent: {color}">{f"{label} ×{value:g}".strip()}</span>'


def forecast(model: CoxPHFitter, company: dict) -> Forecast:
    """Run one company through the pipeline: traits, Cox curve, expected months, lifetime value."""
    features = model_features(pd.DataFrame([company]))
    curve = curve_window(cox_curve(model, features), 0)
    monthly_price = ANNUAL_PRICE[company["plan"]] // 12
    # The value is computed from the rounded months, so the cards multiply out exactly as shown.
    months = round(area_under(curve), 1)
    return Forecast(
        risk=relative_risk(model, features), curve=curve, monthly_price=monthly_price,
        months=months, lifetime_value=round_half_up(monthly_price * months),
    )


def traits(company: dict) -> list[str]:
    """Short labels for a company's traits."""
    return [
        company["plan"],
        "Cloud" if company["cloud"] else "Self-managed",
        "Large company" if company["large_company"] else "Smaller company",
        "Artifactory only" if company["products"] == 1 else f"{company['products']} products",
        "Usage falling" if company["usage_falling"] else "Usage steady",
    ]


def curves_chart(forecasts: list[Forecast]) -> go.Figure:
    """The survival curve the model gives each example company, labelled with its expected months."""
    axis_font = {"size": 15, "color": PALETTE["muted"]}
    fig = go.Figure()
    for company, result in zip(EXAMPLES, forecasts):
        fig.add_trace(go.Scatter(
            x=result.curve.index, y=result.curve, mode="lines", hoverinfo="skip",
            line={"color": PALETTE[company["color"]], "width": 4, "shape": "hv"},
        ))
    # Each curve is labelled at its right end. Labels of curves that end close together are nudged apart.
    label_height = None
    for company, result in sorted(zip(EXAMPLES, forecasts), key=lambda pair: -pair[1].curve.iloc[-1]):
        end = result.curve.iloc[-1]
        label_height = end if label_height is None else min(end, label_height - LABEL_GAP)
        fig.add_annotation(
            x=1, xref="paper", xanchor="left", xshift=10, y=label_height, showarrow=False,
            text=f"<b>{company['name']}</b> · {result.months:.1f} months",
            font={"size": 15, "color": PALETTE[company["color"]]},
        )
    fig.update_xaxes(
        title_text="Months since subscribing", range=[0, HORIZON_MONTHS],
        tickvals=list(range(0, HORIZON_MONTHS + 1, 6)),
        showgrid=True, gridcolor=PALETTE["line"], zeroline=False, tickfont=axis_font, title_font=axis_font,
    )
    fig.update_yaxes(
        title_text="Still a customer", range=[0, 1.05], tickvals=[0, 0.25, 0.5, 0.75, 1], tickformat=".0%",
        showgrid=True, gridcolor=PALETTE["line"], zeroline=False, tickfont=axis_font, title_font=axis_font,
    )
    fig.update_layout(
        height=380,
        margin={"l": 10, "r": 200, "t": 20, "b": 10},
        showlegend=False,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig


def company_card(company: dict, result: Forecast) -> str:
    chips = "".join(f"<span>{trait}</span>" for trait in traits(company))
    return f"""
    <div class="company" style="--accent: {PALETTE[company['color']]}">
        <div class="head">
            <div><span class="name">{company['name']}</span> <span class="kind">· {company['kind']}</span></div>
            <div class="risk">Risk of leaving ×{result.risk:.2f}</div>
        </div>
        <div class="chips">{chips}</div>
        <div class="figures">
            <div class="box">
                <div class="tag">Monthly<br>price</div>
                <div class="value">{dollars(result.monthly_price)}</div>
            </div>
            <div class="op">×</div>
            <div class="box">
                <div class="tag">Expected<br>months</div>
                <div class="value">{result.months:.1f}</div>
            </div>
            <div class="op">=</div>
            <div class="box ltv">
                <div class="tag">Predicted<br>LTV</div>
                <div class="value">{dollars(result.lifetime_value)}</div>
            </div>
        </div>
    </div>
    """


model, company_count = load_model()
forecasts = [forecast(model, company) for company in EXAMPLES]

st.html(f"<style>{PAGE_CSS}</style>")
st.html(
    """
    <div class="hero">
        <div class="eyebrow">Applied to JFrog</div>
        <h1>What is a JFrog customer worth?</h1>
        <p>Four steps, from what we know about a company to its predicted lifetime value.</p>
    </div>
    <div class="disclaimer">
        <b>An illustration.</b> Facts about JFrog are cited at the bottom.
        The companies, prices and forecasts on this page are made up.
    </div>
    """
)

section("1 · Why a survival model?")
st.html(
    f"""
    <div class="fact">
        <div>
            <div class="figure">97%</div>
            <div class="label">Gross retention{ref(4)}</div>
        </div>
        <div class="so"><b>Customers rarely leave.</b> Most are still active, so how long they will stay
        is not known yet. Survival analysis is built for exactly that.</div>
    </div>
    """
)

section(
    "2 · A simple LTV formula",
    "Each company pays a fixed annual price. The survival model estimates how many months it will stay.",
)
st.html(
    f"""
    <div class="equation">
        <div class="term" style="--accent: {PALETTE['blue']}">
            <span class="tag">Known</span>
            <div class="icon">💳</div>
            <div class="name">Monthly price</div>
            <div class="hint">annual price ÷ 12</div>
        </div>
        <div class="operator">×</div>
        <div class="term" style="--accent: {PALETTE['orange']}">
            <span class="tag">From the survival model</span>
            <div class="icon">⏳</div>
            <div class="name">Expected months</div>
            <div class="hint">as a customer, over the next {HORIZON_YEARS} years</div>
        </div>
        <div class="operator">=</div>
        <div class="term" style="--accent: {PALETTE['green']}">
            <span class="tag">The answer</span>
            <div class="icon">💰</div>
            <div class="name">Predicted LTV</div>
            <div class="hint">what the company is worth</div>
        </div>
    </div>
    <div class="example-label">For example</div>
    <div class="equation compact">
        <div class="term soft">
            <span class="tag">Monthly price</span>
            <div class="value">$1,000</div>
            <div class="hint">$12,000 a year ÷ 12</div>
        </div>
        <div class="operator">×</div>
        <div class="term soft">
            <span class="tag">Expected months</span>
            <div class="value">30</div>
            <div class="hint">out of the next 36</div>
        </div>
        <div class="operator">=</div>
        <div class="term" style="--accent: {PALETTE['green']}">
            <span class="tag">Predicted LTV</span>
            <div class="value">$30,000</div>
            <div class="hint">$1,000 × 30</div>
        </div>
    </div>
    """
)
st.html('<div class="note">Illustrative numbers. The price is assumed to stay the same for as long as the company subscribes.</div>')

section(
    "3 · What goes into the model?",
    "Five things we would know about each company. The model uses them to tell apart companies likely to stay from companies likely to leave.",
)
with st.container(border=True):
    st.html(
        f"""
        <table class="traits">
            <thead>
                <tr>
                    <th>Company trait</th>
                    <th class="known">✔ Public information about JFrog</th>
                    <th class="assumed">✎ My assumption for the demo</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="trait">📦 Subscription plan</td>
                    <td>Plans such as Pro, Enterprise X and Enterprise+.{ref(2)}</td>
                    <td class="assumed">Companies on higher plans stay longer.
                        {multiplier("plan=Enterprise X", "Enterprise X")} {multiplier("plan=Enterprise+", "Enterprise+")}</td>
                </tr>
                <tr>
                    <td class="trait">🌐 Where it runs</td>
                    <td>In JFrog's cloud, or hosted by the customer.{ref(5)}</td>
                    <td class="assumed">Cloud customers leave a little more easily. {multiplier("cloud")}</td>
                </tr>
                <tr>
                    <td class="trait">🏢 Company size</td>
                    <td>Customers include over 80% of the Fortune 100, and the Pro plan lists at $150 a month.{ref(1, 2)}</td>
                    <td class="assumed">Large companies stay longer. {multiplier("large_company")}</td>
                </tr>
                <tr>
                    <td class="trait">🧩 Products in use</td>
                    <td>Security and other products are added on top of Artifactory.{ref(2, 3)}</td>
                    <td class="assumed">Each extra product lowers the risk. {multiplier("extra_products")}</td>
                </tr>
                <tr>
                    <td class="trait">📉 Usage trend</td>
                    <td>Cloud subscriptions can include usage-based fees.{ref(2, 5)}</td>
                    <td class="assumed">Falling usage is a warning sign. {multiplier("usage_falling")}</td>
                </tr>
            </tbody>
        </table>
        """
    )
st.html(
    '<div class="note">The badge is the assumed effect on the risk of leaving: below ×1 the company stays longer, '
    "above ×1 it leaves sooner. Country and industry would be natural additions with real data.</div>"
)

section("4 · A forecast for every company")
st.html(
    f"""
    <div class="equation compact">
        <div class="term" style="--accent: {PALETTE['blue']}">
            <div class="icon">🏢</div>
            <div class="name">Company traits</div>
            <div class="hint">the five from step 3</div>
        </div>
        <div class="operator">→</div>
        <div class="term" style="--accent: {PALETTE['purple']}">
            <div class="icon">🧠</div>
            <div class="name">Cox model</div>
            <div class="hint">its risk of leaving</div>
        </div>
        <div class="operator">→</div>
        <div class="term" style="--accent: {PALETTE['orange']}">
            <div class="icon">⏳</div>
            <div class="name">Expected months</div>
            <div class="hint">over the next {HORIZON_YEARS} years</div>
        </div>
        <div class="operator">→</div>
        <div class="term" style="--accent: {PALETTE['green']}">
            <div class="icon">💰</div>
            <div class="name">Predicted LTV</div>
            <div class="hint">months × monthly price</div>
        </div>
    </div>
    <div class="disclaimer" style="margin: 1.2rem 0 0.8rem">
        <b>Illustration only.</b> Four made-up companies that have just subscribed.
        Their prices and forecasts are invented.
    </div>
    """
)
with st.container(border=True):
    st.plotly_chart(curves_chart(forecasts), width="stretch", config=CHART_CONFIG)
st.html(
    '<div class="note" style="margin-bottom: 1rem">The higher a company\'s curve, the more months it is expected to stay. '
    "On the cards, the risk of leaving is compared with the average company.</div>"
)
st.html(
    '<div class="companies">'
    + "".join(company_card(company, result) for company, result in zip(EXAMPLES, forecasts))
    + "</div>"
)

callout(
    "🐸",
    "The takeaway",
    "Two companies can pay the same price and still be worth different amounts. The Cox model tells them apart.",
)

section("Sources and assumptions")
sources = "".join(
    f'<li><a href="{url}" target="_blank">{title}</a>: {covers}.</li>' for title, url, covers in SOURCES
)
st.html(
    f"""
    <ol class="sources">{sources}</ol>
    <p class="small-print">
        <b>Assumptions.</b> The model is fitted on {company_count:,} simulated companies, built from the
        assumptions in step 3 and tuned so that about 97% of revenue is kept from one year to the next,
        as JFrog reports. Prices are a fixed $2,400, $12,000 or $120,000 a year by plan and are not
        JFrog's prices. Every example company is a new customer, and months beyond its first
        {HORIZON_YEARS} years are not counted.
    </p>
    """
)
