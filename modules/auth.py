# modules/auth.py
import os
import streamlit as st

def login():
    if "auth" not in st.session_state:
        st.session_state["auth"] = False

    if st.session_state["auth"]:
        return True

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", use_container_width=True)
        st.markdown("<h4 style='text-align:center;'>RSU TERMINAL ACCESS</h4>", unsafe_allow_html=True)
        password = st.text_input("PASSWORD", type="password")
        if st.button("UNLOCK", use_container_width=True):
            real_pwd = st.secrets.get("APP_PASSWORD", "RSU2026")
            if password == real_pwd:
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Clave Incorrecta")

    return False
