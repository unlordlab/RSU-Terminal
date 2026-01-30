import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from config import get_ia_model, obtener_prompt_github

def render():
    # 1. Selector de Ticker (Part superior)
    col_input, _ = st.columns([1, 2])
    with col_input:
        t_in = st.text_input("Introduir Ticker", "NVDA").upper()
    
    if not t_in:
        st.warning("Si us plau, introdueix un ticker.")
        return

    # 2. GRÀFIC TRADINGVIEW (670px)
    tradingview_widget = f"""
    <div style="height:670px;">
      <div id="tradingview_chart" style="height:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{t_in}",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "hide_side_toolbar": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(tradingview_widget, height=670)

    # Obtenir dades de yfinance
    ticker_data = yf.Ticker(t_in)
    info = ticker_data.info

    # 3. SECCIÓ ABOUT
    st.markdown(f"### About {info.get('longName', t_in)}")
    st.write(info.get('longBusinessSummary', 'Descripció no disponible.'))

    # 4. PESTANYES D'ANÀLISI (Overview a la primera)
    tabs = st.tabs(["Overview", "Earnings", "Seasonality", "Insider", "Financials"])

    with tabs[0]:
        st.markdown('<div class="overview-box">', unsafe_allow_html=True)
        st.markdown('<p style="color:#00ffad; font-weight:bold; font-size:14px;">💵 Valuation Multiples</p>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        metrics = [
            {"label": "P/E (Trailing)", "val": info.get('trailingPE'), "tag": "Trailing"},
            {"label": "P/S (TTM)", "val": info.get('priceToSalesTrailing12Months'), "tag": "TTM"},
            {"label": "EV/EBITDA", "val": info.get('enterpriseToEbitda'), "tag": "TTM"},
            {"label": "Forward P/E", "val": info.get('forwardPE'), "tag": "Next 12M"},
            {"label": "PEG Ratio", "val": info.get('pegRatio'), "tag": "Growth"}
        ]

        for i, m in enumerate(metrics):
            target_col = [c1, c2, c3][i % 3]
            with target_col:
                v = f"{m['val']:.2f}x" if isinstance(m['val'], (int, float)) else "N/A"
                st.markdown(f"""
                    <div class="valuation-card">
                        <span class="val-tag">{m['tag']}</span>
                        <div class="val-label">{m['label']}</div>
                        <div class="val-value">{v}</div>
                        <div class="val-sub-label">Sector avg: --</div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[4]:
        st.subheader("Financial Statements")
        st.dataframe(ticker_data.financials, use_container_width=True)

    # 5. BOTÓ GENERAR PROMPT RSU (Al final de tot)
    st.write("---")
    st.subheader("🤖 RSU Artificial Intelligence")
    st.info("Prem el botó per generar un informe complet basat en el prompt personalitzat de RSU.")
    
    if st.button("🪄 GENERAR INFORME IA (RSU)", use_container_width=True):
        model_ia, modelo_nombre, error_ia = get_ia_model()
        if error_ia:
            st.error(f"Error: {error_ia}")
        else:
            with st.spinner(f"L'IA està redactant l'informe per a {t_in}..."):
                template = obtener_prompt_github()
                prompt_final = f"Analitza {t_in} seguint això: {template.replace('[TICKER]', t_in)}"
                try:
                    res = model_ia.generate_content(prompt_final)
                    st.markdown(f"### 📋 Informe RSU: {t_in}")
                    st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)
                    st.caption(f"Generat amb: {modelo_nombre}")
                except Exception as e:
                    st.error(f"Error en l'IA: {e}")
