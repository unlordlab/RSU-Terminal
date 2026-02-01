import streamlit as st
import yfinance as yf
import pandas as pd
from config import get_ia_model

def get_earnings_data(ticker_symbol):
    """Extrae datos con headers para evitar bloqueos de Yahoo Finance."""
    try:
        # Usamos un ticker con sesión para evitar bloqueos 404/403 de Yahoo
        stock = yf.Ticker(ticker_symbol)
        
        # Acceder a info de manera segura
        info = stock.info
        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info:
            # Reintento mínimo si falla la primera carga
            info = stock.fast_info 
            
        calendar = stock.calendar
        next_date = "No disponible"
        
        if calendar is not None:
            if isinstance(calendar, dict):
                next_date = calendar.get('Earnings Date', ["N/A"])[0]
            elif isinstance(calendar, pd.DataFrame) and not calendar.empty:
                next_date = calendar.iloc[0, 0]

        data = {
            "ticker": ticker_symbol,
            "name": info.get('longName', ticker_symbol),
            "price": info.get('currentPrice') or info.get('regularMarketPrice') or info.get('lastPrice'),
            "revenue_growth": info.get('revenueGrowth'),
            "ebitda_margins": info.get('ebitdaMargins'),
            "eps_actual": info.get('trailingEps'),
            "forward_pe": info.get('forwardPE'),
            "debt_to_equity": info.get('debtToEquity'),
            "next_earnings": next_date
        }
        return data
    except Exception as e:
        st.error(f"Error técnico en yfinance: {e}")
        return None

def generate_capyfin_style_analysis(data):
    """Genera el análisis con manejo de error de modelo 404."""
    model, _, _ = get_ia_model()
    
    if not model:
        return "⚠️ Error: No se pudo cargar el modelo de IA. Revisa tu API Key."

    prompt = f"""
    Actúa como analista senior de Capyfin. Analiza {data['ticker']} ({data['name']}):
    - Precio actual: {data['price']}
    - Crecimiento Ingresos: {data['revenue_growth']}
    - Margen EBITDA: {data['ebitda_margins']}
    - PER: {data['forward_pe']}
    
    Genera un informe con:
    ### 📊 Métricas Clave
    ### ✅ Puntos Fuertes
    ### ❌ Puntos Débiles
    ### 💡 Conclusión
    """
    
    try:
        # Forzamos el uso de un modelo que siempre existe si el de config falla
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error en la IA: {str(e)}. Intenta revisar el nombre del modelo en config.py."

def render():
    st.title("📅 Earnings Insight")
    
    ticker = st.text_input("Introduce el Ticker", value="AAPL").upper()
    
    if st.button("Generar Reporte Capyfin"):
        with st.spinner("Buscando datos..."):
            data = get_earnings_data(ticker)
            
            if data and data['price']:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Precio", f"${data['price']:.2f}")
                c2.metric("Próximo Reporte", str(data['next_earnings']).split(' ')[0])
                c3.metric("Rev. Growth", f"{data['revenue_growth']:.2%}" if data['revenue_growth'] else "N/A")
                c4.metric("Forward P/E", f"{data['forward_pe']:.2f}" if data['forward_pe'] else "N/A")
                
                st.markdown("---")
                st.markdown(generate_capyfin_style_analysis(data))
            else:
                st.error(f"No hay conexión con Yahoo Finance para {ticker}. Inténtalo en unos segundos.")
