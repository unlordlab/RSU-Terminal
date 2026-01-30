# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    # Título principal alineado
    st.markdown('<h1 style="margin-top:-60px; margin-bottom:25px;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Columna izquierda para índices, derecha para el widget suelto
    col_idx, col_widget = st.columns([1, 2.2])
    
    with col_idx:
        st.markdown("""
            <div class="group-container">
                <div class="group-header"><p class="group-title">Market Indices</p></div>
                <div class="group-content">
        """, unsafe_allow_html=True)
        
        indices = [
            {"label": "S&P 500", "full": "US 500 Index", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "Nasdaq Composite", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "Industrial Average", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "Small Cap Index", "t": "^RUT"}
        ]
        
        for idx in indices:
            p, c = get_market_index(idx['t'])
            color_class = "pos" if c >= 0 else "neg"
            st.markdown(f"""
                <div class="index-card">
                    <div>
                        <p class="index-ticker">{idx['label']}</p>
                        <p class="index-fullname">{idx['full']}</p>
                    </div>
                    <div style="text-align:right;">
                        <p class="index-price">{p:,.2f}</p>
                        <span class="index-delta {color_class}">{c:+.2f}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    with col_widget:
        # El widget de TradingView ahora está "suelto" pero configurado con altura para alinear
        spread_widget = """
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.MediumWidget({
          "symbols": [["FRED:BAMLH0A0HYM2|1D"]],
          "chartOnly": false,
          "width": "100%",
          "height": 400,
          "locale": "en",
          "colorTheme": "dark",
          "gridLineColor": "rgba(42, 46, 57, 0)",
          "trendLineColor": "#f23645",
          "underLineColor": "rgba(242, 54, 69, 0.1)",
          "container_id": "tv_spread"
        });
        </script>
        <div id="tv_spread" style="height:400px;"></div>
        """
        # Un pequeño margen superior en el componente para alinear con el header de la izquierda
        st.markdown('<p style="color: #888; font-size: 11px; font-weight: bold; text-transform: uppercase; margin-bottom: 8px;">Credit Spreads (OAS)</p>', unsafe_allow_html=True)
        components.html(spread_widget, height=410)

    st.write("---")
