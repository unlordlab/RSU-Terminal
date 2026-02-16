import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from config import get_ia_model
import time
import random
from functools import wraps
import hashlib
import requests
import os

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────

def rate_limit_delay():
    time.sleep(random.uniform(0.3, 0.8))

# ────────────────────────────────────────────────
# CARGA DE PROMPT RSU
# ────────────────────────────────────────────────

def load_rsu_prompt():
    """Carga el prompt de análisis hedge fund desde earnings.txt en raíz."""
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'earnings.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error cargando prompt RSU: {e}")
        return None

# ────────────────────────────────────────────────
# OBTENCIÓN DE DATOS MEJORADA
# ────────────────────────────────────────────────

def get_yfinance_data(ticker_symbol):
    """Obtiene datos de yfinance incluyendo earnings trimestrales."""
    try:
        rate_limit_delay()
        ticker = yf.Ticker(ticker_symbol)
        
        try:
            info = ticker.info
        except:
            info = dict(ticker.fast_info) if hasattr(ticker, 'fast_info') else {}
        
        # Obtener histórico
        try:
            hist = ticker.history(period="1y", auto_adjust=True)
            hist_dict = {
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'open': hist['Open'].tolist(),
                'high': hist['High'].tolist(),
                'low': hist['Low'].tolist(),
                'close': hist['Close'].tolist(),
                'volume': hist['Volume'].tolist()
            } if not hist.empty else None
        except:
            hist_dict = None
        
        # Obtener earnings anuales
        try:
            earnings = ticker.earnings
            earnings_dict = None
            if earnings is not None and not earnings.empty:
                earnings_dict = {
                    'dates': earnings.index.strftime('%Y-%m-%d').tolist() if hasattr(earnings.index, 'strftime') else list(earnings.index),
                    'revenue': earnings.get('Revenue', earnings.get('Total Revenue', [])).tolist() if hasattr(earnings, 'get') else [],
                    'earnings': earnings.get('Earnings', earnings.get('Net Income', [])).tolist() if hasattr(earnings, 'get') else []
                }
        except:
            earnings_dict = None
        
        # OBTENER EARNINGS TRIMESTRALES (crucial para análisis reciente)
        quarterly_earnings_dict = None
        try:
            quarterly = ticker.quarterly_earnings
            if quarterly is not None and not quarterly.empty:
                quarterly_earnings_dict = {
                    'dates': quarterly.index.strftime('%Y-%m-%d').tolist() if hasattr(quarterly.index, 'strftime') else list(quarterly.index),
                    'revenue': quarterly.get('Revenue', []).tolist() if 'Revenue' in quarterly.columns else [],
                    'earnings': quarterly.get('Earnings', []).tolist() if 'Earnings' in quarterly.columns else []
                }
        except Exception as e:
            print(f"Error getting quarterly earnings: {e}")
            quarterly_earnings_dict = None
        
        # Calendario de earnings
        try:
            calendar = ticker.calendar
            calendar_list = []
            if calendar is not None and not calendar.empty:
                for idx, row in calendar.iterrows():
                    calendar_list.append({
                        'date': str(idx),
                        'eps_est': row.get('Earnings Estimate', 'N/A'),
                        'revenue_est': row.get('Revenue Estimate', 'N/A')
                    })
        except:
            calendar_list = []
        
        # EPS estimates
        eps_estimates_dict = None
        try:
            eps_est = ticker.eps_estimates
            if eps_est is not None and not eps_est.empty:
                eps_estimates_dict = eps_est.to_dict()
        except:
            pass
        
        # Recomendaciones
        recommendations_dict = None
        try:
            recs = ticker.recommendations
            if recs is not None and not recs.empty:
                recommendations_dict = recs.tail(5).to_dict()
        except:
            pass
        
        return {
            'info': info, 
            'history': hist_dict, 
            'earnings': earnings_dict,
            'quarterly_earnings': quarterly_earnings_dict,
            'calendar': calendar_list,
            'eps_estimates': eps_estimates_dict,
            'recommendations': recommendations_dict,
            'source': 'yfinance'
        }
        
    except Exception as e:
        print(f"Error yfinance: {e}")
        return None

