import streamlit as st
import yfinance as yf
import pandas as pd
from config import get_ia_model

def get_earnings_data(ticker_symbol):
    """Obtiene datos financieros minimizando bloqueos."""
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        # Datos esenciales
        data = {
            "ticker": ticker_symbol,
            "name": info.get('longName', ticker_symbol),
            "price": info.get('currentPrice') or info.get('regularMarketPreviousClose'),
            "rev_growth": info.get('revenueGrowth'),
            "ebitda_margin": info.get('ebitdaMargins'),
            "pe_ratio": info.get('forwardPE'),
            "eps": info.get('trailingEps'),
            "cash": info.get('freeCashflow')
        }
        return data
    except Exception:
        return None

def render():
    st.title("📅 Earnings Insight")
    st.markdown("---")

    col1, _ = st.columns([1, 2])
    with col1:
        ticker = st.text_input("Introduce Ticker", value="NVDA").upper()

    if st.button("Analizar Reporte"):
        with st.spinner(f"Extrayendo métricas de {ticker}..."):
            data = get_earnings_data(ticker)
            
            if not data or not data['price']:
                st.error("No se pudieron obtener datos. Revisa el ticker.")
                return

            # Cabecera Estilo Capyfin
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Precio", f"${data['price']:.2f}")
            c2.metric("EPS", f"{data['eps']:.2f}" if data['eps'] else "N/A")
            c3.metric("Rev. Growth", f"{data['rev_growth']:.1%}" if data['rev_growth'] else "N/A")
            c4.metric("Forward P/E", f"{data['pe_ratio']:.1f}" if data['pe_ratio'] else "N/A")

            st.write("---")

            # Llamada a IA
            model, name, err = get_ia_model()
            if model:
                prompt = f"""
                Analiza como experto en Capyfin la empresa {data['name']} ({data['ticker']}).
                Métricas: Crecimiento {data['rev_growth']}, Margen EBITDA {data['ebitda_margin']}, PER {data['pe_ratio']}.
                Genera:
                1. MÉTRICAS CLAVE (Resumen breve)
                2. ✅ PUNTOS FUERTES (Bullet points)
                3. ❌ PUNTOS DÉBILES (Bullet points)
                4. 💡 CONCLUSIÓN
                """
                try:
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error en la IA: {e}")
            else:
                st.warning(f"IA no disponible: {err}")
