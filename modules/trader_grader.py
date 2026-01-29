# modules/trade_grader.py
import streamlit as st

def render():
    st.subheader("RSU Scorecard")
    ten = st.selectbox("Tendencia", ["A favor", "Neutral", "En contra"])
    rrr = st.slider("RRR", 1.0, 5.0, 2.0)

    if st.button("CALCULAR"):
        st.success(f"Grado calculado para tendencia {ten} (RRR: {rrr})")
