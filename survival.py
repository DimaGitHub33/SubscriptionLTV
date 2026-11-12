"""Survival curves and the expected subscription time derived from them."""

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter

HORIZON_MONTHS = 36


def kaplan_meier(subscribers: pd.DataFrame) -> pd.Series:
    """Share of subscribers still subscribed at each tenure, indexed by month."""
    fitter = KaplanMeierFitter().fit(subscribers["tenure_months"], subscribers["churned"])
    return fitter.survival_function_.iloc[:, 0].rename("survival")


def fit_cox(features: pd.DataFrame, subscribers: pd.DataFrame) -> CoxPHFitter:
    """Cox proportional hazards model of churn on the given numeric features."""
    frame = features.assign(tenure_months=subscribers["tenure_months"], churned=subscribers["churned"])
    return CoxPHFitter().fit(frame, duration_col="tenure_months", event_col="churned")


def cox_curve(model: CoxPHFitter, features: pd.DataFrame) -> pd.Series:
    """Survival curve the model predicts for the subscriber in the first row, indexed by month."""
    curve = model.predict_survival_function(features.iloc[[0]]).iloc[:, 0]
    if curve.index[0] > 0:
        curve = pd.concat([pd.Series([1.0], index=[0.0]), curve])
    return curve.rename("survival")


def relative_risk(model: CoxPHFitter, features: pd.DataFrame) -> float:
    """Churn risk of the subscriber in the first row, as a multiple of the average subscriber's."""
    return float(model.predict_partial_hazard(features.iloc[[0]]).iloc[0])


def survival_at(curve: pd.Series, month: float) -> float:
    """Value of a step survival curve at a given month."""
    position = np.searchsorted(curve.index.to_numpy(), month, side="right") - 1
    return float(curve.iloc[position]) if position >= 0 else 1.0


def curve_window(curve: pd.Series, tenure: float, horizon: float = HORIZON_MONTHS) -> pd.Series:
    """The part of the curve covering the next `horizon` months after `tenure`."""
    end = tenure + horizon
    if end > curve.index[-1]:
        raise ValueError(
            f"The curve is only observed up to month {curve.index[-1]:.1f}, "
            f"but tenure {tenure} plus a {horizon}-month horizon needs month {end}."
        )
    times, values = curve.index.to_numpy(), curve.to_numpy()
    inside = (times > tenure) & (times < end)
    months = np.concatenate(([tenure], times[inside], [end]))
    window = np.concatenate(([survival_at(curve, tenure)], values[inside], [survival_at(curve, end)]))
    return pd.Series(window, index=months, name="survival")


def rebased_curve(curve: pd.Series, tenure: float, horizon: float = HORIZON_MONTHS) -> pd.Series:
    """Survival over the next `horizon` months for a subscriber who has already reached `tenure`.

    The curve is cut at `tenure` and rescaled so that it starts at 100% there.
    """
    window = curve_window(curve, tenure, horizon)
    return window / window.iloc[0]


def area_under(curve: pd.Series) -> float:
    """Area under a step survival curve, in months."""
    return float(np.sum(np.diff(curve.index.to_numpy()) * curve.to_numpy()[:-1]))
