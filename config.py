# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(
    page_title="RSU Master Terminal",
    layout="wide",
    page_icon="📊"
)

def set_style():
    st.markdown("""
        <style>
        /* Estil base de l'aplicació */
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* Contenidor de l'Informe d'IA */
        .prompt-container {
            background-color: #1a1e26; border-left: 5px solid #2962ff;
            padding: 20px; border-radius: 5px; margin-top: 10px; white-space: pre-wrap;
        }

        /* Targetes de valoració estil Terminal (Pestanya Overview) */
        .overview-box {
            background-color: #151921;
            border: 1px solid #2d3439;
            border-radius: 8px;
            padding: 20px;
            margin-top: 10px;
        }
        .valuation-card {
            background-color: #1a1e26;
            border: 1px solid #2d3439;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
            height: 130px;
        }
        .val-label { color: #888; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .val-value { color: white; font-size: 22px; font-weight: bold; margin: 5px 0; }
        .val-sub-label { color: #555; font-size: 10px; margin-top: 2px; }
        .val-tag { 
            background-color: #242933; color: #a0a0a0; 
            font-size: 10px; padding: 2px 8px; border-radius: 4px; float: right;
            border: 1px solid #3d444b;
        }
        
        /* Pestanyes personalitzades */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #151921;
            border-radius: 4px 4px 0px 0px;
            padding: 10px 20px;
            color: #888;
        }
        .stTabs [aria-selected="true"] {
            background-color: #2962ff !important;
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)

API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

@st.cache_resource
def get_ia_model():
    try:
        if not API_KEY:
            return None, None, "API Key no trobada"
        genai.configure(api_key=API_KEY)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        return genai.GenerativeModel(model_name=sel, safety_settings=safety_settings), sel, None
    except Exception as e:
        return None, None, str(e)

@st.cache_data(ttl=600)
def obtener_prompt_github():
    try:
        url_raw = "https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/prompt_report.txt"
        r = requests.get(url_raw)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

@st.cache_data(ttl=3600)
def get_cnn_fear_greed():
    # Simulat segons el teu codi previ
    return 50



