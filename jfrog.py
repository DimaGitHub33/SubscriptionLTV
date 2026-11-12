"""Simulated customer companies of a JFrog-like software vendor.

Nothing here is JFrog data. Which company traits matter, how strongly, and what companies pay
are assumptions, chosen only to demonstrate the method on a customer base shaped like the one
JFrog describes in public: fixed-term subscriptions and low revenue churn.
"""

import numpy as np
import pandas as pd

# How far back the simulated customer base goes, in months.
OBSERVATION_MONTHS = 96

PLANS = ["Pro", "Enterprise X", "Enterprise+"]
MAX_PRODUCTS = 4

# Illustrative annual subscription price of each plan, in dollars. Not JFrog's prices.
ANNUAL_PRICE = {"Pro": 2_400, "Enterprise X": 12_000, "Enterprise+": 120_000}

# Assumed effect of each trait on the risk of leaving, as a multiplier. Below 1 means staying longer.
ASSUMED_RISK_MULTIPLIERS = {
    "plan=Enterprise X": 0.75,
    "plan=Enterprise+": 0.55,
    "cloud": 1.20,
    "large_company": 0.65,
    "extra_products": 0.75,
    "usage_falling": 2.00,
}

# Weibull baseline with shape below 1: the risk of leaving is highest early and falls with tenure.
# The scale is tuned so that active customers keep about 97% of their revenue over the next year,
# the gross retention JFrog reported for the third quarter of 2026.
BASELINE_SHAPE = 0.8
BASELINE_SCALE = 150.0


def model_features(companies: pd.DataFrame) -> pd.DataFrame:
    """Numeric model inputs, one column per assumed multiplier. Pro and self-managed are the references."""
    return pd.DataFrame({
        "plan=Enterprise X": (companies["plan"] == "Enterprise X").astype(float),
        "plan=Enterprise+": (companies["plan"] == "Enterprise+").astype(float),
        "cloud": companies["cloud"].astype(float),
        "large_company": companies["large_company"].astype(float),
        "extra_products": companies["products"].astype(float) - 1,
        "usage_falling": companies["usage_falling"].astype(float),
    }, index=companies.index)


def log_hazard(companies: pd.DataFrame) -> np.ndarray:
    """Each company's assumed log risk multiplier."""
    effects = np.log(pd.Series(ASSUMED_RISK_MULTIPLIERS))
    return model_features(companies).mul(effects).sum(axis=1).to_numpy()


def generate_companies(n: int = 8000, seed: int = 11) -> pd.DataFrame:
    """One row per customer company: traits, tenure in months, and whether it left."""
    rng = np.random.default_rng(seed)

    # Large companies tend to buy higher plans, host the platform themselves and use more products.
    large_company = rng.random(n) < 0.30
    plan_odds = np.array([[0.60, 0.30, 0.10], [0.10, 0.35, 0.55]])
    plan = np.array([rng.choice(PLANS, p=plan_odds[int(large)]) for large in large_company])
    cloud = rng.random(n) < np.where(large_company, 0.40, 0.65)
    extra_product_rate = pd.Series(plan).map({"Pro": 0.08, "Enterprise X": 0.30, "Enterprise+": 0.55})
    products = 1 + rng.binomial(MAX_PRODUCTS - 1, extra_product_rate.to_numpy())
    usage_falling = rng.random(n) < 0.15

    companies = pd.DataFrame({
        "company_id": np.arange(1, n + 1),
        "plan": plan,
        "cloud": cloud,
        "large_company": large_company,
        "products": products,
        "usage_falling": usage_falling,
    })
    lifetime = BASELINE_SCALE * (
        rng.exponential(size=n) / np.exp(log_hazard(companies))
    ) ** (1 / BASELINE_SHAPE)

    # Companies joined at different times, so each has been observed for a different length.
    months_since_joining = rng.uniform(0, OBSERVATION_MONTHS, size=n)
    companies["tenure_months"] = np.minimum(lifetime, months_since_joining)
    companies["churned"] = (lifetime <= months_since_joining).astype(int)
    return companies
