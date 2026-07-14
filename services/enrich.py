"""Enrich a parsed reading with supplementary, clearly-labeled content.

The readings themselves are the authentic liturgical text and are NEVER
rewritten. Enrichment only *adds* optional fields — a one-line message, a short
reflection, a kids' version, discussion questions and an image prompt — produced
by a pluggable provider:

  - StubProvider (default, offline, deterministic): templated from the reading,
    with no network, so tests and the end-to-end check run without any API key.
  - LLMProvider: an OpenAI-compatible chat endpoint. It works with the free
    tiers the project targets (Groq, Cloudflare Workers AI, Gemini's
    OpenAI-compatible API, or a local Ollama). Select it with ENRICH_PROVIDER=llm
    and configure ENRICH_API_URL / ENRICH_API_KEY / ENRICH_MODEL.

Everything AI-generated is stored under its own fields and marked with the
provider name, so clients can label it clearly as reflection/art, distinct from
the readings.
"""

import json
import os

import requests

# Bumped when the stored document schema/format changes, so legacy records can
# be distinguished or filtered (e.g. `{source_version: 2}`).
SOURCE_VERSION = 2

_SYSTEM_PROMPT = (
    'Eres un asistente católico que escribe en español, con tono reverente y '
    'cercano. No modifiques ni cites textualmente la Escritura: ofrece solo un '
    'comentario breve y original. Responde únicamente con el texto pedido.'
)


def _gospel(reading):
    for lectura in reading.get('lecturas', []):
        if 'evangelio' in lectura.get('title', '').lower():
            return lectura
    lecturas = reading.get('lecturas') or [{}]
    return lecturas[-1]


class StubProvider:
    """Deterministic, offline enrichment — a useful placeholder until a real
    LLM provider is configured. Keeps tests and the e2e reproducible."""

    name = 'stub'

    def message(self, reading):
        gospel = _gospel(reading)
        return gospel.get('first_line') or reading.get('title', '')

    def reflection(self, reading):
        title = reading.get('title', 'la Palabra de hoy')
        return (f'La Palabra de hoy ({title}) nos invita a detenernos y escuchar. '
                'Dedica un momento a leerla despacio y a llevar una frase contigo durante el día.')

    def kids(self, reading):
        return ('Hoy Jesús nos habla en el Evangelio. Escúchalo con el corazón y '
                'trata de hacer feliz a alguien hoy.')

    def questions(self, reading):
        return [
            '¿Qué frase de la lectura de hoy te llama más la atención?',
            '¿Cómo puedes vivir hoy lo que has leído?',
        ]

    def image_prompt(self, reading):
        gospel = _gospel(reading)
        scene = gospel.get('first_line') or reading.get('title', '')
        return f'Ilustración reverente y luminosa, estilo cálido, de: {scene}'


class LLMProvider:
    """Enrichment via an OpenAI-compatible chat completions endpoint."""

    name = 'llm'

    def __init__(self):
        self._url = os.getenv('ENRICH_API_URL')
        self._key = os.getenv('ENRICH_API_KEY')
        self._model = os.getenv('ENRICH_MODEL', 'llama-3.1-8b-instant')

    def _chat(self, instruction, reading):
        gospel = _gospel(reading)
        context = f"{reading.get('title', '')}\n\n{gospel.get('content', '')}"
        payload = {
            'model': self._model,
            'messages': [
                {'role': 'system', 'content': _SYSTEM_PROMPT},
                {'role': 'user', 'content': f'{instruction}\n\nLectura:\n{context}'},
            ],
        }
        headers = {'Authorization': f'Bearer {self._key}', 'Content-Type': 'application/json'}
        response = requests.post(self._url, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()

    def message(self, reading):
        return self._chat('Escribe un "mensaje del día" de una sola frase inspirado en el Evangelio.', reading)

    def reflection(self, reading):
        return self._chat('Escribe una reflexión breve (2-3 frases) que conecte el Evangelio con la vida diaria.', reading)

    def kids(self, reading):
        return self._chat('Explica el Evangelio de hoy para un niño pequeño, en 1-2 frases sencillas.', reading)

    def questions(self, reading):
        raw = self._chat('Propón dos preguntas breves para reflexionar en familia. Una por línea, sin numerar.', reading)
        return [line.strip('-• ').strip() for line in raw.splitlines() if line.strip()][:2]

    def image_prompt(self, reading):
        return self._chat('Describe en una frase, en español, una escena del Evangelio para ilustrarla (prompt de imagen).', reading)


def get_provider():
    if os.getenv('ENRICH_PROVIDER') == 'llm':
        return LLMProvider()
    return StubProvider()


def enrich(reading, provider=None):
    # Adds the supplementary fields onto the reading dict and stamps its schema
    # version + the provider used. Returns the same dict for convenience.
    if not reading:
        return reading
    provider = provider or get_provider()
    reading['message'] = provider.message(reading)
    reading['reflection'] = provider.reflection(reading)
    reading['kids_reflection'] = provider.kids(reading)
    reading['questions'] = provider.questions(reading)
    reading['image_prompt'] = provider.image_prompt(reading)
    reading['enrichment_provider'] = provider.name
    reading['source_version'] = SOURCE_VERSION
    return reading