def get_finnhub_data(ticker, api_key):
    """Obtiene datos de Finnhub."""
    if not api_key:
        return None
    
    try:
        base_url = "https://finnhub.io/api/v1"
        headers = {"X-Finnhub-Token": api_key}
        
        quote_resp = requests.get(f"{base_url}/quote", params={"symbol": ticker}, headers=headers, timeout=10)
        quote = quote_resp.json() if quote_resp.status_code == 200 else {}
        
        profile_resp = requests.get(f"{base_url}/stock/profile2", params={"symbol": ticker}, headers=headers, timeout=10)
        profile = profile_resp.json() if profile_resp.status_code == 200 else {}
        
        metrics_resp = requests.get(f"{base_url}/stock/metric", params={"symbol": ticker, "metric": "all"}, headers=headers, timeout=10)
        metrics = metrics_resp.json().get('metric', {}) if metrics_resp.status_code == 200 else {}
        
        return {
            'info': {
                'longName': profile.get('name'),
                'sector': profile.get('finnhubIndustry'),
                'industry': profile.get('industry'),
                'country': profile.get('country'),
                'website': profile.get('weburl'),
                'longBusinessSummary': profile.get('description'),
                'currentPrice': quote.get('c'),
                'previousClose': quote.get('pc'),
                'open': quote.get('o'),
                'dayHigh': quote.get('h'),
                'dayLow': quote.get('l'),
                'marketCap': (profile.get('marketCapitalization') or 0) * 1e6,
                'volume': quote.get('v'),
                'beta': metrics.get('beta'),
                'revenueGrowth': metrics.get('revenueGrowth5Y'),
                'ebitdaMargins': metrics.get('ebitdaMarginAnnual'),
                'profitMargins': metrics.get('netProfitMarginAnnual'),
                'trailingPE': metrics.get('peTTM'),
                'forwardPE': metrics.get('peNormalizedAnnual'),
                'returnOnEquity': metrics.get('roeTTM'),
                'trailingEps': metrics.get('epsTTM'),
                'totalCash': metrics.get('cashPerShareAnnual', 0) * (profile.get('shareOutstanding') or 0) * 1e6 if profile.get('shareOutstanding') else 0,
                'totalDebt': metrics.get('totalDebtAnnual'),
                'dividendYield': metrics.get('dividendYieldIndicatedAnnual'),
                'debtToEquity': metrics.get('totalDebtToTotalEquityAnnual'),
            },
            'history': None,
            'earnings': None,
            'quarterly_earnings': None,
            'calendar': [],
            'source': 'finnhub'
        }
        
    except Exception as e:
        print(f"Error Finnhub: {e}")
        return None

