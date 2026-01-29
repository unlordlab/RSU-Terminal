# modules/tesis.py
import streamlit as st
import pandas as pd

def render():
    st.subheader("Tesis de Inversión")
    try:
        df = pd.read_csv(st.secrets["URL_TESIS"])
        sel = st.selectbox("Tesis:", df['Ticker'].tolist())
        st.info(df[df['Ticker'] == sel]['Tesis_Corta'].values[0])
    except Exception:
        st.info("Configura URL_TESIS.")
