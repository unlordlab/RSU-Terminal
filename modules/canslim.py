# -*- coding: utf-8 -*-
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import streamlit.components.v1 as components
from config import get_market_index

def get_timestamp():
    return datetime.now().strftime('%H:%M:%S')

@st.cache_data(ttl=300)
def get_canslim_candidates():
    try:
        growth_stocks = [
            'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'AVGO', 'NFLX', 'AMD',
            'CRM', 'ADBE', 'PLTR', 'PANW', 'SNOW', 'DDOG', 'CRWD', 'NET', 'OKTA', 'ZS',
            'ENPH', 'SEDG', 'FSLR', 'RUN', 'NOVA', 'SPWR', 'SOL', 'NEE', 'DUK', 'SO',
            'UNH', 'LLY', 'JNJ', 'PFE', 'MRK', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY',
            'V', 'MA', 'AXP', 'PYPL', 'SQ', 'COIN', 'HOOD', 'SOFI', 'AFRM', 'UPST',
            'COST', 'WMT', 'HD', 'LOW', 'TGT', 'DG', 'DLTR', 'ROST', 'TJX', 'BURL'
        ]

        candidates = []

        for ticker in growth_stocks[:30]:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="1y")

                if len(hist) < 50:
                    continue

                market_cap = info.get('marketCap', 0) / 1e9
                revenue_growth = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0
                earnings_growth = info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0
                eps_growth = info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0

                current_price = hist['Close'].iloc[-1]
                high_52w = hist['High'].max()
                pct_from_high = ((current_price - high_52w) / high_52w) * 100

                avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
                current_volume = hist['Volume'].iloc[-1]
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

                spy = yf.Ticker("SPY").history(period="1y")
                stock_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
                spy_return = (spy['Close'].iloc[-1] / spy['Close'].iloc[0] - 1) * 100
                rs_rating = 50 + (stock_return - spy_return) * 2
                rs_rating = max(0, min(100, rs_rating))

                inst_ownership = info.get('heldPercentInstitutions', 0) * 100 if info.get('heldPercentInstitutions') else 0

                score = 0
                if earnings_growth > 25: score += 20
                elif earnings_growth > 15: score += 15
                elif earnings_growth > 0: score += 10

                if revenue_growth > 20: score += 15
                elif revenue_growth > 10: score += 10
                elif revenue_growth > 0: score += 5

                if eps_growth > 25: score += 15
                elif eps_growth > 15: score += 10

                if pct_from_high > -10: score += 15
                elif pct_from_high > -20: score += 10

                if rs_rating > 80: score += 15
                elif rs_rating > 60: score += 10
                elif rs_rating > 40: score += 5

                if volume_ratio > 1.5: score += 10
                elif volume_ratio > 1.0: score += 5

                if inst_ownership > 50: score += 10
                elif inst_ownership > 30: score += 5

                if score >= 40 and market_cap > 1:
                    candidates.append({
                        'ticker': ticker,
                        'name': info.get('shortName', ticker),
                        'sector': info.get('sector', 'N/A'),
                        'market_cap': market_cap,
                        'price': current_price,
                        'score': score,
                        'earnings_growth': earnings_growth,
                        'revenue_growth': revenue_growth,
                        'rs_rating': rs_rating,
                        'pct_from_high': pct_from_high,
                        'volume_ratio': volume_ratio,
                        'inst_ownership': inst_ownership,
                        'c_grade': 'A' if earnings_growth > 25 else 'B' if earnings_growth > 15 else 'C',
                        'a_grade': 'A' if eps_growth > 25 else 'B' if eps_growth > 15 else 'C',
                        'n_grade': 'A' if pct_from_high > -5 else 'B' if pct_from_high > -15 else 'C',
                        's_grade': 'A' if volume_ratio > 1.5 else 'B' if volume_ratio > 1.0 else 'C',
                        'l_grade': 'A' if rs_rating > 80 else 'B' if rs_rating > 60 else 'C',
                        'i_grade': 'A' if inst_ownership > 60 else 'B' if inst_ownership > 40 else 'C'
                    })
            except:
                continue

        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:15]
    except:
        return get_fallback_candidates()

