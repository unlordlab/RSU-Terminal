
# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    st.markdown('<h1 style="margin-top:-60px; margin-bottom:20px;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    col_idx, col_spread = st.columns([1, 2])
    
    # --- COLUMNA IZQUIERDA: ÍNDICES ---
    with col_idx:
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
            price_val = f"{p:,.2f}" if p > 0 else "Cargando..."
            
            cards_html += f"""
            <div style="background-color: #1a1e26; border: 1px solid #2d3439; border-radius: 8px; padding: 12px 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; font-family: sans-serif;">
                <div>
                    <p style="color: white; font-weight: bold; font-size: 14px; margin: 0;">{idx['label']}</p>
                    <p style="color: #555; font-size: 10px; margin: 0; text-transform: uppercase;">{idx['full']}</p>
                </div>
                <div style="text-align:right;">
                    <p style="font-weight: bold; font-size: 16px; color: white; margin: 0;">{price_val}</p>
                    <span style="font-size: 11px; border-radius: 4px; padding: 2px 6px; font-weight: bold;" class="{color_class}">{c:+.2f}%</span>
                </div>
            </div>"""

        st.markdown(f"""
            <div class="group-container">
                <div class="group-header"><p class="group-title">Market Indices</p></div>
                <div class="group-content">{cards_html}</div>
            </div>
        """, unsafe_allow_html=True)

    # --- COLUMNA DERECHA: CREDIT SPREADS ---
    with col_spread:
        # Altura para que coincida con la izquierda
        altura_total = 430 
        
        # Metemos TODO el HTML de la caja y el widget en un solo componente
        full_widget_html = f"""
        <style>
            .group-container {{
                background-color: #11141a; 
                border: 1px solid #2d3439;
                border-radius: 12px; 
                height: {altura_total}px;
                overflow: hidden;
                font-family: sans-serif;
            }}
            .group-header {{
                background-color: #1a1e26;
                padding: 12px 20px;
                border-bottom: 1px solid #2d3439;
            }}
            .group-title {{ 
                color: #888; font-size: 12px; font-weight: bold; 
                text-transform: uppercase; margin: 0; 
            }}
            .group-content {{ padding: 15px; height: calc(100% - 60px); }}
        </style>
        <div class="group-container">
            <div class="group-header"><p class="group-title">US High Yield Credit Spreads (OAS)</p></div>
            <div class="group-content">
                <div id="tv_spread" style="height:100%; width:100%;"></div>
            </div>
        </div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.MediumWidget({{
          "symbols": [["FRED:BAMLH0A0HYM2|1D"]],
          "chartOnly": false,
          "width": "100%",
          "height": "100%",
          "locale": "en",
          "colorTheme": "dark",
          "gridLineColor": "transparent",
          "trendLineColor": "#f23645",
          "underLineColor": "rgba(242, 54, 69, 0.15)",
          "container_id": "tv_spread"
        }});
        </script>
        """
        components.html(full_widget_html, height=altura_total + 10)

    st.write("---")
