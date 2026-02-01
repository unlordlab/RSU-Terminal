import streamlit as st
import yfinance as yf
import pandas as pd
from config import get_ia_model

def get_earnings_data(ticker_symbol):
    """Extrae datos financieros clave para el análisis."""
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    
    # Intentamos obtener el calendario de earnings
    calendar = stock.calendar
    next_date = "N/A"
    if calendar is not None and not calendar.empty:
        # Dependiendo de la versión de yfinance, el formato del calendar varía
        if isinstance(calendar, pd.DataFrame) and 'Earnings Date' in calendar.index:
            next_date = calendar.loc['Earnings Date'][0]
        else:
            next_date = calendar.iloc[0, 0]

    data = {
        "ticker": ticker_symbol,
        "name": info.get('longName', ticker_symbol),
        "price": info.get('currentPrice'),
        "revenue_growth": info.get('revenueGrowth'),
        "ebitda_margins": info.get('ebitdaMargins'),
        "eps_actual": info.get('trailingEps'),
        "forward_pe": info.get('forwardPE'),
        "debt_to_equity": info.get('debtToEquity'),
        "free_cash_flow": info.get('freeCashflow'),
        "next_earnings": next_date
    }
    return data

def generate_capyfin_style_analysis(data):
    """Usa Gemini para generar el análisis cualitativo."""
    model, _, _ = get_ia_model()
    if not model:
        return "⚠️ Error: Configura tu GEMINI_API_KEY para ver el análisis."

    prompt = f"""
    Eres un analista financiero senior de Capyfin. Analiza los siguientes datos de {data['name']} ({data['ticker']}):
    - Crecimiento de Ingresos: {data['revenue_growth']}
    - Margen EBITDA: {data['ebitda_margins']}
    - EPS: {data['eps_actual']}
    - PER Adelantado: {data['forward_pe']}
    - Deuda/Patrimonio: {data['debt_to_equity']}
    
    Genera un informe con este formato exacto:
    
    ### 📊 Métricas Clave
    (Menciona 3 métricas críticas comentadas brevemente)
    
    ### ✅ Puntos Fuertes (Estilo Capyfin)
    - (Punto 1)
    - (Punto 2)
    
    ### ❌ Puntos Débiles (Estilo Capyfin)
    - (Punto 1)
    - (Punto 2)
    
    ### 💡 Conclusión
    (Una frase sobre si el reporte fue sólido o decepcionante)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generando análisis: {e}"

def render():
    st.title("📅 Earnings Insight")
    st.markdown("---")
    
    col_input, _ = st.columns([1, 2])
    with col_input:
        ticker = st.text_input("Introduce el Ticker (ej: NVDA)", value="AAPL").upper()
    
    if st.button("Generar Reporte Estilo Capyfin"):
        with st.spinner(f"Analizando {ticker}..."):
            try:
                data = get_earnings_data(ticker)
                
                # Layout de métricas superiores
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Precio", f"${data['price']}")
                c2.metric("Próximo Reporte", str(data['next_earnings']).split()[0])
                c3.metric("Rev. Growth", f"{data['revenue_growth']:.2%}" if data['revenue_growth'] else "N/A")
                c4.metric("Forward P/E", f"{data['forward_pe']:.2f}" if data['forward_pe'] else "N/A")
                
                st.markdown("---")
                
                # Análisis de IA
                analysis = generate_capyfin_style_analysis(data)
                st.markdown(analysis)
                
            except Exception as e:
                st.error(f"No se pudieron obtener datos para {ticker}. Verifica el símbolo.")