def get_fallback_candidates():
    return [
        {'ticker': 'NVDA', 'name': 'NVIDIA Corp', 'sector': 'Technology', 'market_cap': 3200, 'price': 875.50, 'score': 92, 'earnings_growth': 265, 'revenue_growth': 206, 'rs_rating': 95, 'pct_from_high': -2.5, 'volume_ratio': 1.8, 'inst_ownership': 68, 'c_grade': 'A', 'a_grade': 'A', 'n_grade': 'A', 's_grade': 'A', 'l_grade': 'A', 'i_grade': 'A'},
        {'ticker': 'META', 'name': 'Meta Platforms', 'sector': 'Technology', 'market_cap': 1200, 'price': 485.20, 'score': 88, 'earnings_growth': 168, 'revenue_growth': 25, 'rs_rating': 88, 'pct_from_high': -1.2, 'volume_ratio': 1.4, 'inst_ownership': 65, 'c_grade': 'A', 'a_grade': 'A', 'n_grade': 'A', 's_grade': 'B', 'l_grade': 'A', 'i_grade': 'A'},
        {'ticker': 'LLY', 'name': 'Eli Lilly', 'sector': 'Healthcare', 'market_cap': 720, 'price': 725.80, 'score': 85, 'earnings_growth': 68, 'revenue_growth': 28, 'rs_rating': 92, 'pct_from_high': -3.1, 'volume_ratio': 1.2, 'inst_ownership': 82, 'c_grade': 'A', 'a_grade': 'A', 'n_grade': 'A', 's_grade': 'B', 'l_grade': 'A', 'i_grade': 'A'},
        {'ticker': 'AVGO', 'name': 'Broadcom Inc', 'sector': 'Technology', 'market_cap': 680, 'price': 1450.30, 'score': 82, 'earnings_growth': 42, 'revenue_growth': 34, 'rs_rating': 85, 'pct_from_high': -5.8, 'volume_ratio': 1.6, 'inst_ownership': 78, 'c_grade': 'A', 'a_grade': 'A', 'n_grade': 'B', 's_grade': 'A', 'l_grade': 'A', 'i_grade': 'A'},
        {'ticker': 'NFLX', 'name': 'Netflix Inc', 'sector': 'Technology', 'market_cap': 310, 'price': 715.40, 'score': 78, 'earnings_growth': 52, 'revenue_growth': 15, 'rs_rating': 82, 'pct_from_high': -4.2, 'volume_ratio': 1.3, 'inst_ownership': 80, 'c_grade': 'A', 'a_grade': 'A', 'n_grade': 'A', 's_grade': 'B', 'l_grade': 'A', 'i_grade': 'A'},
        {'ticker': 'AMD', 'name': 'AMD Inc', 'sector': 'Technology', 'market_cap': 280, 'price': 175.20, 'score': 75, 'earnings_growth': 32, 'revenue_growth': 17, 'rs_rating': 78, 'pct_from_high': -12.5, 'volume_ratio': 1.5, 'inst_ownership': 72, 'c_grade': 'A', 'a_grade': 'B', 'n_grade': 'C', 's_grade': 'A', 'l_grade': 'B', 'i_grade': 'A'},
    ]

@st.cache_data(ttl=600)
def get_breakout_stocks():
    candidates = get_canslim_candidates()
    breakouts = [c for c in candidates if c['pct_from_high'] > -5 and c['volume_ratio'] > 1.2]
    return breakouts[:6]

@st.cache_data(ttl=600)
def get_can_slim_leaders():
    candidates = get_canslim_candidates()
    sectors = {}
    for c in candidates:
        sector = c['sector']
        if sector not in sectors or c['score'] > sectors[sector]['score']:
            sectors[sector] = c
    return list(sectors.values())[:6]

def get_grade_color(grade):
    colors = {'A': '#00ffad', 'B': '#ff9800', 'C': '#f23645', 'N/A': '#666'}
    return colors.get(grade, '#666')

def get_score_color(score):
    if score >= 80: return '#00ffad'
    elif score >= 60: return '#ff9800'
    else: return '#f23645'