def process_data(raw_data, ticker):
    """Procesa datos crudos."""
    if not raw_data:
        return None
    
    info = raw_data.get('info', {})
    
    def get(keys, default=None):
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            if key in info and info[key] is not None:
                val = info[key]
                if isinstance(val, pd.Series):
                    return val.iloc[0] if len(val) > 0 else default
                if isinstance(val, (int, float, str, bool)):
                    return val
                try:
                    return float(val)
                except:
                    return val
        return default
    
    price = get(['currentPrice', 'regularMarketPrice', 'previousClose', 'c'], 0)
    prev_close = get(['previousClose', 'regularMarketPreviousClose', 'pc'], price)
    
    if price == 0:
        return None
    
    hist_df = pd.DataFrame()
    hist_data = raw_data.get('history')
    if hist_data:
        try:
            hist_df = pd.DataFrame({
                'Open': hist_data['open'],
                'High': hist_data['high'],
                'Low': hist_data['low'],
                'Close': hist_data['close'],
                'Volume': hist_data['volume']
            }, index=pd.to_datetime(hist_data['dates']))
        except:
            pass
    
    earnings_df = pd.DataFrame()
    earnings_data = raw_data.get('earnings')
    if earnings_data and earnings_data.get('dates'):
        try:
            earnings_df = pd.DataFrame({
                'Revenue': earnings_data.get('revenue', []),
                'Earnings': earnings_data.get('earnings', [])
            }, index=earnings_data['dates'])
        except:
            pass
    
    # Procesar earnings trimestrales
    quarterly_earnings_df = pd.DataFrame()
    quarterly_data = raw_data.get('quarterly_earnings')
    if quarterly_data and quarterly_data.get('dates'):
        try:
            quarterly_earnings_df = pd.DataFrame({
                'Revenue': quarterly_data.get('revenue', []),
                'Earnings': quarterly_data.get('earnings', [])
            }, index=quarterly_data['dates'])
        except:
            pass
    
    data = {
        "ticker": ticker,
        "name": get(['longName', 'shortName', 'name'], ticker),
        "sector": get(['sector', 'finnhubIndustry'], 'N/A'),
        "industry": get(['industry'], 'N/A'),
        "country": get(['country'], 'N/A'),
        "employees": int(get(['fullTimeEmployees'], 0) or 0),
        "website": get(['website', 'weburl'], '#'),
        "summary": get(['longBusinessSummary', 'description'], f"Empresa {ticker}"),
        
        "price": float(price),
        "prev_close": float(prev_close),
        "open": float(get(['open', 'regularMarketOpen', 'o'], price)),
        "day_high": float(get(['dayHigh', 'regularMarketDayHigh', 'h'], price * 1.01)),
        "day_low": float(get(['dayLow', 'regularMarketDayLow', 'l'], price * 0.99)),
        "fifty_two_high": float(get(['fiftyTwoWeekHigh', '52WeekHigh'], price * 1.2)),
        "fifty_two_low": float(get(['fiftyTwoWeekLow', '52WeekLow'], price * 0.8)),
        "volume": int(get(['volume', 'regularMarketVolume', 'v'], 0) or 0),
        "avg_volume": int(get(['averageVolume', 'avgVolume'], 0) or 0),
        
        "market_cap": float(get(['marketCap', 'marketCapitalization'], 0) or 0),
        "enterprise_value": float(get(['enterpriseValue'], 0) or 0),
        
        "rev_growth": float(get(['revenueGrowth', 'revenueGrowth5Y'])) if get(['revenueGrowth', 'revenueGrowth5Y']) is not None else None,
        "ebitda_margin": float(get(['ebitdaMargins', 'ebitdaMarginAnnual'])) if get(['ebitdaMargins', 'ebitdaMarginAnnual']) is not None else None,
        "profit_margin": float(get(['profitMargins', 'netProfitMarginAnnual'])) if get(['profitMargins', 'netProfitMarginAnnual']) is not None else None,
        "operating_margin": float(get(['operatingMargins'])) if get(['operatingMargins']) is not None else None,
        "gross_margin": float(get(['grossMargins'])) if get(['grossMargins']) is not None else None,
        
        "pe_trailing": float(get(['trailingPE', 'peTrailing', 'peTTM'])) if get(['trailingPE', 'peTrailing', 'peTTM']) is not None else None,
        "pe_forward": float(get(['forwardPE', 'peForward', 'peNormalizedAnnual'])) if get(['forwardPE', 'peForward', 'peNormalizedAnnual']) is not None else None,
        "peg_ratio": float(get(['pegRatio'])) if get(['pegRatio']) is not None else None,
        "price_to_sales": float(get(['priceToSalesTrailing12Months'])) if get(['priceToSalesTrailing12Months']) is not None else None,
        "price_to_book": float(get(['priceToBook'])) if get(['priceToBook']) is not None else None,
        
        "eps": float(get(['trailingEps', 'epsTTM'])) if get(['trailingEps', 'epsTTM']) is not None else None,
        "eps_forward": float(get(['forwardEps'])) if get(['forwardEps']) is not None else None,
        "eps_growth": float(get(['earningsGrowth'])) if get(['earningsGrowth']) is not None else None,
        
        "roe": float(get(['returnOnEquity', 'roeTTM'])) if get(['returnOnEquity', 'roeTTM']) is not None else None,
        "roa": float(get(['returnOnAssets'])) if get(['returnOnAssets']) is not None else None,
        
        "cash": float(get(['totalCash', 'freeCashflow'], 0) or 0),
        "free_cashflow": float(get(['freeCashflow'], 0) or 0),
        "operating_cashflow": float(get(['operatingCashflow'], 0) or 0),
        "debt": float(get(['totalDebt', 'totalDebtAnnual'], 0) or 0),
        "debt_to_equity": float(get(['debtToEquity', 'totalDebtToTotalEquityAnnual'])) if get(['debtToEquity', 'totalDebtToTotalEquityAnnual']) is not None else None,
        "current_ratio": float(get(['currentRatio'])) if get(['currentRatio']) is not None else None,
        
        "dividend_rate": float(get(['dividendRate'], 0) or 0),
        "dividend_yield": float(get(['dividendYield', 'dividendYieldIndicatedAnnual'], 0) or 0) / 100 if get(['dividendYield'], 0) and get(['dividendYield'], 0) > 1 else float(get(['dividendYield'], 0) or 0),
        "ex_div_date": get(['exDividendDate']),
        "payout_ratio": float(get(['payoutRatio'], 0) or 0),
        
        "target_high": float(get(['targetHighPrice'], price * 1.2)),
        "target_low": float(get(['targetLowPrice'], price * 0.8)),
        "target_mean": float(get(['targetMeanPrice', 'targetMedianPrice'], price)),
        "target_median": float(get(['targetMedianPrice', 'targetMeanPrice'], price)),
        "recommendation": get(['recommendationKey'], 'none'),
        "num_analysts": int(get(['numberOfAnalystOpinions'], 0) or 0),
        
        "hist": hist_df,
        "earnings_hist": earnings_df,
        "quarterly_earnings_hist": quarterly_earnings_df,
        "earnings_calendar": raw_data.get('calendar', []),
        "eps_estimates": raw_data.get('eps_estimates'),
        "recommendations": raw_data.get('recommendations'),
        "beta": float(get(['beta'], 0) or 0),
        
        "is_real_data": raw_data.get('source') != 'mock',
        "data_source": raw_data.get('source', 'unknown')
    }
    
    if data['prev_close'] and data['prev_close'] != 0:
        data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
        data['change_abs'] = data['price'] - data['prev_close']
    else:
        data['change_pct'] = 0
        data['change_abs'] = 0
        
    if data['fifty_two_high'] and data['fifty_two_high'] != 0:
        data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
    else:
        data['pct_from_high'] = 0
    
    return data

