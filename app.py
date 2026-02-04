# app.py
import os
import sys
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math
from datetime import datetime
import pytz
import yfinance as yf

# Workaround: Agregar el directorio raiz al path para evitar problemas de import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar config con manejo de error
try:
    from config import set_style, get_cnn_fear_greed, actualizar_contador_usuarios
except ImportError as e:
    st.error(f"Error importing config: {e}")
    # Funciones fallback minimas
    def set_style():
        st.markdown("""
        <style>
        .stApp { background-color: #0a0c10; color: white; }
        </style>
        """, unsafe_allow_html=True)
    def get_cnn_fear_greed():
        return None
    def actualizar_contador_usuarios():
        return 1

# Importar modulos con manejo
