"""
scripts/generate_briefing.py

Arquitectura:
  1. NewsAPI (gratuita) — obtiene titulares reales de las últimas horas
  2. yfinance — obtiene precios reales de futuros/índices en el momento de ejecución
  3. Inyecta esos datos en el prompt como contexto real
  4. Groq llama-3.3-70b — genera el briefing (100% gratuito, ~1s latencia)
  5. Guarda resultado en Supabase — todos los usuarios leen el mismo briefing

Configurar en GitHub Secrets:
  GROQ_API_KEY         — console.groq.com (gratuito)
  NEWS_API_KEY         — newsapi.org (gratuito, 100 req/día)
  SUPABASE_URL         — Settings > API en tu proyecto Supabase
  SUPABASE_SERVICE_KEY — service_role key (para escritura)

Cron: 13:00 UTC = 14:00 CET (30min antes apertura USA en horario europeo)
"""
import os, sys, json, requests, pytz
from datetime import datetime, timedelta

CET      = pytz.timezone('Europe/Madrid')
now_cet  = datetime.now(CET)
today_str= now_cet.strftime('%A %d de %B de %Y')
date_key = now_cet.strftime('%Y-%m-%d')
time_str = now_cet.strftime('%H:%M')

if now_cet.weekday() >= 5:
    print(f"Fin de semana — no se genera briefing.")
    sys.exit(0)


# ── 1. DATOS DE MERCADO REALES (yfinance) ───────────────────────────────────
def get_market_snapshot():
    """Precio real de futuros e índices en el momento del job."""
    try:
        import yfinance as yf
        tickers = {
            'ES=F':  'S&P 500 Futuros',
            'NQ=F':  'Nasdaq 100 Futuros',
            '^VIX':  'VIX',
            '^GSPC': 'S&P 500',
            'GC=F':  'Oro',
            'CL=F':  'Petróleo WTI',
            'DX-Y.NYB': 'DXY (Dólar)',
        }
        lines = []
        for sym, name in tickers.items():
            try:
                t = yf.Ticker(sym)
                h = t.history(period='2d', interval='1h')
                if h.empty:
                    continue
                price = float(h['Close'].iloc[-1])
                prev  = float(h['Close'].iloc[-25]) if len(h) >= 25 else float(h['Close'].iloc[0])
                pct   = (price - prev) / prev * 100 if prev else 0
                lines.append(f"  {name}: {price:,.2f} ({pct:+.2f}% vs 24h)")
            except Exception:
                continue
        return '\n'.join(lines) if lines else "  Datos no disponibles"
    except ImportError:
        return "  yfinance no instalado"