def get_mock_data(ticker):
    """Datos de demostración."""
    mock_db = {
        "AAPL": {"name": "Apple Inc.", "sector": "Technology", "price": 275.69, "market_cap": 4.05e12, "rev_growth": 0.157, "pe_forward": 29.7, "eps": 7.91, "dividend_yield": 0.0038, "roe": 1.52, "beta": 1.107, "ebitda_margin": 0.351, "profit_margin": 0.270},
        "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "price": 420.30, "market_cap": 3.1e12, "rev_growth": 0.15, "pe_forward": 32.0, "eps": 11.80, "dividend_yield": 0.007, "roe": 0.38, "beta": 0.9, "ebitda_margin": 0.45, "profit_margin": 0.35},
        "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "price": 875.50, "market_cap": 2.15e12, "rev_growth": 2.10, "pe_forward": 35.0, "eps": 12.90, "dividend_yield": 0.0003, "roe": 0.55, "beta": 1.75, "ebitda_margin": 0.58, "profit_margin": 0.48},
    }
    
    if ticker not in mock_db:
        seed = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 1000
        base_price = 50 + (seed % 950)
        mock_db[ticker] = {
            "name": f"{ticker} Corp.", "sector": "Technology", "price": float(base_price),
            "market_cap": float(base_price * 1e9 * random.uniform(0.5, 5)),
            "rev_growth": random.uniform(-0.1, 0.5), "pe_forward": random.uniform(15, 50),
            "eps": float(base_price) / random.uniform(15, 40), "dividend_yield": random.choice([0.0, 0.0, 0.0, 0.02, 0.04]),
            "roe": random.uniform(0.05, 0.40), "beta": random.uniform(0.8, 2.0),
            "ebitda_margin": random.uniform(0.15, 0.40), "profit_margin": random.uniform(0.10, 0.30)
        }
    
    mock = mock_db[ticker]
    price = float(mock["price"])
    
    return {
        "ticker": ticker, "name": mock["name"], "sector": mock["sector"], "industry": "Technology",
        "country": "United States", "employees": 100000, "website": "#",
        "summary": f"{mock['name']} es líder en su sector con fuerte posición de mercado.",
        "price": price, "prev_close": price * 0.98, "open": price, "day_high": price * 1.02,
        "day_low": price * 0.98, "fifty_two_high": price * 1.3, "fifty_two_low": price * 0.7,
        "volume": 50000000, "avg_volume": 45000000, "market_cap": mock["market_cap"],
        "enterprise_value": mock["market_cap"] * 1.1, "rev_growth": mock["rev_growth"],
        "ebitda_margin": mock["ebitda_margin"], "profit_margin": mock["profit_margin"],
        "operating_margin": mock["profit_margin"] * 1.2, "gross_margin": 0.45,
        "pe_trailing": mock["pe_forward"] * 1.1, "pe_forward": mock["pe_forward"],
        "peg_ratio": 1.5, "price_to_sales": 8.0, "price_to_book": 25.0,
        "eps": mock["eps"], "eps_forward": mock["eps"] * 1.15, "eps_growth": mock["rev_growth"],
        "roe": mock["roe"], "roa": mock["roe"] * 0.6, "cash": mock["market_cap"] * 0.05,
        "free_cashflow": mock["market_cap"] * 0.03, "operating_cashflow": mock["market_cap"] * 0.04,
        "debt": mock["market_cap"] * 0.15, "debt_to_equity": 50.0, "current_ratio": 1.2,
        "dividend_rate": price * mock["dividend_yield"], "dividend_yield": mock["dividend_yield"],
        "ex_div_date": None, "payout_ratio": 0.20, "target_high": price * 1.3,
        "target_low": price * 0.8, "target_mean": price * 1.1, "target_median": price * 1.1,
        "recommendation": "buy", "num_analysts": 35, "hist": pd.DataFrame(),
        "earnings_hist": pd.DataFrame(), "quarterly_earnings_hist": pd.DataFrame(),
        "earnings_calendar": [], "eps_estimates": None, "recommendations": None,
        "beta": mock["beta"], "is_real_data": False, "data_source": "mock",
        "change_pct": 2.04, "change_abs": price * 0.02, "pct_from_high": -5.0
    }

# ────────────────────────────────────────────────
# FUNCIONES DE RENDER
# ────────────────────────────────────────────────

def format_value(value, prefix="", suffix="", decimals=2):
    if value is None or value == 0 or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    try:
        val = float(value)
        if abs(val) >= 1e12:
            return f"{prefix}{val/1e12:.{decimals}f}T{suffix}"
        elif abs(val) >= 1e9:
            return f"{prefix}{val/1e9:.{decimals}f}B{suffix}"
        elif abs(val) >= 1e6:
            return f"{prefix}{val/1e6:.{decimals}f}M{suffix}"
        elif abs(val) >= 1e3:
            return f"{prefix}{val/1e3:.{decimals}f}K{suffix}"
        return f"{prefix}{val:.{decimals}f}{suffix}"
    except:
        return str(value)

def format_pct(value, decimals=2):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A", "#888"
    try:
        val = float(value) * 100 if abs(float(value)) < 1 else float(value)
        color = "#00ffad" if val >= 0 else "#f23645"
        return f"{val:.{decimals}f}%", color
    except:
        return "N/A", "#888"

