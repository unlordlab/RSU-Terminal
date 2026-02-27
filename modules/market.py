    # === REDDIT SOCIAL PULSE MEJORADO - MASTER BUZZ (DISEÑO VISUAL) ===
    with col3:
        master_data = get_buzztickr_master_data()
        buzz_items = master_data.get('data', [])
        
        cards_html = ""
        
        for item in buzz_items[:10]:
            rank = str(item.get('rank', '-'))
            ticker = str(item.get('ticker', '-'))
            buzz_score = str(item.get('buzz_score', '-'))
            health = str(item.get('health', '-'))
            smart_money = str(item.get('smart_money', ''))
            squeeze = str(item.get('squeeze', ''))
            
            # Color de rank
            try:
                rank_num = int(rank)
                if rank_num <= 3:
                    rank_bg = "#f23645"
                    rank_color = "white"
                    glow = "box-shadow: 0 0 10px rgba(242, 54, 69, 0.3);"
                else:
                    rank_bg = "#1a1e26"
                    rank_color = "#888"
                    glow = ""
            except:
                rank_bg = "#1a1e26"
                rank_color = "#888"
                glow = ""
            
            # Parsear health (número + texto)
            health_num = "50"
            health_text = "NEUTRAL"
            health_color = "#ff9800"
            health_bg = "#ff980022"
            
            health_parts = health.split()
            if len(health_parts) >= 1:
                health_num = health_parts[0]
            if len(health_parts) >= 2:
                health_text = health_parts[1].upper()
            
            if 'strong' in health.lower():
                health_color = "#00ffad"
                health_bg = "#00ffad15"
            elif 'weak' in health.lower():
                health_color = "#f23645"
                health_bg = "#f2364515"
            
            # Procesar Smart Money
            has_smart = bool(smart_money and 'whales' in smart_money.lower())
            smart_icon = "🐋" if has_smart else "○"
            smart_color = "#00ffad" if has_smart else "#333"
            smart_text = "SMART $" if has_smart else "—"
            
            # Procesar Squeeze
            has_squeeze = bool(squeeze and ('short' in squeeze.lower() or 'squeeze' in squeeze.lower()))
            squeeze_icon = "🧨" if has_squeeze else "○"
            squeeze_color = "#f23645" if has_squeeze else "#333"
            
            # Extraer porcentaje de short interest si existe
            squeeze_pct = ""
            if has_squeeze:
                import re
                pct_match = re.search(r'(\d+\.?\d*)%', squeeze)
                if pct_match:
                    squeeze_pct = f"{pct_match.group(1)}%"
            
            # Barra de buzz score (0-10)
            try:
                score_val = int(buzz_score)
                score_width = (score_val / 10) * 100
            except:
                score_width = 50
            
            cards_html += f"""
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 10px; margin-bottom: 8px; {glow}">
                <!-- Header: Rank + Ticker + Score -->
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <div style="width: 26px; height: 26px; border-radius: 50%; background: {rank_bg}; color: {rank_color}; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 11px; flex-shrink: 0;">
                        {rank}
                    </div>
                    <div style="flex: 1;">
                        <div style="color: #00ffad; font-weight: bold; font-size: 14px; letter-spacing: 0.5px;">${ticker}</div>
                        <div style="display: flex; align-items: center; gap: 6px; margin-top: 2px;">
                            <div style="flex: 1; height: 4px; background: #1a1e26; border-radius: 2px; overflow: hidden;">
                                <div style="width: {score_width}%; height: 100%; background: linear-gradient(90deg, #00ffad, #00cc8a);"></div>
                            </div>
                            <span style="color: #888; font-size: 10px; font-weight: bold;">{buzz_score}/10</span>
                        </div>
                    </div>
                </div>
                
                <!-- Métricas en fila -->
                <div style="display: flex; gap: 8px;">
                    <!-- Health Badge -->
                    <div style="flex: 1; background: {health_bg}; border: 1px solid {health_color}30; border-radius: 6px; padding: 6px; text-align: center;">
                        <div style="font-size: 8px; color: #666; text-transform: uppercase; margin-bottom: 2px;">Health</div>
                        <div style="color: {health_color}; font-weight: bold; font-size: 11px;">{health_num}</div>
                        <div style="color: {health_color}; font-size: 8px; opacity: 0.8;">{health_text}</div>
                    </div>
                    
                    <!-- Smart Money -->
                    <div style="flex: 1; background: #0f1218; border: 1px solid {smart_color}30; border-radius: 6px; padding: 6px; text-align: center;">
                        <div style="font-size: 8px; color: #666; text-transform: uppercase; margin-bottom: 2px;">Smart $</div>
                        <div style="color: {smart_color}; font-size: 14px;">{smart_icon}</div>
                        <div style="color: {smart_color}; font-size: 8px; margin-top: 1px;">{smart_text}</div>
                    </div>
                    
                    <!-- Squeeze -->
                    <div style="flex: 1; background: #0f1218; border: 1px solid {squeeze_color}30; border-radius: 6px; padding: 6px; text-align: center;">
                        <div style="font-size: 8px; color: #666; text-transform: uppercase; margin-bottom: 2px;">Squeeze</div>
                        <div style="color: {squeeze_color}; font-size: 14px;">{squeeze_icon}</div>
                        <div style="color: {squeeze_color}; font-size: 8px; margin-top: 1px;">{squeeze_pct if squeeze_pct else '—'}</div>
                    </div>
                </div>
            </div>
            """
        
        # Stats footer
        count = master_data.get('count', 0)
        source = master_data.get('source', 'API')
        timestamp = master_data.get('timestamp', get_timestamp())
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #11141a; }}
        
        .module-container {{ 
            border: 1px solid #1a1e26; 
            border-radius: 10px; 
            overflow: hidden; 
            background: #11141a; 
            height: 420px;
            display: flex;
            flex-direction: column;
        }}
        .module-header {{ 
            background: #0c0e12; 
            padding: 10px 12px; 
            border-bottom: 1px solid #1a1e26; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }}
        .module-title {{ 
            margin: 0; 
            color: white; 
            font-size: 13px; 
            font-weight: bold; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .module-content {{ 
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }}
        .update-timestamp {{
            text-align: center;
            color: #555;
            font-size: 10px;
            padding: 6px 0;
            font-family: 'Courier New', monospace;
            border-top: 1px solid #1a1e26;
            background: #0c0e12;
        }}
        
        /* Scrollbar styling */
        .module-content::-webkit-scrollbar {{
            width: 6px;
        }}
        .module-content::-webkit-scrollbar-track {{
            background: #0c0e12;
        }}
        .module-content::-webkit-scrollbar-thumb {{
            background: #2a3f5f;
            border-radius: 3px;
        }}
        
        /* Tooltip */
        .tooltip-wrapper {{
            position: relative;
            display: inline-block;
        }}
        .tooltip-btn {{
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
        }}
        .tooltip-content {{
            display: none;
            position: absolute;
            right: 0;
            top: 30px;
            width: 220px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 12px;
            border-radius: 8px;
            z-index: 1000;
            font-size: 11px;
            border: 1px solid #3b82f6;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
        }}
        .tooltip-wrapper:hover .tooltip-content {{
            display: block;
        }}
        
        /* Live badge pulse */
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
        .live-badge {{
            animation: pulse 2s infinite;
        }}
        </style>
        </head>
        <body>
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Reddit Social Pulse</div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span class="live-badge" style="background: #f23645; color: white; padding: 2px 8px; border-radius: 4px; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;">LIVE</span>
                    <div class="tooltip-wrapper">
                        <div class="tooltip-btn">?</div>
                        <div class="tooltip-content">Top 10 activos más mencionados en Reddit según BuzzTickr. Incluye Health Score, Smart Money tracking y Squeeze Potential.</div>
                    </div>
                </div>
            </div>
            <div class="module-content">
                {cards_html}
            </div>
            <div class="update-timestamp">Updated: {timestamp} • {source} • Top {count}</div>
        </div>
        </body>
        </html>
        """
        
        components.html(full_html, height=420, scrolling=False)















