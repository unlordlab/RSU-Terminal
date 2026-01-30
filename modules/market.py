# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    # Título principal
    st.markdown('<h1 style="margin-top:-60px; margin-bottom:25px;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Columnas con proporción 1:1 para simetría perfecta
    col1, col2 = st.columns([1, 1])
    BOX_HEIGHT = 460

    with col1:
        # 1. Preparamos los datos
        indices_data = [
            ("S&P 500", "^GSPC"),
            ("NASDAQ 100", "^IXIC"),
            ("DOW JONES", "^DJI"),
            ("RUSSELL 2000", "^RUT")
        ]
        
        # 2. Construimos el HTML de las filas en una sola variable
        rows_html = ""
        for name, ticker in indices_data:
            price, change = get_market_index(ticker)
            color_class = "pos" if change >= 0 else "neg"
            rows_html += f"""
            <div class="index-row">
                <div>
                    <div style="font-weight:bold; font-size:14px; color:white;">{name}</div>
                    <div style="color:#555; font-size:10px; text-transform:uppercase;">{ticker}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:16px; font-weight:bold; color:white;">{price:,.2f}</div>
                    <div class="{color_class}" style="font-size:11px;">{change:+.2f}%</div>
                </div>
            </div>
            """

        # 3. Renderizamos la tarjeta completa de una sola vez
        st.markdown(f"""
            <div class="dashboard-card">
                <div class="card-header">Market Indices</div>
                {rows_html}
            </div>
        """, unsafe_allow_html=True)

    with col2:
        # Widget de TradingView encapsulado para evitar conflictos de CSS
        tradingview_widget = f"""
        <div style="background-color: #11141a; border: 1px solid #2d3439; border-radius: 12px; height: {BOX_HEIGHT}px; padding: 20px; overflow: hidden; font-family: sans-serif;">
            <div style="color: #888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px;">Credit Spreads (OAS)</div>
            <div id="tv_chart_container" style="height: 360px; width: 100%;"></div>
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
          "underLineColor": "rgba(242, 54, 69, 0.1)",
          "container_id": "tv_chart_container"
        }});
        </script>
        """
        # Renderizado del componente con un pequeño margen extra para el iframe
        components.html(tradingview_widget, height=BOX_HEIGHT + 10)

    st.write("---")
