# modules/cartera.py
import streamlit as st
import pandas as pd

def render():
    st.subheader("Cartera RSU")
    try:
        df = pd.read_csv(st.secrets["URL_CARTERA"])
        st.table(df)
    except Exception:
        st.warning("Configura URL_CARTERA.")
