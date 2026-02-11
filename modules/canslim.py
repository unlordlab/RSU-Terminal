# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from datetime import datetime
from config import get_ia_model, obtener_prompt_github

def render():
    # ═══════════════════════════════════════════════════════════
    # CSS GLOBAL - Estética Market.py (Dark/Professional)
    # ═══════════════════════════════════════════════════════════
    st.markdown("""
    <style>
        /* Reset y base */
        .main > div { padding-top: 0; }
        
        /* Contenedores estilo market.py */
        .rsu-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
            margin-bottom: 20px;
        }
        .rsu-header {
            background: #0c0e12;
            padding: 12px 15px;
            border-bottom: 1px solid #1a1e26;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .rsu-title {
            margin: 0;
            color: white;
            font-size: 14px;
            font-weight: bold;
        }
        .rsu-content {
            padding: 15px;
            background: #11141a;
        }
        
        /* Cards de métricas estilo market.py */
        .metric-card {
            background: #0c0e12;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #1a1e26;
            text-align: center;
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            border-color: #2a3f5f;
            transform: translateY(-2px);
        }
        .metric-label {
            color: #888;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .metric-value {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            margin: 5px 0;
        }
        .metric-tag {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: bold;
            background: #2a3f5f;
            color: #00ffad;
            margin-bottom: 8px;
        }
        .metric-delta {
            font-size: 11px;
            font-weight: bold;
        }
        .positive { color: #00ffad; }
        .negative { color: #f23645; }
        
        /* Input estilizado */
        .ticker-input-container {
            background: #0c0e12;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #1a1e26;
            margin-bottom: 20px;
        }
        div[data-testid="stTextInput"] input {
            background: #11141a !important;
            color: white !important;
            border: 1px solid #2a3f5f !important;
            border-radius: 8px !important;
            font-size: 1.2rem !important;
            font-weight: bold !important;
            text-transform: uppercase !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #00ffad !important;
            box-shadow: 0 0 0 2px rgba(0, 255, 173, 0.2) !important;
        }
        
        /* TradingView container */
        .chart-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #0c0e12;
        }
        
        /* Tabs estilo market.py */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            background: #0c0e12;
            padding: 0 15px;
            border-bottom: 1px solid #1a1e26;
        }
        .stTabs [data-baseweb="tab"] {
            color: #888;
            border: none;
            padding: 12px 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: white;
            background: #1a1e26;
        }
        .stTabs [aria-selected="true"] {
            color: #00ffad !important;
            border-bottom: 2px solid #00ffad !important;
            background: #11141a !important;
        }
        
        /* Sección RSU PROMPT - Hero Section */
        .rsu-hero {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 2px solid #00ffad;
            border-radius: 15px;
            padding: 30px;
            margin-top: 30px;
            position: relative;
            overflow: hidden;
        }
        .rsu-hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00ffad, #00ffad44, #00ffad);
            animation: shimmer 3s infinite;
        }
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        .rsu-hero-title {
            color: #00ffad;
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .rsu-hero-subtitle {
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 20px;
        }
        .rsu-button {
            background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%) !important;
            color: #0c0e12 !important;
            border: none !important;
            padding: 15px 30px !important;
            border-radius: 10px !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(0, 255, 173, 0.3) !important;
        }
        .rsu-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 255, 173, 0.4) !important;
        }
        .rsu-button:active {
            transform: translateY(0);
        }
        
        /* Contenedor de resultado del prompt */
        .prompt-result {
            background: #0c0e12;
            border: 1px solid #2a3f5f;
            border-radius: 10px;
            padding: 25px;
            margin-top: 20px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            color: #eee;
            line-height: 1.6;
            max-height: 600px;
            overflow-y: auto;
        }
        .prompt-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #1a1e26;
        }
        .prompt-badge {
            background: #00ffad22;
            color: #00ffad;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        /* Tooltips */
        .tooltip-container {
            position: relative;
            cursor: help;
        }
        .tooltip-icon {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: #1a1e26;
            border: 2px solid #555;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 16px;
            font-weight: bold;
        }
        .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px 12px;
            border-radius: 6px;
            position: absolute;
            z-index: 999;
            top: 35px;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        
        /* Grid de métricas */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        /* Loading animation */
        .loading-pulse {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00ffad;
            animation: pulse 1.5s infinite;
            margin-right: 10px;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
        }
    </style>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # 1. HEADER Y INPUT DE TICKER
    # ═══════════════════════════════════════════════════════════
    st.markdown('<h1 style="text-align:center; margin-bottom:30px; color:white;">RSU Intelligence Terminal</h1>', unsafe_allow_html=True)
    
    # Input container estilizado
    st.markdown('<div class="ticker-input-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.write("")
    with col2:
        t_in = st.text_input("🔍 TICKER SYMBOL", "NVDA", key="ticker_input").upper()
    with col3:
        st.write("")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if not t_in:
        st.warning("⚠️ Introdueix un ticker per començar l'anàlisi")
        return

    # ═══════════════════════════════════════════════════════════
    # 2. GRÀFIC TRADINGVIEW (Full Width)
    # ═══════════════════════════════════════════════════════════
    st.markdown('<div class="rsu-container">', unsafe_allow_html=True)
    st.markdown('<div class="rsu-header"><p class="rsu-title">📈 Technical Chart - TradingView Pro</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    tradingview_widget = f"""
    <div style="height:600px;">
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
        "container_id": "tradingview_chart",
        "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"]
      }});
      </script>
    </div>
    """
    components.html(tradingview_widget, height=600)
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Obtenir dades de yfinance
    try:
        ticker_data = yf.Ticker(t_in)
        info = ticker_data.info
        hist = ticker_data.history(period="2d")
        
        # Calcular canvi diari
        if len(hist) >= 2:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            price_change = ((current_price - prev_price) / prev_price) * 100
        else:
            current_price = info.get('currentPrice', 0)
            price_change = 0
            
    except Exception as e:
        st.error(f"Error carregant dades de {t_in}: {e}")
        return

    # ═══════════════════════════════════════════════════════════
    # 3. SECCIÓ ABOUT (Collapsible)
    # ═══════════════════════════════════════════════════════════
    with st.expander(f"📋 About {info.get('longName', t_in)}", expanded=True):
        st.markdown(f"""
        <div style="background:#0c0e12; padding:20px; border-radius:10px; border:1px solid #1a1e26;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <div>
                    <h3 style="color:#00ffad; margin:0;">{info.get('longName', t_in)}</h3>
                    <p style="color:#888; margin:5px 0; font-size:0.9rem;">{info.get('sector', 'Sector N/A')} | {info.get('industry', 'Industry N/A')}</p>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:2rem; font-weight:bold; color:white;">${current_price:,.2f}</div>
                    <div style="color:{'#00ffad' if price_change >= 0 else '#f23645'}; font-weight:bold;">
                        {'▲' if price_change >= 0 else '▼'} {price_change:+.2f}%
                    </div>
                </div>
            </div>
            <p style="color:#ccc; line-height:1.6;">{info.get('longBusinessSummary', 'Descripció no disponible.')}</p>
            <div style="display:flex; gap:20px; margin-top:15px; font-size:0.85rem; color:#666;">
                <span>🏢 {info.get('fullTimeEmployees', 'N/A')} empleats</span>
                <span>📍 {info.get('country', 'N/A')}</span>
                <span>💱 {info.get('currency', 'USD')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # 4. PESTANYES D'ANÀLISI (Estilo market.py)
    # ═══════════════════════════════════════════════════════════
    tabs = st.tabs(["📊 Overview", "💰 Earnings", "📅 Seasonality", "👤 Insider", "📈 Financials", "⚖️ Valuation"])
    
    # TAB 1: OVERVIEW (Métricas clave en grid)
    with tabs[0]:
        st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
        
        metrics = [
            {"label": "Market Cap", "val": info.get('marketCap'), "format": "B", "tag": "Size"},
            {"label": "P/E Ratio", "val": info.get('trailingPE'), "format": "x", "tag": "Valuation"},
            {"label": "Forward P/E", "val": info.get('forwardPE'), "format": "x", "tag": "Future"},
            {"label": "PEG Ratio", "val": info.get('pegRatio'), "format": "x", "tag": "Growth"},
            {"label": "Price/Sales", "val": info.get('priceToSalesTrailing12Months'), "format": "x", "tag": "Sales"},
            {"label": "EV/EBITDA", "val": info.get('enterpriseToEbitda'), "format": "x", "tag": "Enterprise"},
            {"label": "Profit Margin", "val": info.get('profitMargins'), "format": "%", "tag": "Efficiency"},
            {"label": "Revenue Growth", "val": info.get('revenueGrowth'), "format": "%", "tag": "YoY"},
        ]
        
        cols = st.columns(4)
        for i, m in enumerate(metrics):
            with cols[i % 4]:
                val = m['val']
                if val is None or val == 0:
                    display_val = "N/A"
                elif m['format'] == "B":
                    display_val = f"${val/1e9:.2f}B"
                elif m['format'] == "%":
                    display_val = f"{val*100:.2f}%"
                else:
                    display_val = f"{val:.2f}{m['format']}"
                
                st.markdown(f"""
                <div class="metric-card">
                    <span class="metric-tag">{m['tag']}</span>
                    <div class="metric-label">{m['label']}</div>
                    <div class="metric-value">{display_val}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional stats row
        st.write("")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            beta = info.get('beta', 'N/A')
            st.metric("Beta", f"{beta:.2f}" if isinstance(beta, (int, float)) else beta)
        with c2:
            div_yield = info.get('dividendYield', 0)
            st.metric("Div Yield", f"{div_yield*100:.2f}%" if div_yield else "N/A")
        with c3:
            st.metric("52W High", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")
        with c4:
            st.metric("52W Low", f"${info.get('fiftyTwoWeekLow', 0):,.2f}")

    # TAB 2: EARNINGS
    with tabs[1]:
        st.markdown('<div class="rsu-container"><div class="rsu-content">', unsafe_allow_html=True)
        try:
            earnings = ticker_data.earnings
            if earnings is not None and not earnings.empty:
                st.dataframe(earnings, use_container_width=True)
            else:
                st.info("📭 Dades d'earnings no disponibles")
        except:
            st.info("📭 Dades d'earnings no disponibles")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # TAB 3: SEASONALITY (Placeholder para futuro desarrollo)
    with tabs[2]:
        st.markdown('<div class="rsu-container"><div class="rsu-content">', unsafe_allow_html=True)
        st.info("🗓️ Anàlisi de seasonality en desenvolupament...")
        # Aquí puedes integrar datos históricos de seasonality
        st.markdown('</div></div>', unsafe_allow_html=True)

    # TAB 4: INSIDER
    with tabs[3]:
        st.markdown('<div class="rsu-container"><div class="rsu-content">', unsafe_allow_html=True)
        try:
            insider = ticker_data.insider_transactions
            if insider is not None and not insider.empty:
                st.dataframe(insider.head(10), use_container_width=True)
            else:
                st.info("📭 Dades d'insider trading no disponibles")
        except:
            st.info("📭 Dades d'insider trading no disponibles")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # TAB 5: FINANCIALS
    with tabs[4]:
        st.markdown('<div class="rsu-container"><div class="rsu-content">', unsafe_allow_html=True)
        try:
            financials = ticker_data.financials
            if financials is not None and not financials.empty:
                st.dataframe(financials, use_container_width=True)
            else:
                st.info("📭 Estats financers no disponibles")
        except Exception as e:
            st.info(f"📭 Estats financers no disponibles")
        st.markdown('</div></div>', unsafe_allow_html=True)
        
    # TAB 6: VALUATION (Detallado)
    with tabs[5]:
        st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
        
        valuation_metrics = [
            ("Enterprise Value", info.get('enterpriseValue'), "B"),
            ("EV/Revenue", info.get('enterpriseToRevenue'), "x"),
            ("EV/EBITDA", info.get('enterpriseToEbitda'), "x"),
            ("Book Value", info.get('bookValue'), "$"),
            ("Price/Book", info.get('priceToBook'), "x"),
            ("Trailing EPS", info.get('trailingEps'), "$"),
            ("Forward EPS", info.get('forwardEps'), "$"),
        ]
        
        cols = st.columns(4)
        for i, (label, val, fmt) in enumerate(valuation_metrics):
            with cols[i % 4]:
                if val is None:
                    display = "N/A"
                elif fmt == "B":
                    display = f"${val/1e9:.2f}B"
                elif fmt == "$":
                    display = f"${val:.2f}"
                else:
                    display = f"{val:.2f}{fmt}"
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{display}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # 5. SECCIÓ HERO: RSU PROMPT GENERATOR (Énfasis máximo)
    # ═══════════════════════════════════════════════════════════
    st.write("")
    st.markdown("""
    <div class="rsu-hero">
        <div class="rsu-hero-title">
            🤖 RSU Artificial Intelligence
            <span style="font-size:0.8rem; background:#00ffad22; padding:4px 10px; border-radius:20px;">v2.0</span>
        </div>
        <div class="rsu-hero-subtitle">
            Genera un informe complet d'anàlisi fonamental i tècnic utilitzant el prompt personalitzat RSU. 
            L'IA analitzarà {ticker} seguint la metodologia proprietària RSU.
        </div>
    """.replace("{ticker}", t_in), unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        generate_clicked = st.button(
            "✨ GENERAR INFORME RSU COMPLET", 
            key="generate_rsu",
            use_container_width=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # 6. LÓGICA DE GENERACIÓN DEL INFORME
    # ═══════════════════════════════════════════════════════════
    if generate_clicked:
        model_ia, modelo_nombre, error_ia = get_ia_model()
        
        if error_ia:
            st.error(f"❌ Error de connexió amb l'IA: {error_ia}")
        else:
            with st.spinner(""):
                # Animación de carga personalizada
                st.markdown("""
                <div style="text-align:center; padding:40px;">
                    <div class="loading-pulse"></div>
                    <div class="loading-pulse" style="animation-delay:0.2s"></div>
                    <div class="loading-pulse" style="animation-delay:0.4s"></div>
                    <p style="color:#888; margin-top:20px; font-size:1.1rem;">
                        L'RSU AI està analitzant {ticker}...<br>
                        <span style="font-size:0.9rem; color:#555;">Processant mètriques, tendències i fondària de mercat</span>
                    </p>
                </div>
                """.replace("{ticker}", t_in), unsafe_allow_html=True)
                
                try:
                    template = obtener_prompt_github()
                    prompt_final = f"""
                    Analitza l'empresa amb ticker {t_in} seguint aquesta metodologia RSU:
                    
                    {template.replace('[TICKER]', t_in)}
                    
                    Dades actuals del ticker:
                    - Preu actual: ${current_price:.2f}
                    - Canvi diari: {price_change:+.2f}%
                    - Market Cap: ${info.get('marketCap', 0)/1e9:.2f}B
                    - P/E: {info.get('trailingPE', 'N/A')}
                    - Sector: {info.get('sector', 'N/A')}
                    """
                    
                    res = model_ia.generate_content(prompt_final)
                    
                    # Mostrar resultado con formato premium
                    st.markdown(f"""
                    <div class="prompt-result">
                        <div class="prompt-header">
                            <div>
                                <span style="color:white; font-weight:bold; font-size:1.2rem;">📋 Informe RSU: {t_in}</span>
                                <span class="prompt-badge">{modelo_nombre}</span>
                            </div>
                            <div style="color:#666; font-size:0.85rem;">
                                {datetime.now().strftime('%d/%m/%Y %H:%M')}
                            </div>
                        </div>
                        <div style="color:#ddd; line-height:1.8;">
                            {res.text}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botones de acción post-generación
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.download_button(
                            "📥 Descarregar TXT",
                            res.text,
                            file_name=f"RSU_Report_{t_in}_{datetime.now().strftime('%Y%m%d')}.txt",
                            use_container_width=True
                        )
                    with c2:
                        if st.button("🔄 Regenerar", use_container_width=True):
                            st.rerun()
                    with c3:
                        st.button("📤 Compartir", disabled=True, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ Error en la generació de l'informe: {str(e)}")
                    st.info("💡 Consell: Verifica que el prompt de GitHub sigui accessible i el model d'IA estigui configurat correctament.")
