"""
scripts/generate_briefing.py
Ejecutado por GitHub Actions a las 08:00 CET (lunes-viernes).
SDK: google-genai (nuevo oficial). NO usa google-generativeai (deprecado).
"""
import os, sys, requests, pytz
from datetime import datetime

CET      = pytz.timezone('Europe/Madrid')
now_cet  = datetime.now(CET)
today_str= now_cet.strftime('%A %d de %B de %Y')
date_key = now_cet.strftime('%Y-%m-%d')
time_str = now_cet.strftime('%H:%M')

if now_cet.weekday() >= 5:
    print(f"Fin de semana ({now_cet.strftime('%A')}) — no se genera briefing.")
    sys.exit(0)

PROMPT = (
    f"Actua como analista senior de mercados financieros con acceso a busqueda web en tiempo real.\n"
    f"Hoy es {today_str}. Genera un briefing PRE-APERTURA conciso (max 350 palabras) en ESPANOL.\n\n"
    "Estructura OBLIGATORIA - usa UNICAMENTE datos reales de busqueda, nunca inventes cifras:\n\n"
    "1. Sentimiento del Mercado: Risk-on, Risk-off o Neutral.\n"
    "   Basa la conclusion en: futuros S&P 500, Nasdaq y nivel actual del VIX.\n\n"
    "2. Accion del Precio y Niveles Clave:\n"
    "   - S&P 500: precio futuro actual, soporte y resistencia inmediatos.\n"
    "   - Nasdaq 100: idem.\n\n"
    "3. Calendario Macro de Hoy (USA - Hora Espanola):\n"
    "   Lista los 2-4 datos economicos de impacto de HOY con hora exacta y consenso.\n\n"
    "4. Catalizadores del Dia:\n"
    "   Aranceles, Fed/BCE, geopolitica o earnings relevantes para HOY. Cita fuente.\n\n"
    "5. Conclusion Tactica:\n"
    "   Una frase: agresivo o defensivo hoy? Justificacion en 1-2 lineas.\n\n"
    "REGLAS: Si no tienes un dato exacto escribe 'no disponible a esta hora'. NUNCA inventes.\n"
    "Responde SIEMPRE en espanol. Tono directo y profesional.\n"
)


def generate_with_gemini(api_key):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    attempts = [
        ('gemini-2.5-flash-preview-04-17', True),
        ('gemini-2.5-flash-preview-04-17', False),
        ('gemini-2.0-flash', False),
    ]

    for model_id, use_grounding in attempts:
        try:
            if use_grounding:
                cfg = types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                )
            else:
                cfg = types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                )

            response = client.models.generate_content(
                model=model_id,
                contents=PROMPT,
                config=cfg,
            )
            text = (response.text or '').strip()
            if text:
                label = f'{model_id} + Google Search grounding' if use_grounding else f'{model_id} sin grounding'
                print(f'  OK: {label}')
                return text, label
        except Exception as e:
            print(f'  [{model_id} grounding={use_grounding}] Error: {e}')
            continue

    raise RuntimeError("Todos los modelos Gemini fallaron")


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
        print(f'Supabase OK: {date_key} {time_str} CET')
    else:
        print(f'Supabase error {r.status_code}: {r.text[:300]}')
        r.raise_for_status()


def main():
    gemini_key   = os.environ['GEMINI_API_KEY']
    supabase_url = os.environ['SUPABASE_URL']
    supabase_key = os.environ['SUPABASE_SERVICE_KEY']

    print(f'Generando briefing {date_key} a las {time_str} CET...')
    text, model = generate_with_gemini(gemini_key)
    print(f'Modelo: {model} | Palabras: {len(text.split())}')
    print('--- PREVIEW ---')
    print(text[:400] + ('...' if len(text) > 400 else ''))
    print('---')
    save_to_supabase(text, model, supabase_url, supabase_key)
    print('Completado.')


if __name__ == '__main__':
    main()
