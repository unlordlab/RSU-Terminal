# modules/ia_report.py
import streamlit as st
import yfinance as yf
from config import get_ia_model, obtener_prompt_github

def render():
    model_ia, modelo_nombre, error_ia = get_ia_model()

    # Selector de Ticker
    t_in = st.text_input("Introduir Ticker (ex: NVDA, AAPL)", "NVDA").upper()
    
    if not t_in:
        st.warning("Si us plau, introdueix un ticker.")
        return

    # Obtenir dades de yfinance
    ticker_data = yf.Ticker(t_in)
    info = ticker_data.info

    # --- SECCIÓ 1: ABOUT ---
    st.markdown(f"### About {t_in}")
    st.write(info.get('longBusinessSummary', 'No hi ha descripció disponible per a aquest ticker.'))

    # --- SECCIÓ 2: PESTANYES (Com a la imatge) ---
    tabs = st.tabs(["Overview", "Earnings", "Seasonality", "Insider", "Financials", "Options"])

    with tabs[0]: # PESTANYA OVERVIEW
        st.markdown('<div class="overview-box">', unsafe_allow_html=True)
        st.markdown('<h4>📊 Company Overview</h4>', unsafe_allow_html=True)
        st.caption("Valuation metrics and analyst consensus")
        
        st.markdown('<p style="color:#00ffad; font-size:13px; margin-top:10px; font-weight:bold;">💵 Valuation Multiples</p>', unsafe_allow_html=True)
        
        # Graella de mètriques
        col1, col2, col3 = st.columns(3)
        
        # Mètriques a mostrar
        metrics_list = [
            {"label": "P/E (Trailing)", "value": info.get('trailingPE'), "tag": "Trailing", "sub": "Price to Earnings"},
            {"label": "P/S (TTM)", "value": info.get('priceToSalesTrailing12Months'), "tag": "TTM", "sub": "Price to Sales"},
            {"label": "EV/EBITDA", "value": info.get('enterpriseToEbitda'), "tag": "TTM", "sub": "Enterprise / EBITDA"},
            {"label": "Forward P/E", "value": info.get('forwardPE'), "tag": "Next 12M", "sub": "Expected P/E"},
            {"label": "PEG Ratio", "value": info.get('pegRatio'), "tag": "Growth", "sub": "P/E to Growth"}
        ]

        for i, m in enumerate(metrics_list):
            target_col = [col1, col2, col3][i % 3]
            with target_col:
                val = f"{m['value']:.2f}x" if m['value'] and isinstance(m['value'], (int, float)) else "N/A"
                st.markdown(f"""
                    <div class="valuation-card">
                        <span class="val-tag">{m['tag']}</span>
                        <div class="val-label">{m['label']}</div>
                        <div class="val-value">{val}</div>
                        <div class="val-sub-label">Sector avg: --</div>
                        <div class="val-sub-label">{m['sub']}</div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[4]: # PESTANYA FINANCIALS
        st.markdown("### Financial Statements")
        st.dataframe(ticker_data.financials, use_container_width=True)

    # --- SECCIÓ 3: GENERADOR D'IA (Sota les pestanyes o on prefereixis) ---
    st.write("---")
    st.subheader("🤖 RSU AI Report Generator")
    if st.button("GENERAR INFORME COMPLET"):
        if error_ia:
            st.error(error_ia)
            return

        with st.spinner(f"L'IA està analitzant {t_in}..."):
            template = obtener_prompt_github()
            prompt_final = f"Analitza {t_in} seguint això: {template.replace('[TICKER]', t_in)}"
            try:
                res = model_ia.generate_content(prompt_final)
                text = getattr(res, "text", None)
                if text:
                    st.markdown(f"### 📋 Informe d'IA: {t_in}")
                    st.markdown(f'<div class="prompt-container">{text}</div>', unsafe_allow_html=True)
                else:
                    st.warning("L'IA no ha retornat text.")
            except Exception as e:
                st.error(f"Error: {e}")

    st.caption(f"Engine: {modelo_nombre}")
