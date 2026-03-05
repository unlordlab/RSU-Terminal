"""
scripts/generate_briefing.py
Flujo: yfinance (precios reales) + NewsAPI (titulares) → Groq llama-3.3-70b → GitHub Gist
"""
import os, sys, json, requests, pytz
from datetime import datetime, timedelta

CET      = pytz.timezone('Europe/Madrid')
now_cet  = datetime.now(CET)
today_str= now_cet.strftime('%A %d de %B de %Y')
date_key = now_cet.strftime('%Y-%m-%d')
time_str = now_cet.strftime('%H:%M')
weekday  = now_cet.strftime('%A')

if now_cet.weekday() >= 5:
    print(f"Fin de semana — no se genera briefing.")
    sys.exit(0)


def get_market_snapshot():
    """Precios reales con análisis técnico básico (medias, distancia a niveles)."""
    try:
        import yfinance as yf
        import statistics

        result = {}
        specs = {
            'ES=F':     'S&P 500 Futuros',
            'NQ=F':     'Nasdaq 100 Futuros',
            '^VIX':     'VIX',
            'GC=F':     'Oro',
            'CL=F':     'Petroleo WTI',
            'DX-Y.NYB': 'DXY Dolar Index',
            '^TNX':     'Bono 10Y USA (yield)',
            'ZN=F':     'Futuros Bono 10Y',
        }

        lines = []
        for sym, name in specs.items():
            try:
                h = yf.Ticker(sym).history(period='5d', interval='1h')
                if h.empty or len(h) < 5:
                    continue
                closes = list(h['Close'])
                price  = closes[-1]
                prev24 = closes[-25] if len(closes) >= 25 else closes[0]
                prev5d = closes[0]
                pct24  = (price - prev24) / prev24 * 100 if prev24 else 0
                pct5d  = (price - prev5d) / prev5d * 100 if prev5d else 0

                # Simple support/resistance: recent high/low
                highs = list(h['High'][-50:])
                lows  = list(h['Low'][-50:])
                res   = max(highs)
                sup   = min(lows)

                line = f"  {name}: {price:,.2f} | 24h: {pct24:+.2f}% | 5d: {pct5d:+.2f}%"
                if sym in ('ES=F', '^GSPC'):
                    line += f" | Rango 50h: {sup:,.0f} - {res:,.0f}"
                lines.append(line)
            except Exception:
                continue

        return '\n'.join(lines) if lines else "  Datos no disponibles"
    except Exception as e:
        return f"  Error yfinance: {e}"


