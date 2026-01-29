# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

st.set_page_config(
    page_title="RSU Master Terminal",
    layout="wide",
    page_icon="📊"
)

# Estilos globales
def set_style():
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        .metric-card {
            background-color: #151921; padding: 20px; border-radius: 10px;
            border: 1px solid #2d3439; text-align: center;
        }
        .prompt-container {
            background-color: #1a1e26; border-left: 5px solid #2962ff;
            padding: 20px; border-radius: 5px; margin-top: 10px; white-space: pre-wrap;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

@st.cache_resource
def get_ia_model():
    if not API_KEY:
        return None, None, "Falta API KEY en Secrets"
    try:
        genai.configure(api_key=API_KEY)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        modelos = [m.name for m in genai.list_models()
                   if 'generateContent' in m.supported_generation_methods]
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
    try:
        url = "https://edition.cnn.com/markets/fear-and-greed"
        headers = {'User-Agent': 'Mozilla/5.0'}
        soup = BeautifulSoup(requests.get(url, headers=headers).content, 'html.parser')
        val = soup.find("span", class_="market-fng-gauge__dial-number-value").text
        return int(val)
    except:
        return 50