def render():
    st.markdown("""
    <style>
    .tooltip-wrapper {
        position: relative;
        display: inline-block;
    }
    .tooltip-btn {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #1a1e26;
        border: 2px solid #555;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #aaa;
        font-size: 14px;
        font-weight: bold;
        cursor: help;
        position: relative;
    }
    .tooltip-content {
        display: none;
        position: fixed;
        width: 300px;
        background-color: #1e222d;
        color: #eee;
        text-align: left;
        padding: 12px 14px;
        border-radius: 8px;
        z-index: 99999;
        font-size: 12px;
        border: 1px solid #444;
        box-shadow: 0 8px 30px rgba(0,0,0,0.8);
        line-height: 1.4;
    }
    .tooltip-wrapper:hover .tooltip-content {
        display: block;
    }
    .update-timestamp {
        text-align: center;
        color: #555;
        font-size: 10px;
        padding: 6px 0;
        font-family: 'Courier New', monospace;
        border-top: 1px solid #1a1e26;
        background: #0c0e12;
        flex-shrink: 0;
    }
    .module-container { 
        border: 1px solid #1a1e26; 
        border-radius: 10px; 
        overflow: hidden; 
        background: #11141a; 
        height: 340px;
        display: flex;
        flex-direction: column;
        margin-bottom: 0;
    }
    .module-header { 
        background: #0c0e12; 
        padding: 10px 12px; 
        border-bottom: 1px solid #1a1e26; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        flex-shrink: 0;
    }
    .module-title { 
        margin: 0; 
        color: white; 
        font-size: 13px; 
        font-weight: bold; 
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .module-content { 
        flex: 1;
        overflow-y: auto;
        padding: 10px;
    }
    .canslim-card {
        background: #0c0e12;
        border: 1px solid #1a1e26;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 8px;
        transition: all 0.2s;
    }
    .canslim-card:hover {
        border-color: #2a3f5f;
        background: #14161d;
    }
    .canslim-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .canslim-ticker {
        color: #00ffad;
        font-weight: bold;
        font-size: 14px;
    }
    .canslim-name {
        color: #888;
        font-size: 9px;
        margin-left: 6px;
    }
    .canslim-score {
        font-size: 18px;
        font-weight: bold;
    }
    .canslim-grades {
        display: flex;
        gap: 4px;
        margin-top: 6px;
    }
    .grade-badge {
        width: 22px;
        height: 22px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: bold;
        border: 1px solid;
    }
    .grade-label {
        font-size: 7px;
        color: #555;
        text-align: center;
        margin-top: 2px;
    }
    .canslim-metrics {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 4px;
        margin-top: 6px;
        font-size: 9px;
    }
    .metric-item {
        color: #888;
    }
    .metric-value {
        color: white;
        font-weight: bold;
    }
    .breakout-badge {
        background: linear-gradient(135deg, #00ffad22, #00ffad11);
        border: 1px solid #00ffad44;
        color: #00ffad;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 8px;
        font-weight: bold;
    }
    .stColumns {
        gap: 0.5rem !important;
    }
    .stColumn {
        padding: 0 0.25rem !important;
    }
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    .canslim-legend {
        display: flex;
        justify-content: space-around;
        padding: 8px;
        background: #0c0e12;
        border-radius: 6px;
        margin-top: 8px;
    }
    .legend-item {
        text-align: center;
    }
    .legend-letter {
        font-size: 12px;
        font-weight: bold;
        color: white;
    }
    .legend-desc {
        font-size: 7px;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 style="margin-top:15px; text-align:center; margin-bottom:5px; font-size: 1.8rem;">🎯 CAN SLIM Scanner</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#888; font-size:12px; margin-bottom:20px;">Estrategia de Inversión de William O'Neil</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        canslim_explained = """
        <div style="background:#0c0e12; padding:12px; border-radius:8px; border:1px solid #1a1e26; height:100%;">
            <div style="color:#00ffad; font-weight:bold; font-size:12px; margin-bottom:8px;">📋 Los 7 Criterios CAN SLIM</div>
            <div style="font-size:10px; color:#ccc; line-height:1.6;">
                <b style="color:#fff;">C</b> - Current Qtr Earnings &gt;25%<br>
                <b style="color:#fff;">A</b> - Annual Earnings Growth &gt;25%<br>
                <b style="color:#fff;">N</b> - New Products/Mgmt/Highs<br>
                <b style="color:#fff;">S</b> - Supply & Demand (Volume)<br>
                <b style="color:#fff;">L</b> - Leader or Laggard (RS)<br>
                <b style="color:#fff;">I</b> - Institutional Sponsorship<br>
                <b style="color:#fff;">M</b> - Market Direction (Timing)
            </div>
        </div>
        """
        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">CAN SLIM Guide</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">Sistema de selección de acciones de William O'Neil para encontrar growth stocks en mercados alcistas.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 12px;">{canslim_explained}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        spy_val, spy_change = get_market_index("^GSPC")
        qq_val, qq_change = get_market_index("^IXIC")

        market_status = "BULLISH" if spy_change > 0 and qq_change > 0 else "BEARISH" if spy_change < -1 and qq_change < -1 else "MIXED"
        status_color = "#00ffad" if market_status == "BULLISH" else "#f23645" if market_status == "BEARISH" else "#ff9800"

        market_html = f'''
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
            <div style="font-size:3.5rem; font-weight:bold; color:{status_color};">{market_status}</div>
            <div style="color:white; font-size:1rem; font-weight:bold; margin:8px 0;">Market Direction</div>
            <div style="background:#0c0e12; padding:10px 16px; border-radius:6px; border:1px solid #1a1e26; width:90%; margin-top:10px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="color:#888; font-size:10px;">S&P 500</span>
                    <span style="color:{'#00ffad' if spy_change >=0 else '#f23645'}; font-size:10px; font-weight:bold;">{spy_change:+.2f}%</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#888; font-size:10px;">NASDAQ</span>
                    <span style="color:{'#00ffad' if qq_change >=0 else '#f23645'}; font-size:10px; font-weight:bold;">{qq_change:+.2f}%</span>
                </div>
            </div>
            <div style="color:#555; font-size:9px; margin-top:15px; text-align:center; line-height:1.4;">
                M = Market Direction<br>
                Solo operar en mercados alcistas confirmados
            </div>
        </div>
        '''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">M - Market Direction</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">El factor M es crucial: solo comprar acciones CAN SLIM cuando el mercado general está en tendencia alcista confirmada.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 15px;">{market_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        candidates = get_canslim_candidates()

        if candidates:
            avg_score = sum(c['score'] for c in candidates) / len(candidates)
            high_scores = len([c for c in candidates if c['score'] >= 80])
            avg_rs = sum(c['rs_rating'] for c in candidates) / len(candidates)

            stats_html = f'''
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; height:100%;">
                <div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:12px; text-align:center;">
                    <div style="color:#00ffad; font-size:24px; font-weight:bold;">{len(candidates)}</div>
                    <div style="color:#888; font-size:9px;">Candidatos</div>
                </div>
                <div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:12px; text-align:center;">
                    <div style="color:#00ffad; font-size:24px; font-weight:bold;">{avg_score:.0f}</div>
                    <div style="color:#888; font-size:9px;">Score Medio</div>
                </div>
                <div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:12px; text-align:center;">
                    <div style="color:#00ffad; font-size:24px; font-weight:bold;">{high_scores}</div>
                    <div style="color:#888; font-size:9px;">Score &gt;80</div>
                </div>
                <div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:12px; text-align:center;">
                    <div style="color:#00ffad; font-size:24px; font-weight:bold;">{avg_rs:.0f}</div>
                    <div style="color:#888; font-size:9px;">RS Medio</div>
                </div>
            </div>
            <div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:8px; margin-top:8px; text-align:center;">
                <div style="color:#888; font-size:9px;">Mejor Candidato</div>
                <div style="color:#00ffad; font-size:14px; font-weight:bold;">{candidates[0]['ticker']} - Score {candidates[0]['score']}</div>
            </div>
            '''
        else:
            stats_html = '<div style="color:#888; text-align:center; padding:20px;">No hay datos disponibles</div>'

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Scanner Stats</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">Estadísticas del universo de acciones analizadas con criterios CAN SLIM.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 10px;">{stats_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.write("")
    col1, col2 = st.columns([2, 1])

    with col1:
        candidates = get_canslim_candidates()

        candidates_html = ""
        for c in candidates[:8]:
            score_color = get_score_color(c['score'])

            grades_html = ""
            for letter, grade in [('C', c['c_grade']), ('A', c['a_grade']), ('N', c['n_grade']), 
                                  ('S', c['s_grade']), ('L', c['l_grade']), ('I', c['i_grade'])]:
                grade_color = get_grade_color(grade)
                grades_html += f'''<div>
                    <div class="grade-badge" style="color:{grade_color}; border-color:{grade_color}44; background:{grade_color}11;">{grade}</div>
                    <div class="grade-label">{letter}</div>
                </div>'''

            breakout_badge = ""
            if c['pct_from_high'] > -3 and c['volume_ratio'] > 1.3:
                breakout_badge = '<span class="breakout-badge">BREAKOUT</span>'

            eg_color = '#00ffad' if c['earnings_growth'] > 25 else '#ff9800' if c['earnings_growth'] > 0 else '#f23645'
            rg_color = '#00ffad' if c['revenue_growth'] > 20 else '#ff9800' if c['revenue_growth'] > 0 else '#f23645'
            rs_color = '#00ffad' if c['rs_rating'] > 80 else '#ff9800' if c['rs_rating'] > 60 else '#f23645'
            fh_color = '#00ffad' if c['pct_from_high'] > -5 else '#ff9800' if c['pct_from_high'] > -15 else '#f23645'

            candidates_html += f'''<div class="canslim-card">
                <div class="canslim-header">
                    <div>
                        <span class="canslim-ticker">{c['ticker']}</span>
                        <span class="canslim-name">{c['name'][:25]}</span>
                        {breakout_badge}
                    </div>
                    <div class="canslim-score" style="color:{score_color};">{c['score']}</div>
                </div>
                <div class="canslim-grades">
                    {grades_html}
                </div>
                <div class="canslim-metrics">
                    <div class="metric-item">EPS Growth: <span class="metric-value" style="color:{eg_color};">{c['earnings_growth']:.1f}%</span></div>
                    <div class="metric-item">Rev Growth: <span class="metric-value" style="color:{rg_color};">{c['revenue_growth']:.1f}%</span></div>
                    <div class="metric-item">RS Rating: <span class="metric-value" style="color:{rs_color};">{c['rs_rating']:.0f}</span></div>
                    <div class="metric-item">From High: <span class="metric-value" style="color:{fh_color};">{c['pct_from_high']:.1f}%</span></div>
                </div>
            </div>'''

        st.markdown(f'''
        <div class="module-container" style="height: 400px;">
            <div class="module-header">
                <div class="module-title">🏆 Top CAN SLIM Candidates</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">Acciones ordenadas por score CAN SLIM. Cada letra representa la calificación del criterio correspondiente.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 10px;">{candidates_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        breakouts = get_breakout_stocks()

        breakouts_html = ""
        for b in breakouts:
            breakouts_html += f'''<div style="background:#0c0e12; border:1px solid #00ffad33; border-radius:6px; padding:10px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <span style="color:#00ffad; font-weight:bold; font-size:12px;">{b['ticker']}</span>
                    <span style="color:#00ffad; font-size:10px; font-weight:bold;">🔥 BREAKOUT</span>
                </div>
                <div style="color:#888; font-size:9px; margin-bottom:4px;">{b['name'][:20]}</div>
                <div style="display:flex; justify-content:space-between; font-size:9px;">
                    <span style="color:#666;">Score: <span style="color:white; font-weight:bold;">{b['score']}</span></span>
                    <span style="color:#666;">Vol: <span style="color:#00ffad; font-weight:bold;">{b['volume_ratio']:.1f}x</span></span>
                </div>
                <div style="margin-top:4px; font-size:8px; color:#555;">
                    {b['pct_from_high']:.1f}% from high | RS {b['rs_rating']:.0f}
                </div>
            </div>'''

        st.markdown(f'''
        <div class="module-container" style="height: 400px;">
            <div class="module-header">
                <div class="module-title">🚀 Breakouts</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">Acciones cerca de máximos históricos con volumen elevado. Señal de entrada potencial.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 10px;">{breakouts_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.write("")
    col1, col2, col3 = st.columns(3)

    with col1:
        leaders = get_can_slim_leaders()

        leaders_html = ""
        for l in leaders:
            leaders_html += f'''<div style="background:#0c0e12; border:1px solid #1a1e26; border-radius:6px; padding:8px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color:#00ffad; font-weight:bold; font-size:11px;">{l['ticker']}</div>
                    <div style="color:#666; font-size:8px;">{l['sector'][:15]}</div>
                </div>
                <div style="text-align:right;">
                    <div style="color:white; font-weight:bold; font-size:12px;">{l['score']}</div>
                    <div style="color:#888; font-size:8px;">Score</div>
                </div>
            </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">L - Sector Leaders</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">Líderes CAN SLIM por sector. Buscar las acciones #1 de cada industria.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 10px;">{leaders_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        candidates = get_canslim_candidates()
        high_earnings = [c for c in candidates if c['earnings_growth'] > 50]

        c_analysis_html = f'''<div style="text-align:center; padding:10px;">
            <div style="font-size:2.5rem; font-weight:bold; color:#00ffad;">{len(high_earnings)}</div>
            <div style="color:#888; font-size:10px; margin-bottom:10px;">con EPS Growth &gt;50%</div>
            <div style="background:#0c0e12; border-radius:6px; padding:8px; text-align:left;">
                <div style="color:#888; font-size:9px; margin-bottom:6px;">Top C - Current Earnings:</div>'''

        for c in sorted(candidates, key=lambda x: x['earnings_growth'], reverse=True)[:4]:
            c_analysis_html += f'''<div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color:#00ffad; font-size:10px; font-weight:bold;">{c['ticker']}</span>
                <span style="color:white; font-size:10px;">{c['earnings_growth']:.1f}%</span>
            </div>'''

        c_analysis_html += '</div></div>'

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">C - Current Earnings</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">Crecimiento trimestral de beneficios. Buscar &gt;25%, idealmente &gt;50%.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 10px;">{c_analysis_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        candidates = get_canslim_candidates()
        strong_rs = [c for c in candidates if c['rs_rating'] > 85]

        l_analysis_html = f'''<div style="text-align:center; padding:10px;">
            <div style="font-size:2.5rem; font-weight:bold; color:#00ffad;">{len(strong_rs)}</div>
            <div style="color:#888; font-size:10px; margin-bottom:10px;">con RS Rating &gt;85</div>
            <div style="background:#0c0e12; border-radius:6px; padding:8px; text-align:left;">
                <div style="color:#888; font-size:9px; margin-bottom:6px;">Top L - Relative Strength:</div>'''

        for c in sorted(candidates, key=lambda x: x['rs_rating'], reverse=True)[:4]:
            l_analysis_html += f'''<div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color:#00ffad; font-size:10px; font-weight:bold;">{c['ticker']}</span>
                <span style="color:white; font-size:10px;">{c['rs_rating']:.0f}</span>
            </div>'''

        l_analysis_html += '</div></div>'

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">L - RS Rating</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">Relative Strength. Comparación del rendimiento vs el mercado general. Buscar &gt;80.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 10px;">{l_analysis_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("""
    <div class="canslim-legend">
        <div class="legend-item">
            <div class="legend-letter" style="color:#00ffad;">C</div>
            <div class="legend-desc">Current<br>Quarterly</div>
        </div>
        <div class="legend-item">
            <div class="legend-letter" style="color:#00ffad;">A</div>
            <div class="legend-desc">Annual<br>Earnings</div>
        </div>
        <div class="legend-item">
            <div class="legend-letter" style="color:#00ffad;">N</div>
            <div class="legend-desc">New<br>Products</div>
        </div>
        <div class="legend-item">
            <div class="legend-letter" style="color:#00ffad;">S</div>
            <div class="legend-desc">Supply &<br>Demand</div>
        </div>
        <div class="legend-item">
            <div class="legend-letter" style="color:#00ffad;">L</div>
            <div class="legend-desc">Leader or<br>Laggard</div>
        </div>
        <div class="legend-item">
            <div class="legend-letter" style="color:#00ffad;">I</div>
            <div class="legend-desc">Institutional<br>Sponsorship</div>
        </div>
        <div class="legend-item">
            <div class="legend-letter" style="color:#00ffad;">M</div>
            <div class="legend-desc">Market<br>Direction</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
