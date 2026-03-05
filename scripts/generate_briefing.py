"""
scripts/generate_briefing.py

Flujo: yfinance + NewsAPI → prompt con datos reales → Groq → GitHub Gist
Todos los usuarios leen el mismo Gist. Sin base de datos. 100% gratuito.

GitHub Secrets necesarios:
  GROQ_API_KEY      — console.groq.com (gratis)
  GH_GIST_TOKEN     — github.com/settings/tokens → scope: gist
  BRIEFING_GIST_ID  — ID del Gist donde se guarda (ver instrucciones abajo)
  NEWS_API_KEY      — newsapi.org (gratis, opcional)

Crear el Gist por primera vez:
  1. Ve a gist.github.com
  2. Crea un Gist público llamado "briefing.json" con contenido: {}
  3. Copia el ID de la URL: gist.github.com/tuusuario/ESTE-ES-EL-ID
  4. Añade ese ID como secret BRIEFING_GIST_ID en GitHub Actions
     Y también en Streamlit secrets como BRIEFING_GIST_ID
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


def get_market_snapshot():
    try:
        import yfinance as yf
        tickers = {
            'ES=F':      'S&P 500 Futuros',
            'NQ=F':      'Nasdaq 100 Futuros',
            '^VIX':      'VIX',
            'GC=F':      'Oro',
            'CL=F':      'Petroleo WTI',
            'DX-Y.NYB':  'DXY (Dolar)',
        }
        lines = []
        for sym, name in tickers.items():
            try:
                h = yf.Ticker(sym).history(period='2d', interval='1h')
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


def get_market_news(api_key):
    if not api_key:
        return "  NewsAPI no configurada"
    try:
        since = (datetime.utcnow() - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%S')
        r = requests.get(
            'https://newsapi.org/v2/everything',
            params={
                'q':        'stock market OR S&P 500 OR Federal Reserve OR tariffs',
                'from':      since,
                'language': 'en',
                'sortBy':   'publishedAt',
                'pageSize':  8,
                'apiKey':    api_key,
            },
            timeout=10
        )
        if r.status_code != 200:
            return f"  NewsAPI error {r.status_code}"
        articles = r.json().get('articles', [])
        lines = []
        for a in articles[:6]:
            title  = a.get('title', '').replace('[Removed]', '').strip()
            source = a.get('source', {}).get('name', '')
            pub    = a.get('publishedAt', '')[:16].replace('T', ' ')
            if title and len(title) > 10:
                lines.append(f"  [{pub}] {title} ({source})")
        return '\n'.join(lines) if lines else "  Sin titulares relevantes"
    except Exception as e:
        return f"  Error: {e}"


def build_prompt(market_data, news_data):
    return (
        f"Eres analista senior de mercados financieros. Hoy es {today_str}, {time_str} CET.\n"
        "Genera un briefing PRE-APERTURA AMERICANA conciso (max 320 palabras) en ESPANOL.\n\n"
        "DATOS REALES AHORA MISMO:\n"
        f"{market_data}\n\n"
        "TITULARES ULTIMAS HORAS:\n"
        f"{news_data}\n\n"
        "Usando UNICAMENTE los datos anteriores redacta:\n\n"
        "1. Sentimiento del Mercado: Risk-on, Risk-off o Neutral. Justifica con VIX y futuros.\n\n"
        "2. Accion del Precio S&P 500: precio futuro actual (usa el dato arriba), "
        "soporte y resistencia inmediatos estimados.\n\n"
        "3. Calendario Macro Hoy (USA, hora espanola): "
        "Si algun titular menciona datos macro de hoy incluyelo. Si no, indica 'consultar Investing.com'.\n\n"
        "4. Catalizadores: resume los 2-3 titulares mas relevantes.\n\n"
        "5. Conclusion Tactica: agresivo o defensivo hoy? Una frase con justificacion.\n\n"
        "Si no tienes un dato escribelo explicitamente. Tono directo y profesional."
    )


def call_groq(api_key, prompt):
    r = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
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


def save_to_gist(text, model, gist_id, gh_token):
    payload = json.dumps({
        'date':         date_key,
        'text':         text,
        'generated_at': time_str,
        'model':        model,
    }, ensure_ascii=False, indent=2)

    r = requests.patch(
        f'https://api.github.com/gists/{gist_id}',
        headers={
            'Authorization': f'Bearer {gh_token}',
            'Accept':        'application/vnd.github.v3+json',
        },
        json={'files': {'briefing.json': {'content': payload}}},
        timeout=15,
    )
    if r.status_code == 200:
        print(f'Gist OK: {date_key} {time_str} CET')
        print(f'URL: {r.json().get("html_url", "")}')
    else:
        print(f'Gist error {r.status_code}: {r.text[:200]}')
        r.raise_for_status()


def main():
    groq_key  = os.environ['GROQ_API_KEY']
    gist_id   = os.environ['BRIEFING_GIST_ID']
    gh_token  = os.environ['GH_GIST_TOKEN']
    news_key  = os.environ.get('NEWS_API_KEY', '')

    print(f'Generando briefing {date_key} a las {time_str} CET...')

    print('Obteniendo datos de mercado...')
    market_data = get_market_snapshot()
    print(market_data)

    print('Obteniendo titulares...')
    news_data = get_market_news(news_key)
    print(news_data[:200])

    print('Llamando a Groq...')
    prompt = build_prompt(market_data, news_data)
    text   = call_groq(groq_key, prompt)
    model  = 'Groq llama-3.3-70b'

    print(f'Generado: {len(text.split())} palabras')
    print('--- PREVIEW ---')
    print(text[:400] + ('...' if len(text) > 400 else ''))
    print('---')

    save_to_gist(text, model, gist_id, gh_token)
    print('Completado.')


if __name__ == '__main__':
    main()
