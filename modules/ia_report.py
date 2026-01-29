# modules/ia_report.py
import streamlit as st
from config import get_ia_model, obtener_prompt_github

def render():
    model_ia, modelo_nombre, error_ia = get_ia_model()

    t_in = st.text_input("Ticker", "NVDA").upper()
    if st.button("GENERAR PROMPT RSU"):
        if error_ia:
            st.error(error_ia)
            return

        with st.spinner(f"Analizando {t_in}..."):
            template = obtener_prompt_github()
            prompt_final = f"Analitza {t_in} seguint això: {template.replace('[TICKER]', t_in)}"
            try:
                res = model_ia.generate_content(prompt_final)
                text = getattr(res, "text", None)
                if text:
                    st.markdown(f"### 📋 Informe: {t_in}")
                    st.markdown(f'<div class="prompt-container">{text}</div>', unsafe_allow_html=True)
                else:
                    st.warning("No se ha podido obtener texto del modelo.")
            except Exception as e:
                st.error(f"Error de IA: {e}")

    # Pie de página del motor
    _, modelo_nombre, _ = get_ia_model()
    st.caption(f"Engine: {modelo_nombre}")

