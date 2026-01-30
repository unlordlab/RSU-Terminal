# modules/market.py
import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index

def render():
    # Título con margen negativo para subirlo
    st.markdown('<h2 style="margin-top:-50px; margin-bottom:20px;">Market Dashboard</h2>', unsafe_allow_html=True)
    
    # Columnas equilibradas
    col1, col2 = st.columns([1, 1])
    BOX_HEIGHT = 450

    with col1:
        # Iniciamos la caja decorativa
        st.markdown('<div class="market-box">', unsafe_allow_html=True)
        st.markdown('<p style="color:#888; font-weight:bold; font-size:12px; margin-bottom:15px; text-transform:uppercase;">Market Indices</p>', unsafe_allow_html=True)
        
        indices = [
            ("S&P 500", "^GSPC"),
            ("NASDAQ 100", "^IXIC"),
            ("DOW JONES", "^DJI"),
            ("RUSSELL 2000", "^RUT")
        ]
        
        for name, ticker in indices:
            price, change = get_market_index(ticker)
            color_class = "pos" if change >= 0 else "neg"
            
            # Renderizado individual por cada fila
            st.markdown(f"""
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
            """, unsafe_allow_html=True)
        
        # Cerramos la caja
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Widget de TradingView encapsulado en un contenedor idéntico al de la izquierda
        html_widget = f"""
        <div style="background-color: #11141a; border: 1px solid #2d3439; border-radius: 12px; height: {BOX_HEIGHT}px; overflow: hidden; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            <p style="color:#888; font-weight:bold; font-size:12px; margin-bottom:15px; text-transform: uppercase; letter-spacing:1px;">Credit Spreads (OAS)</p>
            <div id="tv_chart_spread" style="height: 350px; width: 100%;"></div>
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
          "container_id": "tv_chart_spread"
        }});
        </script>
        """
        # El height del component debe ser ligeramente mayor al del div para evitar scroll
        components.html(html_widget, height=BOX_HEIGHT + 10)

    st.write("---")
