# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from config import get_market_index

def get_timestamp():
    return datetime.now().strftime('%H:%M:%S')

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
    }
    .tooltip-wrapper:hover .tooltip-content {
        display: block;
    }
    .module-container { 
        border: 1px solid #1a1e26; 
        border-radius: 10px; 
        overflow: hidden; 
        background: #11141a; 
        height: 340px;
        display: flex;
        flex-direction: column;
    }
    .module-header { 
        background: #0c0e12; 
        padding: 10px 12px; 
        border-bottom: 1px solid #1a1e26; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
    }
    .module-title { 
        margin: 0; 
        color: white; 
        font-size: 13px; 
        font-weight: bold; 
        text-transform: uppercase;
    }
    .module-content { 
        flex: 1;
        overflow-y: auto;
        padding: 10px;
    }
    .update-timestamp {
        text-align: center;
        color: #555;
        font-size: 10px;
        padding: 6px 0;
        font-family: 'Courier New', monospace;
        border-top: 1px solid #1a1e26;
        background: #0c0e12;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 style="margin-top:15px; text-align:center; margin-bottom:15px; font-size: 1.8rem;">🗄️ RSU Database</h1>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Watchlist</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">Lista de seguimiento personalizada.</div>
                </div>
            </div>
            <div class="module-content">
                <div style="color:#888; text-align:center; padding:20px;">Módulo en desarrollo</div>
            </div>
            <div class="update-timestamp">Updated: ''' + get_timestamp() + '''</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown('''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Historial</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">Historial de operaciones.</div>
                </div>
            </div>
            <div class="module-content">
                <div style="color:#888; text-align:center; padding:20px;">Módulo en desarrollo</div>
            </div>
            <div class="update-timestamp">Updated: ''' + get_timestamp() + '''</div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        st.markdown('''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Análisis</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content" style="top: 50px; right: 20px;">Análisis de rendimiento.</div>
                </div>
            </div>
            <div class="module-content">
                <div style="color:#888; text-align:center; padding:20px;">Módulo en desarrollo</div>
            </div>
            <div class="update-timestamp">Updated: ''' + get_timestamp() + '''</div>
        </div>
        ''', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
