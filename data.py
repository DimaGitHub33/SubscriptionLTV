"""Synthetic subscriber data with known churn drivers."""

import numpy as np
import pandas as pd

# How long the service has been running, in months. No tenure can exceed it.
OBSERVATION_MONTHS = 84

PLANS = {"Basic": 10, "Standard": 15, "Premium": 20}

# Weibull baseline with shape below 1: churn risk is highest early and falls with tenure.
BASELINE_SHAPE = 0.7
BASELINE_SCALE = 30.0

# True log hazard ratios behind the churn times, kept so fitted models can be checked against them.
TRUE_EFFECTS = {
    "plan": {"Basic": 0.0, "Standard": -0.25, "Premium": -0.5},
    "channel": {"Organic": 0.0, "Paid ads": 0.35, "Referral": -0.3},
    "promo_signup": 0.4,
    "weekly_hours": -0.08,
}
CHANNELS = list(TRUE_EFFECTS["channel"])


def model_features(subscribers: pd.DataFrame) -> pd.DataFrame:
    """Numeric model inputs: an indicator for every plan and channel except the first, plus promo and usage.

    The first plan and the first channel are the reference that the others are compared with.
    """
    columns = {}
    for feature in ("plan", "channel"):
        for level in list(TRUE_EFFECTS[feature])[1:]:
            columns[f"{feature}={level}"] = (subscribers[feature] == level).astype(float)
    columns["promo_signup"] = subscribers["promo_signup"].astype(float)
    columns["weekly_hours"] = subscribers["weekly_hours"].astype(float)
    return pd.DataFrame(columns, index=subscribers.index)


def true_log_hazard_ratios() -> pd.Series:
    """The true effect behind each column of `model_features`."""
    effects = {}
    for feature in ("plan", "channel"):
        for level, effect in list(TRUE_EFFECTS[feature].items())[1:]:
            effects[f"{feature}={level}"] = effect
    effects["promo_signup"] = TRUE_EFFECTS["promo_signup"]
    effects["weekly_hours"] = TRUE_EFFECTS["weekly_hours"]
    return pd.Series(effects)


def generate_subscribers(n: int = 5000, seed: int = 7) -> pd.DataFrame:
    """One row per subscriber: features, tenure in months, and whether they cancelled."""
    rng = np.random.default_rng(seed)

    plan = rng.choice(list(PLANS), size=n, p=[0.45, 0.35, 0.20])
    channel = rng.choice(CHANNELS, size=n, p=[0.5, 0.3, 0.2])
    promo_signup = rng.random(n) < 0.3
    weekly_hours = rng.gamma(shape=2.0, scale=2.5, size=n).round(1)

    log_hazard = (
        pd.Series(plan).map(TRUE_EFFECTS["plan"]).to_numpy()
        + pd.Series(channel).map(TRUE_EFFECTS["channel"]).to_numpy()
        + TRUE_EFFECTS["promo_signup"] * promo_signup
        + TRUE_EFFECTS["weekly_hours"] * weekly_hours
    )
    lifetime = BASELINE_SCALE * (rng.exponential(size=n) / np.exp(log_hazard)) ** (1 / BASELINE_SHAPE)

    # Subscribers joined at different times, so each has been observed for a different length.
    months_since_joining = rng.uniform(0, OBSERVATION_MONTHS, size=n)
    churned = lifetime <= months_since_joining

    return pd.DataFrame({
        "customer_id": np.arange(1, n + 1),
        "plan": plan,
        "monthly_price": pd.Series(plan).map(PLANS).to_numpy(),
        "channel": channel,
        "promo_signup": promo_signup,
        "weekly_hours": weekly_hours,
        "tenure_months": np.minimum(lifetime, months_since_joining),
        "churned": churned.astype(int),
    })
