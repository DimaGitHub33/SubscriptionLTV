"""Cached data and fitted models shared by the app pages."""

import pandas as pd
import streamlit as st
from lifelines import CoxPHFitter

from data import generate_subscribers, model_features
from survival import fit_cox, kaplan_meier


@st.cache_data
def subscribers() -> pd.DataFrame:
    return generate_subscribers()


@st.cache_data
def kaplan_meier_curve() -> pd.Series:
    return kaplan_meier(subscribers())


@st.cache_resource
def cox_model() -> CoxPHFitter:
    data = subscribers()
    return fit_cox(model_features(data), data)
