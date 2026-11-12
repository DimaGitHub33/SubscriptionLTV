"""Survival curves and the expected subscription time derived from them."""

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter

HORIZON_MONTHS = 36


def kaplan_meier(subscribers: pd.DataFrame) -> pd.Series:
    """Share of subscribers still subscribed at each tenure, indexed by month."""
    fitter = KaplanMeierFitter().fit(subscribers["tenure_months"], subscribers["churned"])
    return fitter.survival_function_.iloc[:, 0].rename("survival")


def survival_at(curve: pd.Series, month: float) -> float:
    """Value of a step survival curve at a given month."""
    position = np.searchsorted(curve.index.to_numpy(), month, side="right") - 1
    return float(curve.iloc[position])


def rebased_curve(curve: pd.Series, tenure: float, horizon: float = HORIZON_MONTHS) -> pd.Series:
    """Survival over the next `horizon` months for a subscriber who has already reached `tenure`.

    The curve is cut at `tenure` and rescaled so that it starts at 100% there.
    """
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
    return pd.Series(window / window[0], index=months, name="survival")


def expected_months(curve: pd.Series) -> float:
    """Area under a step survival curve: the expected number of months subscribed."""
    return float(np.sum(np.diff(curve.index.to_numpy()) * curve.to_numpy()[:-1]))