def generate_outlook_points(data):
    """Genera puntos de outlook basados en métricas reales."""
    positive = []
    challenges = []
    
    if data.get('rev_growth'):
        if data['rev_growth'] > 0.20:
            positive.append(f"🚀 Crecimiento explosivo de ingresos ({data['rev_growth']:.1%})")
        elif data['rev_growth'] > 0.10:
            positive.append(f"📈 Sólido crecimiento de ingresos ({data['rev_growth']:.1%})")
        elif data['rev_growth'] > 0:
            positive.append(f"↗️ Crecimiento moderado de ingresos ({data['rev_growth']:.1%})")
        else:
            challenges.append(f"📉 Contracción de ingresos ({data['rev_growth']:.1%})")
    
    if data.get('profit_margin'):
        if data['profit_margin'] > 0.25:
            positive.append(f"💰 Márgenes de beneficio excepcionales ({data['profit_margin']:.1%})")
        elif data['profit_margin'] > 0.15:
            positive.append(f"✅ Márgenes de beneficio saludables ({data['profit_margin']:.1%})")
        elif data['profit_margin'] < 0.05:
            challenges.append(f"⚠️ Márgenes de beneficio comprimidos ({data['profit_margin']:.1%})")
    
    if data.get('ebitda_margin'):
        if data['ebitda_margin'] > 0.30:
            positive.append(f"🏭 Alta generación operativa (EBITDA {data['ebitda_margin']:.1%})")
    
    if data.get('roe'):
        if data['roe'] > 0.30:
            positive.append(f"🎯 ROE excepcional ({data['roe']:.1%}) - Eficiencia superior")
        elif data['roe'] > 0.15:
            positive.append(f"📊 ROE sólido ({data['roe']:.1%})")
        elif data['roe'] < 0.08:
            challenges.append(f"📉 ROE bajo ({data['roe']:.1%}) - Menor rentabilidad")
    
    if data.get('debt_to_equity'):
        if data['debt_to_equity'] < 50:
            positive.append(f"⚖️ Balance poco apalancado (Deuda/Pat {data['debt_to_equity']:.0f}%)")
        elif data['debt_to_equity'] > 100:
            challenges.append(f"⚠️ Alto apalancamiento financiero ({data['debt_to_equity']:.0f}%)")
    
    if data.get('free_cashflow') and data['free_cashflow'] > 0:
        positive.append(f"💵 Generación robusta de Free Cash Flow ({format_value(data['free_cashflow'], '$')})")
    elif data.get('free_cashflow') and data['free_cashflow'] < 0:
        challenges.append(f"🔥 Free Cash Flow negativo - quema de caja")
    
    if data.get('pe_forward'):
        if data['pe_forward'] < 15:
            positive.append(f"💎 Valoración atractiva (P/E {data['pe_forward']:.1f}x)")
        elif data['pe_forward'] > 40:
            challenges.append(f"💸 Valoración elevada (P/E {data['pe_forward']:.1f}x) - altas expectativas")
    
    if data.get('dividend_yield') and data['dividend_yield'] > 0.02:
        positive.append(f"🎁 Dividendo atractivo ({data['dividend_yield']:.2%} yield)")
    
    if data.get('target_mean') and data.get('price'):
        upside = ((data['target_mean'] - data['price']) / data['price']) * 100
        if upside > 20:
            positive.append(f"🎯 Potencial alcista del {upside:.1f}% vs consenso")
        elif upside < -10:
            challenges.append(f"📉 Precio por encima del consenso ({upside:.1f}%)")
    
    defaults_pos = [
        "🌟 Posición de liderazgo en el sector",
        "🔧 Fortalezas operativas diferenciadas",
        "📱 Exposición a tendencias de crecimiento"
    ]
    defaults_chal = [
        "🌪️ Exposición a ciclos económicos",
        "⚔️ Presión competitiva del sector",
        "🌍 Incertidumbre macroeconómica global"
    ]
    
    while len(positive) < 3:
        positive.append(defaults_pos[len(positive) % len(defaults_pos)])
    while len(challenges) < 3:
        challenges.append(defaults_chal[len(challenges) % len(defaults_chal)])
    
    return positive[:4], challenges[:4]