# ── 2. TITULARES REALES (NewsAPI) ───────────────────────────────────────────
def get_market_news(api_key):
    """Titulares de mercado de las últimas 6 horas."""
    if not api_key:
        return "  NewsAPI no configurada — omitir sección de noticias"
    try:
        since = (datetime.utcnow() - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%S')
        r = requests.get(
            'https://newsapi.org/v2/everything',
            params={
                'q':          'stock market OR S&P 500 OR Federal Reserve OR tariffs OR aranceles',
                'from':        since,
                'language':   'en',
                'sortBy':     'publishedAt',
                'pageSize':   8,
                'apiKey':     api_key,
            },
            timeout=10
        )
        if r.status_code != 200:
            return f"  NewsAPI error {r.status_code}"
        articles = r.json().get('articles', [])
        if not articles:
            return "  Sin titulares relevantes en las últimas 6 horas"
        lines = []
        for a in articles[:6]:
            title  = a.get('title', '').replace('[Removed]', '').strip()
            source = a.get('source', {}).get('name', '')
            pub    = a.get('publishedAt', '')[:16].replace('T', ' ')
            if title and len(title) > 10:
                lines.append(f"  [{pub}] {title} ({source})")
        return '\n'.join(lines) if lines else "  Sin titulares"
    except Exception as e:
        return f"  Error NewsAPI: {e}"


# ── 3. PROMPT CON DATOS REALES INYECTADOS ───────────────────────────────────
def build_prompt(market_data, news_data):
    return (
        f"Eres analista senior de mercados financieros. Hoy es {today_str}, son las {time_str} CET.\n"
        "Genera un briefing PRE-APERTURA AMERICANA conciso (máximo 320 palabras) en ESPAÑOL.\n\n"
        "DATOS REALES DE MERCADO EN ESTE MOMENTO:\n"
        f"{market_data}\n\n"
        "TITULARES DE LAS ÚLTIMAS HORAS:\n"
        f"{news_data}\n\n"
        "Usando ÚNICAMENTE los datos anteriores (no inventes cifras adicionales), redacta:\n\n"
        "1. **Sentimiento del Mercado:** Risk-on, Risk-off o Neutral.\n"
        "   Justifica con los datos de futuros y VIX que tienes arriba.\n\n"
        "2. **Acción del Precio y Niveles Clave (S&P 500):**\n"
        "   Precio futuro actual (usa el dato de arriba), soporte y resistencia inmediatos.\n\n"
        "3. **Calendario Macro de Hoy (USA — Hora Española):**\n"
        "   Si algún titular menciona datos macro de hoy, inclúyelos. Si no, indica 'verificar Investing.com'.\n\n"
        "4. **Catalizadores del Día:**\n"
        "   Resume los 2-3 titulares más relevantes de los que tienes arriba.\n\n"
        "5. **Conclusión Táctica:**\n"
        "   Una frase: agresivo o defensivo. Justificación en 1-2 líneas.\n\n"
        "REGLAS: Usa los datos que te he dado. Si no tienes un dato, escríbelo explícitamente. "
        "Tono directo y profesional. Sin perogrulladas."
    )


# ── 4. LLAMADA A GROQ ────────────────────────────────────────────────────────
def call_groq(api_key, prompt):
    r = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type':  'application/json',
        },
        json={
            'model':       'llama-3.3-70b-versatile',
            'messages':    [{'role': 'user', 'content': prompt}],
            'temperature': 0.15,
            'max_tokens':  900,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content'].strip()


# ── 5. GUARDAR EN SUPABASE ───────────────────────────────────────────────────
def save_to_supabase(text, model, url, key):
    r = requests.post(
        f'{url}/rest/v1/market_briefings',
        headers={
            'apikey':        key,
            'Authorization': f'Bearer {key}',
            'Content-Type':  'application/json',
            'Prefer':        'resolution=merge-duplicates',
        },
        json={
            'date':         date_key,
            'text':         text,
            'generated_at': time_str,
            'model':        model,
        },
        timeout=15,
    )
    if r.status_code in (200, 201):
        print(f'✓ Supabase: {date_key} {time_str} CET guardado')
    else:
        print(f'✗ Supabase {r.status_code}: {r.text[:200]}')
        r.raise_for_status()


# ── MAIN ────────────────────────────────────────────────────────────────────
def main():
    groq_key     = os.environ['GROQ_API_KEY']
    news_key     = os.environ.get('NEWS_API_KEY', '')     # opcional pero recomendado
    supabase_url = os.environ['SUPABASE_URL']
    supabase_key = os.environ['SUPABASE_SERVICE_KEY']

    print(f'Generando briefing {date_key} a las {time_str} CET...')

    print('  Obteniendo datos de mercado...')
    market_data = get_market_snapshot()
    print(market_data)

    print('  Obteniendo titulares...')
    news_data = get_market_news(news_key)
    print(news_data[:300])

    print('  Llamando a Groq llama-3.3-70b...')
    prompt = build_prompt(market_data, news_data)
    text   = call_groq(groq_key, prompt)
    model  = 'Groq llama-3.3-70b + NewsAPI + yfinance'

    print(f'  ✓ Generado: {len(text.split())} palabras')
    print('--- PREVIEW ---')
    print(text[:500] + ('...' if len(text) > 500 else ''))
    print('---')

    save_to_supabase(text, model, supabase_url, supabase_key)
    print('✓ Completado.')


if __name__ == '__main__':
    main()


if __name__ == '__main__':
    main()
