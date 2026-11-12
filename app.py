"""SubscriptionLTV: entry point of the Streamlit app.

Run with:  streamlit run app.py
"""

import streamlit as st

from ui import apply_theme

st.set_page_config(page_title="SubscriptionLTV", page_icon="📈", layout="wide")
apply_theme()

pages = [
    st.Page("app_pages/problem.py", title="The problem", icon="🎯", default=True),
    st.Page("app_pages/kaplan_meier.py", title="Kaplan–Meier", icon="📉"),
    st.Page("app_pages/conditional_expectation.py", title="Step by step", icon="🧮"),
    st.Page("app_pages/cox.py", title="Cox model", icon="👤"),
]

st.navigation(pages, position="top").run()
