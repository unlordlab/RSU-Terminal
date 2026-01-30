# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from config import get_ia_model, obtener_prompt_github

def render():
    # 1. Input del Ticker
    t_in = st.text_input("Introduir Ticker", "NVDA").upper()
    
    if not t_in:
        st.warning("Escriu un ticker.")
        return

    # 2. GRÀFIC GRAN (670px)
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

    # 3. Dades de yfinance
    ticker_data = yf.Ticker(t_in)
    info = ticker_data.info

    # 4. About & Tabs
    st.markdown(f"### About {t_in}")
    st.write(info.get('longBusinessSummary', 'Sense descripció.'))

    tabs = st.tabs(["Overview", "Earnings", "Seasonality", "Insider", "Financials"])

    with tabs[0]: # Overview amb les targetes
        st.markdown('<div class="overview-box">', unsafe_allow_html=True)
        st.markdown('<p style="color:#00ffad; font-weight:bold;">💵 Valuation Multiples</p>', unsafe_allow_html=True)
        
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

    with tabs[4]: # Financials
        st.dataframe(ticker_data.financials, use_container_width=True)