def get_market_news(api_key):
    """Titulares de las últimas 8 horas con múltiples queries para mayor cobertura."""
    if not api_key:
        return "  NewsAPI no configurada — el modelo debe basar el análisis en los datos de precio."

    all_articles = []
    queries = [
        'S&P 500 OR Nasdaq OR stock market futures',
        'Federal Reserve OR interest rates OR inflation',
        'tariffs OR trade war OR Trump economy',
        'earnings results OR GDP OR unemployment',
    ]
    since = (datetime.utcnow() - timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M:%S')

    for q in queries:
        try:
            r = requests.get(
                'https://newsapi.org/v2/everything',
                params={
                    'q':        q,
                    'from':     since,
                    'language': 'en',
                    'sortBy':   'publishedAt',
                    'pageSize': 5,
                    'apiKey':   api_key,
                },
                timeout=8
            )
            if r.status_code == 200:
                all_articles += r.json().get('articles', [])
        except Exception:
            continue

    # Dedup by title
    seen, unique = set(), []
    for a in all_articles:
        t = a.get('title', '')
        if t and t not in seen and '[Removed]' not in t and len(t) > 15:
            seen.add(t)
            unique.append(a)

    if not unique:
        return "  Sin titulares disponibles via NewsAPI — análisis basado en datos de precio."

    # Sort by date, take top 8
    unique.sort(key=lambda x: x.get('publishedAt', ''), reverse=True)
    lines = []
    for a in unique[:8]:
        title  = a.get('title', '').strip()
        source = a.get('source', {}).get('name', '')
        pub    = a.get('publishedAt', '')[:16].replace('T', ' ')
        desc   = a.get('description', '') or ''
        lines.append(f"  [{pub}] {title} ({source})")
        if desc and len(desc) > 20:
            lines.append(f"    → {desc[:120]}")

    return '\n'.join(lines)


def build_prompt(market_data, news_data):
    return f"""Eres un analista de mercados senior con 20 años de experiencia en trading institucional.
Hoy es {weekday} {today_str}, son las {time_str} CET. La sesión americana abre en ~30 minutos.

DATOS DE MERCADO EN TIEMPO REAL:
{market_data}

TITULARES DE LAS ÚLTIMAS HORAS:
{news_data}

Redacta un briefing PRE-APERTURA AMERICANA profesional en ESPAÑOL, máximo 380 palabras.
El tono debe ser el de un analista institucional: directo, técnico, con convicción.
NO uses frases vacías como "los mercados están atentos a" o "los inversores observan".

Estructura OBLIGATORIA — sigue exactamente este formato:

**Briefing de Mercado — {weekday} {today_str}**

**1. Sentimiento del Mercado: [ETIQUETA]**
[Etiqueta: Risk-On / Risk-Off / Cautela / Neutral / Euforia / Capitulación]
Párrafo de 3-4 líneas. Interpreta el VIX, la dirección de los futuros y los titulares como un analista que toma posición. Identifica si hay divergencias entre activos (ej: futuros alcistas pero bono cayendo = señal de alerta).

**2. Acción del Precio y Niveles Clave (S&P 500)**
- Precio futuro actual: [usar dato real de arriba]
- **Resistencia clave:** [nivel concreto derivado del rango que tienes + contexto técnico]
- **Soporte crítico:** [nivel concreto + qué implica perderlo]
- Una línea de contexto sobre si el precio está respetando o violando niveles importantes.

**3. Calendario Macro de Hoy (USA — Hora Española)**
[Si los titulares mencionan datos de hoy, inclúyelos con hora y consenso]
[Si no, escribe exactamente: "Verificar en Investing.com/economic-calendar para datos del día"]

**4. Catalizadores Específicos**
- [Titular 1 más relevante de los que tienes: qué implica para el mercado]
- [Titular 2: idem]
- [Titular 3 si procede]
[Si no hay titulares relevantes: "Sin catalizadores externos identificados. La sesión se moverá por datos técnicos y flujo de órdenes."]

**5. Conclusión Táctica**
Una frase con verbo de acción: qué hacer hoy y por qué. Ejemplo: "Reducir exposición hasta que el SPX recupere [nivel] con volumen." No uses condicionales vagos.

REGLAS: Usa los datos numéricos que te he dado. Si derivas niveles técnicos, justifícalos brevemente. Responde SOLO en español castellano."""


def call_groq(api_key, prompt):
    r = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={
            'model':       'llama-3.3-70b-versatile',
            'messages':    [
                {
                    'role': 'system',
                    'content': (
                        'Eres un analista de mercados institucional senior. '
                        'Escribes con precisión técnica y convicción. '
                        'Nunca usas lenguaje vago ni generalidades. '
                        'Respondes SIEMPRE en español castellano. '
                        'Cuando tienes datos reales los usas; cuando no, lo dices explícitamente.'
                    )
                },
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.25,
            'max_tokens':  1100,
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
        print(f'✓ Gist actualizado: {r.json().get("html_url", "")}')
    else:
        print(f'✗ Gist error {r.status_code}: {r.text[:200]}')
        r.raise_for_status()


def main():
    groq_key  = os.environ['GROQ_API_KEY']
    gist_id   = os.environ['BRIEFING_GIST_ID']
    gh_token  = os.environ['GH_GIST_TOKEN']
    news_key  = os.environ.get('NEWS_API_KEY', '')

    print(f'=== Briefing {date_key} {time_str} CET ===')

    print('\n[1/3] Datos de mercado...')
    market_data = get_market_snapshot()
    print(market_data)

    print('\n[2/3] Titulares...')
    news_data = get_market_news(news_key)
    print(news_data[:400])

    print('\n[3/3] Generando con Groq llama-3.3-70b...')
    prompt = build_prompt(market_data, news_data)
    text   = call_groq(groq_key, prompt)
    model  = 'Groq llama-3.3-70b'

    print(f'\n✓ {len(text.split())} palabras generadas')
    print('\n--- PREVIEW ---')
    print(text[:600] + ('...' if len(text) > 600 else ''))
    print('---\n')

    save_to_gist(text, model, gist_id, gh_token)
    print('✓ Completado.')


if __name__ == '__main__':
    main()
