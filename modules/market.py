# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    st.markdown('<h1 style="margin-top:-60px; margin-bottom:20px;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Columnas 1:1 para asegurar misma anchura
    col_left, col_right = st.columns([1, 1])
    
    # ALTURA TOTAL FIJA (debe coincidir con el CSS)
    BOX_HEIGHT = 480

    # --- CAJA IZQUIERDA: INDICES ---
    with col_left:
        indices = [
            {"label": "S&P 500", "full": "US 500 Index", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "Nasdaq Composite", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "Industrial Average", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "Small Cap Index", "t": "^RUT"}
        ]
        
        cards_html = ""
        for idx in indices:
            p, c = get_market_index(idx['t'])
            color_class = "pos" if c >= 0 else "neg"
            price = f"{p:,.2f}" if p > 0 else "Cargando..."
            
            cards_html += f"""
            <div class="index-card">
                <div>
                    <p style="color:white; font-weight:bold; margin:0; font-size:14px;">{idx['label']}</p>
                    <p style="color:#555; font-size:10px; margin:0;">{idx['full']}</p>
                </div>
                <div style="text-align:right;">
                    <p style="font-weight:bold; color:white; margin:0; font-size:16px;">{price}</p>
                    <span class="index-delta {color_class}" style="font-size:11px; padding:2px 6px; border-radius:4px;">{c:+.2f}%</span>
                </div>
            </div>"""

        st.markdown(f"""
            <div class="group-container">
                <div class="group-header"><p class="group-title">Market Indices</p></div>
                <div class="group-content">{cards_html}</div>
            </div>
        """, unsafe_allow_html=True)

    # --- CAJA DERECHA: WIDGET INTEGRADO ---
    with col_right:
        # Definimos el HTML del widget con el contenedor oscuro incluido para evitar saltos
        # Ajustamos a temporalidad diaria ("1D") y quitamos bordes internos
        widget_html = f"""
        <div style="background-color: #11141a; border: 1px solid #2d3439; border-radius: 12px; height: {BOX_HEIGHT}px; overflow: hidden; font-family: sans-serif;">
            <div style="background-color: #1a1e26; padding: 15px 20px; border-bottom: 1px solid #2d3439;">
                <p style="color: #888; font-size: 12px; font-weight: bold; text-transform: uppercase; margin: 0;">US High Yield Credit Spreads (OAS)</p>
            </div>
            <div style="padding: 10px; height: calc(100% - 60px);">
                <div id="tv_spread" style="height:100%; width:100%;"></div>
            </div>
        </div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.MediumWidget({{
          "symbols": [["FRED:BAMLH0A0HYM2|1D"]],
          "chartOnly": false, "width": "100%", "height": "100%",
          "locale": "en", "colorTheme": "dark", "gridLineColor": "transparent",
          "trendLineColor": "#f23645", "underLineColor": "rgba(242, 54, 69, 0.15)",
          "container_id": "tv_spread"
        }});
        </script>
        """
        components.html(widget_html, height=BOX_HEIGHT + 10)

    st.write("---")
