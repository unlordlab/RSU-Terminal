"""
scripts/generate_briefing.py
Ejecutado por GitHub Actions a las 08:00 CET (lunes-viernes).
Genera el briefing con Gemini 2.5-flash + Google Search grounding
y lo guarda en Supabase tabla market_briefings.

Todos los usuarios del dashboard leen el mismo briefing del día
sin coste adicional de API por cada visita.

SQL para crear la tabla en Supabase:
  CREATE TABLE market_briefings (
    date         TEXT PRIMARY KEY,
    text         TEXT NOT NULL,
    generated_at TEXT,
    model        TEXT,
    created_at   TIMESTAMP DEFAULT NOW()
  );
  ALTER TABLE market_briefings ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "public read" ON market_briefings FOR SELECT USING (true);
"""
import os, sys, requests, pytz
from datetime import datetime

CET       = pytz.timezone('Europe/Madrid')
now_cet   = datetime.now(CET)
today_str = now_cet.strftime('%A %d de %B de %Y')
date_key  = now_cet.strftime('%Y-%m-%d')
time_str  = now_cet.strftime('%H:%M')

# No ejecutar en fin de semana
if now_cet.weekday() >= 5:
    print(f"Fin de semana ({now_cet.strftime('%A')}) — no se genera briefing.")
    sys.exit(0)

PROMPT = f"""Actúa como analista senior de mercados financieros con acceso a búsqueda web en tiempo real.
Hoy es {today_str}. Genera un briefing PRE-APERTURA conciso (máximo 350 palabras) en ESPAÑOL.

Estructura OBLIGATORIA — usa ÚNICAMENTE datos reales de búsqueda, nunca inventes cifras:

1. **Sentimiento del Mercado:** 'Risk-on', 'Risk-off' o 'Neutral'.
   Basa la conclusión en: futuros S&P 500, Nasdaq y nivel actual del VIX.

2. **Acción del Precio y Niveles Clave:**
   - S&P 500: precio futuro actual, soporte y resistencia inmediatos.
   - Nasdaq 100: idem.

3. **Calendario Macro de Hoy (USA — Hora Española):**
   Lista los 2-4 datos económicos de impacto de HOY con hora exacta y consenso del mercado.

4. **Catalizadores del Día:**
   Aranceles, Fed/BCE, geopolítica o earnings relevantes para HOY. Cita fuente y hora.

5. **Conclusión Táctica:**
   Una frase: ¿agresivo o defensivo hoy? Justificación en 1-2 líneas.

REGLAS: Si no tienes un dato exacto, escribe "no disponible a esta hora". NUNCA inventes.
Responde SIEMPRE en español. Tono directo y profesional.
"""


def generate_with_gemini(api_key):
    import google.generativeai as genai
    from google.generativeai.types import Tool, GenerateContentConfig
    genai.configure(api_key=api_key)
    for model_name, use_grounding in [
        ('gemini-2.5-flash', True),
        ('gemini-2.5-flash', False),
        ('gemini-2.0-flash', False),
    ]:
        try:
            m = genai.GenerativeModel(model_name)
            if use_grounding:
                r = m.generate_content(PROMPT,
                    tools=[Tool(google_search=genai.protos.GoogleSearch())],
                    generation_config=GenerateContentConfig(temperature=0.1))
            else:
                r = m.generate_content(PROMPT,
                    generation_config=GenerateContentConfig(temperature=0.1))
            text = (r.text or '').strip()
            if text:
                suffix = '' if use_grounding else '\n\n_(sin Google Search grounding)_'
                return text + suffix, model_name
        except Exception as e:
            print(f"  [{model_name}] {e}")
    raise RuntimeError("Todos los modelos Gemini fallaron")


def save_to_supabase(text, model, url, key):
    r = requests.post(
        f'{url}/rest/v1/market_briefings',
        headers={
            'apikey': key, 'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'Prefer': 'resolution=merge-duplicates',
        },
        json={'date': date_key, 'text': text, 'generated_at': time_str, 'model': model},
        timeout=15,
    )
    if r.status_code in (200, 201):
        print(f"✓ Supabase OK: {date_key} {time_str} CET · {model}")
    else:
        print(f"✗ Supabase error {r.status_code}: {r.text[:200]}")
        r.raise_for_status()


def main():
    gemini_key   = os.environ['GEMINI_API_KEY']
    supabase_url = os.environ['SUPABASE_URL']
    supabase_key = os.environ['SUPABASE_SERVICE_KEY']  # service_role para escritura

    print(f"Generando briefing {date_key} a las {time_str} CET...")
    text, model = generate_with_gemini(gemini_key)
    print(f"✓ {model} · {len(text.split())} palabras")
    print("\n--- PREVIEW ---\n" + text[:400] + ('...' if len(text) > 400 else '') + "\n---")
    save_to_supabase(text, model, supabase_url, supabase_key)


if __name__ == '__main__':
    main()