def render_earnings_chart(data):
    """Renderiza gráfico de earnings históricos."""
    if data.get('earnings_hist') is None or data['earnings_hist'].empty:
        st.info("📊 Datos históricos de earnings no disponibles")
        return
    
    earnings = data['earnings_hist']
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    if 'Revenue' in earnings.columns and not earnings['Revenue'].empty:
        fig.add_trace(
            go.Bar(
                x=earnings.index,
                y=earnings['Revenue'] / 1e9,
                name='Ingresos',
                marker_color='#2a3f5f',
                opacity=0.7
            ),
            secondary_y=False
        )
    
    if 'Earnings' in earnings.columns and not earnings['Earnings'].empty:
        fig.add_trace(
            go.Scatter(
                x=earnings.index,
                y=earnings['Earnings'] / 1e9,
                name='Beneficio Neto',
                mode='lines+markers',
                line=dict(color='#00ffad', width=3),
                marker=dict(size=8, color='#00ffad')
            ),
            secondary_y=True
        )
    
    fig.update_layout(
        title="📈 Historial de Ingresos y Beneficios",
        template="plotly_dark",
        plot_bgcolor='#0c0e12',
        paper_bgcolor='#11141a',
        font=dict(color='white', size=10),
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    fig.update_xaxes(gridcolor='#1a1e26', showgrid=True)
    fig.update_yaxes(title_text="Ingresos (B$)", secondary_y=False, gridcolor='#1a1e26')
    fig.update_yaxes(title_text="Beneficio (B$)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

def render_earnings_calendar(data):
    """Muestra próximos earnings."""
    calendar = data.get('earnings_calendar', [])
    if not calendar:
        return
    
    st.markdown("#### 📅 Próximos Earnings")
    cols = st.columns(min(len(calendar), 3))
    for i, (col, event) in enumerate(zip(cols, calendar[:3])):
        with col:
            st.markdown(f"""
            <div style="background: #0c0e12; border: 1px solid #2a3f5f; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="color: #00ffad; font-size: 11px; font-weight: bold;">📊 Q{((datetime.now().month-1)//3)+1} {datetime.now().year}</div>
                <div style="color: white; font-size: 14px; font-weight: bold; margin: 5px 0;">{event.get('date', 'TBA')}</div>
                <div style="color: #888; font-size: 10px;">EPS Est: {event.get('eps_est', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ANÁLISIS RSU - TERMINAL HACKER STYLE
# ────────────────────────────────────────────────

def render_rsu_earnings_analysis(data):
    """Renderiza el análisis con estética terminal hacker."""
    
    base_prompt = load_rsu_prompt()
    
    if not base_prompt:
        st.warning("⚠️ Prompt RSU no encontrado.")
        return
    
    # Preparar datos de earnings trimestrales
    quarterly_str = "No disponible"
    if data.get('quarterly_earnings_hist') is not None and not data['quarterly_earnings_hist'].empty:
        try:
            q_df = data['quarterly_earnings_hist'].tail(4)  # Últimos 4 trimestres
            quarterly_str = q_df.to_string()
        except:
            quarterly_str = str(data['quarterly_earnings_hist'])
    
    # Calendario
    calendar_str = "No disponible"
    if data.get('earnings_calendar'):
        try:
            calendar_str = str(data['earnings_calendar'])
        except:
            pass
    
    # EPS Estimates
    eps_est_str = "No disponible"
    if data.get('eps_estimates'):
        try:
            eps_est_str = str(data['eps_estimates'])
        except:
            pass
    
    # Construir datos para el prompt
    datos_ticker = f"""=== DATOS DEL TICKER ===
TICKER: {data['ticker']}
COMPANY: {data['name']}
SECTOR: {data.get('sector', 'N/A')}
INDUSTRY: {data.get('industry', 'N/A')}

=== DATOS DE MERCADO ===
PRICE: ${data['price']:.2f}
CHANGE: {data.get('change_pct', 0):+.2f}%
PREV_CLOSE: ${data.get('prev_close', 0):.2f}
MARKET_CAP: {format_value(data['market_cap'], '$')}
VOLUME: {format_value(data['volume'], '', '', 0)}
AVG_VOLUME: {format_value(data['avg_volume'], '', '', 0)}
BETA: {data.get('beta', 'N/A')}
52W_RANGE: ${data.get('fifty_two_low', 0):.2f} - ${data.get('fifty_two_high', 0):.2f}
PCT_FROM_HIGH: {data.get('pct_from_high', 0):.1f}%

=== FUNDAMENTALES ===
P/E_TRAILING: {format_value(data.get('pe_trailing'), '', 'x', 2)}
P/E_FORWARD: {format_value(data.get('pe_forward'), '', 'x', 2)}
PEG_RATIO: {format_value(data.get('peg_ratio'), '', '', 2)}
PRICE_TO_SALES: {format_value(data.get('price_to_sales'), '', 'x', 2)}
PRICE_TO_BOOK: {format_value(data.get('price_to_book'), '', 'x', 2)}
EPS: ${data.get('eps', 'N/A')}
EPS_FORWARD: ${data.get('eps_forward', 'N/A')}
EPS_GROWTH: {format_value(data.get('eps_growth'), '', '%', 2)}

=== MÁRGENES ===
GROSS_MARGIN: {format_value(data.get('gross_margin'), '', '%', 2)}
OPERATING_MARGIN: {format_value(data.get('operating_margin'), '', '%', 2)}
EBITDA_MARGIN: {format_value(data.get('ebitda_margin'), '', '%', 2)}
PROFIT_MARGIN: {format_value(data.get('profit_margin'), '', '%', 2)}

=== RENTABILIDAD ===
ROE: {format_value(data.get('roe'), '', '%', 2)}
ROA: {format_value(data.get('roa'), '', '%', 2)}

=== BALANCE ===
CASH: {format_value(data.get('cash'), '$')}
DEBT: {format_value(data.get('debt'), '$')}
FREE_CASH_FLOW: {format_value(data.get('free_cashflow'), '$')}
OPERATING_CASH_FLOW: {format_value(data.get('operating_cashflow'), '$')}
DEBT_TO_EQUITY: {format_value(data.get('debt_to_equity'), '', '%', 2)}
CURRENT_RATIO: {data.get('current_ratio', 'N/A')}

=== DIVIDENDOS ===
DIVIDEND_RATE: ${data.get('dividend_rate', 0):.2f}
DIVIDEND_YIELD: {format_value(data.get('dividend_yield'), '', '%', 2)}
PAYOUT_RATIO: {format_value(data.get('payout_ratio'), '', '%', 2)}

=== CONSENSO ANALISTAS ===
RECOMMENDATION: {data.get('recommendation', 'N/A').upper()}
NUM_ANALYSTS: {data.get('num_analysts', 'N/A')}
TARGET_MEAN: ${data.get('target_mean', 0):.2f}
TARGET_HIGH: ${data.get('target_high', 0):.2f}
TARGET_LOW: ${data.get('target_low', 0):.2f}
TARGET_MEDIAN: ${data.get('target_median', 0):.2f}

=== EARNINGS TRIMESTRALES (ÚLTIMOS 4) ===
{quarterly_str}

=== CALENDARIO PROXIMO EARNINGS ===
{calendar_str}

=== EPS ESTIMATES ===
{eps_est_str}
"""
    
    prompt_completo = f"{base_prompt}\n\n{datos_ticker}\n\n=== INSTRUCCION ===\nGenera el reporte COMPLETO en español siguiendo el formato especificado. NO omitas ninguna sección. Si faltan datos, indica 'N/D' pero mantén la estructura completa."
    
    model, name, err = get_ia_model()
    
    if not model:
        st.info("🤖 IA no configurada.")
        return
    
    try:
        with st.spinner("🧠 Generando análisis..."):
            
            response = model.generate_content(
                prompt_completo,
                generation_config={
                    "temperature": 0.15,
                    "top_p": 0.95,
                    "max_output_tokens": 4000,  # Aumentado para evitar cortes
                }
            )
            
            # TERMINAL HACKER STYLE OUTPUT
            st.markdown("""
            <style>
            .terminal-box {
                background-color: #0c0e12;
                border: 1px solid #00ffad;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                margin: 20px 0;
            }
            .terminal-header {
                background: linear-gradient(90deg, #00ffad22 0%, #00ffad11 100%);
                border-bottom: 1px solid #00ffad;
                padding: 12px 16px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .terminal-title {
                color: #00ffad;
                font-size: 13px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            .terminal-ticker {
                color: #00ffad;
                font-size: 11px;
                margin-left: auto;
                opacity: 0.8;
            }
            .terminal-body {
                padding: 20px;
                color: #e0e0e0;
                line-height: 1.6;
                font-size: 13px;
            }
            .terminal-footer {
                border-top: 1px solid #2a3f5f;
                padding: 8px 16px;
                font-size: 10px;
                color: #666;
                display: flex;
                justify-content: space-between;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="terminal-box">
                <div class="terminal-header">
                    <span style="color: #00ffad;">⬤</span>
                    <span class="terminal-title">RSU Hedge Fund Analysis Terminal</span>
                    <span class="terminal-ticker">{data['ticker']} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
                <div class="terminal-body">
            """, unsafe_allow_html=True)
            
            # OUTPUT DIRECTO DEL PROMPT
            st.markdown(response.text)
            
            st.markdown(f"""
                </div>
                <div class="terminal-footer">
                    <span>Gemini Pro + Yahoo Finance API</span>
                    <span style="color: #00ffad;">RSU_TERMINAL_v1.0</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"❌ Error: {e}")

# ────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .stApp { background-color: #0c0e12; }
        .stTextInput > div > div > input { background-color: #1a1e26; color: white; border: 1px solid #2a3f5f; border-radius: 8px; }
        .stButton > button { background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%); color: #0c0e12; border: none; border-radius: 8px; font-weight: bold; }
        ::-webkit-scrollbar {
            width: 8px;
            background: #0c0e12;
        }
        ::-webkit-scrollbar-thumb {
            background: #00ffad;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #00cc8a;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📅 Análisis de Earnings")
    st.markdown('<div style="color: #888; margin-bottom: 20px;">Análisis fundamental con IA y datos en tiempo real</div>', unsafe_allow_html=True)
    
    # SIN BOTÓN DEMO - Solo input y botón analizar
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("Ticker", value="AAPL").upper().strip()
    with col2:
        st.write("")
        st.write("")
        analyze = st.button("🔍 Analizar", use_container_width=True)
    
    if analyze and ticker:
        with st.spinner("Cargando datos..."):
            raw = get_yfinance_data(ticker)
            if not raw:
                api_key = st.secrets.get("FINNHUB_API_KEY", None)
                if api_key:
                    raw = get_finnhub_data(ticker, api_key)
            
            if raw:
                data = process_data(raw, ticker)
            else:
                data = get_mock_data(ticker)
        
        if not data:
            st.error("No se pudieron obtener datos")
            return
        
        change_color = "#00ffad" if data.get('change_pct', 0) >= 0 else "#f23645"
        source_color = {"yfinance": "#00ffad", "finnhub": "#4caf50", "mock": "#ff9800"}.get(data.get('data_source'), "#888")
        source_label = {"yfinance": "YAHOO FINANCE", "finnhub": "FINNHUB", "mock": "DEMO"}.get(data.get('data_source'), "UNKNOWN")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            <div style="margin-bottom: 5px;">
                <span style="background: {source_color}22; color: {source_color}; padding: 4px 12px; border-radius: 4px; font-size: 10px; font-weight: bold; border: 1px solid {source_color};">
                    ● {source_label}
                </span>
                <span style="color: #666; font-size: 12px; margin-left: 10px;">{data.get('sector', 'N/A')} • {data.get('industry', 'N/A')}</span>
            </div>
            <h1 style="color: white; margin: 0; font-size: 2.2rem;">{data.get('name')} <span style="color: #00ffad; font-size: 1.2rem;">({ticker})</span></h1>
            <div style="color: #666; font-size: 12px; margin-top: 5px;">{data.get('country', '')} • {format_value(data.get('employees'), '', ' empleados', 0)}</div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: right;">
                <div style="color: white; font-size: 2.8rem; font-weight: 700;">${data.get('price', 0):,.2f}</div>
                <div style="color: {change_color}; font-size: 1.1rem; font-weight: 600;">{'▲' if data.get('change_pct', 0) >= 0 else '▼'} {data.get('change_pct', 0):+.2f}%</div>
                <div style="color: #666; font-size: 11px; margin-top: 5px;">Cap: {format_value(data.get('market_cap'), '$')} | Vol: {format_value(data.get('volume'), '', '', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Métricas Fundamentales")
        cols = st.columns(4)
        metrics = [
            ("Crec. Ingresos", data.get('rev_growth'), True),
            ("Margen EBITDA", data.get('ebitda_margin'), True),
            ("ROE", data.get('roe'), True),
            ("P/E Forward", data.get('pe_forward'), False),
        ]
        for col, (label, value, is_pct) in zip(cols, metrics):
            with col:
                if is_pct and value is not None:
                    formatted, color = format_pct(value)
                else:
                    formatted = format_value(value, '', 'x' if 'P/E' in label else '', 1)
                    color = "#00ffad" if value else "#888"
                st.markdown(f"""
                <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 18px; text-align: center;">
                    <div style="color: #666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">{label}</div>
                    <div style="color: {color}; font-size: 1.4rem; font-weight: bold;">{formatted}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        col_chart, col_info = st.columns([3, 2])
        
        with col_chart:
            if not data.get('hist', pd.DataFrame()).empty:
                hist = data['hist']
                fig = go.Figure(data=[go.Candlestick(
                    x=hist.index, open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'],
                    increasing_line_color='#00ffad', decreasing_line_color='#f23645'
                )])
                fig.update_layout(
                    template="plotly_dark", plot_bgcolor='#0c0e12', paper_bgcolor='#11141a',
                    font=dict(color='white'), xaxis_rangeslider_visible=False,
                    height=350, margin=dict(l=30, r=30, t=30, b=30),
                    title="Precio (6 meses)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Gráfico de precio no disponible")
        
        with col_info:
            st.markdown("#### 📋 Sobre la Empresa")
            st.markdown(f"<div style='color: #aaa; font-size: 13px; line-height: 1.6;'>{data.get('summary', 'N/A')[:300]}...</div>", unsafe_allow_html=True)
            
            st.markdown("#### 💰 Métricas Clave")
            st.markdown(f"""
            <div style="background: #0c0e12; border-radius: 8px; padding: 15px; border: 1px solid #1a1e26; font-size: 12px; line-height: 2;">
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">Cash:</span> <span style="color: #00ffad; font-weight: bold;">{format_value(data.get('cash'), '$')}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">Deuda:</span> <span style="color: #f23645; font-weight: bold;">{format_value(data.get('debt'), '$')}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">FCF:</span> <span style="color: {'#00ffad' if (data.get('free_cashflow') or 0) > 0 else '#f23645'}; font-weight: bold;">{format_value(data.get('free_cashflow'), '$')}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">Beta:</span> <span style="color: white; font-weight: bold;">{data.get('beta', 0):.2f}</span></div>
                <div style="display: flex; justify-content: space-between;"><span style="color: #666;">52S vs Max:</span> <span style="color: {'#00ffad' if data.get('pct_from_high', 0) > -10 else '#f23645'}; font-weight: bold;">{data.get('pct_from_high', 0):.1f}%</span></div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        render_earnings_chart(data)
        render_earnings_calendar(data)
        
        st.markdown("---")
        st.markdown("### 🔮 Perspectivas y Desafíos")
        
        positive, challenges = generate_outlook_points(data)
        
        col_pos, col_chal = st.columns(2)
        with col_pos:
            points_html = "".join([f"<li style='margin-bottom: 12px; padding-left: 10px; border-left: 3px solid #00ffad;'>{p}</li>" for p in positive])
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(0,255,173,0.08) 0%, rgba(0,255,173,0.02) 100%); border: 1px solid #00ffad33; border-radius: 12px; padding: 25px; height: 100%;">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div style="width: 36px; height: 36px; background: #00ffad22; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 18px;">📈</div>
                    <h3 style="color: #00ffad; margin: 0; font-size: 1.1rem;">Perspectivas Positivas</h3>
                </div>
                <ul style="color: #ccc; line-height: 1.6; padding-left: 0; list-style: none; margin: 0;">
                    {points_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col_chal:
            points_html = "".join([f"<li style='margin-bottom: 12px; padding-left: 10px; border-left: 3px solid #f23645;'>{c}</li>" for c in challenges])
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(242,54,69,0.08) 0%, rgba(242,54,69,0.02) 100%); border: 1px solid #f2364533; border-radius: 12px; padding: 25px; height: 100%;">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div style="width: 36px; height: 36px; background: #f2364522; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 18px;">⚠️</div>
                    <h3 style="color: #f23645; margin: 0; font-size: 1.1rem;">Desafíos Pendientes</h3>
                </div>
                <ul style="color: #ccc; line-height: 1.6; padding-left: 0; list-style: none; margin: 0;">
                    {points_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        render_rsu_earnings_analysis(data)
        
        # FOOTER SIN CITAS ALEATORIAS
        st.markdown(f"""
        <div style="text-align: center; color: #444; font-size: 11px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #1a1e26;">
            Datos proporcionados por Yahoo Finance & Finnhub | Análisis generado por IA Gemini<br>
            <span style="color: #00ffad;">RSU Dashboard Pro</span> • Para fines informativos únicamente
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()

