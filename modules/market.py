# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    # Título principal con ajuste de margen
    st.markdown('<h1 style="margin-top:-60px; margin-bottom:25px;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Columnas 1:1 para asegurar que tengan la misma anchura
    col_idx, col_widget = st.columns([1, 1])
    
    # Altura fija para que ambas cajas terminen igual (simetría)
    BOX_HEIGHT = 440

    # --- COLUMNA IZQUIERDA: MARKET INDICES ---
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
            # Fallback por si el precio llega a 0
            price_display = f"{p:,.2f}" if p > 0 else "Cargando..."
            
            cards_html += f"""
            <div class="index-card">
                <div>
                    <p class="index-ticker">{idx['label']}</p>
                    <p class="index-fullname">{idx['full']}</p>
                </div>
                <div style="text-align:right;">
                    <p class="index-price">{price_display}</p>
                    <span class="index-delta {color_class}">{c:+.2f}%</span>
                </div>
            </div>"""

        # Renderizamos la caja de índices
        st.markdown(f"""
            <div class="group-container" style="height: {BOX_HEIGHT}px;">
                <div class="group-header"><p class="group-title">Market Indices</p></div>
                <div class="group-content">{cards_html}</div>
            </div>
        """, unsafe_allow_html=True)

    # --- COLUMNA DERECHA: CREDIT SPREADS (WIDGET INTEGRADO) ---
    with col_widget:
        # Inyectamos el HTML del contenedor y el widget en un solo componente para evitar errores de CSS
        full_widget_html = f"""
        <style>
            .group-container {{
                background-color: #11141a; 
                border: 1px solid #2d3439;
                border-radius: 12px; 
                height: {BOX_HEIGHT}px;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            .group-header {{
                background-color: #1a1e26;
                padding: 12px 20px;
                border-bottom: 1px solid #2d3439;
            }}
            .group-title {{ 
                color: #888; font-size: 11px; font-weight: bold; 
                text-transform: uppercase; margin: 0; letter-spacing: 1px;
            }}
            .group-content {{ padding: 10px; height: calc(100% - 50px); }}
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
        # Usamos BOX_HEIGHT + un pequeño margen para el iframe de Streamlit
        components.html(full_widget_html, height=BOX_HEIGHT + 10)

    st.write("---")
