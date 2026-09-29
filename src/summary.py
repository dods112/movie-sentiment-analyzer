"""AI summary of what reviewers say about one movie: a single Groq call, cached."""
import json
import re
import time

import openai
import streamlit as st
from openai import OpenAI

from src.api import _extract_json

MAX_REVIEWS = 40    # newest reviews sent to the model
MAX_CHARS = 300     # per review

SYSTEM_PROMPT = (
    "You summarize audience reviews of one movie. Use only the reviews provided. "
    "Reply with valid JSON only - no prose, no markdown."
)

USER_TEMPLATE = """Movie: {movie}
Reviews ({count}):
{lines}

Return JSON in exactly this format:
{{"verdict": "one or two sentences on the overall reception",
  "loved": ["up to 3 things reviewers liked"],
  "complaints": ["up to 3 things reviewers disliked, or an empty list if none"]}}
Each point must be under 15 words, plain text."""


def _points(value) -> list:
    """Coerce a value into a clean list of up to 3 short strings."""
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()][:3]


def _unwrap(parsed):
    """The model sometimes double-encodes the JSON, or wraps the payload in an
    outer key. Walk inwards until we reach a dict that has a 'verdict' field."""
    # 1. If we got a string, try to parse it.
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except (ValueError, TypeError):
            return {}

    # 2. If we got a dict without 'verdict', look inside its values for one.
    seen = 0
    while isinstance(parsed, dict) and "verdict" not in parsed and seen < 3:
        nested = None
        for v in parsed.values():
            if isinstance(v, dict):
                nested = v
                break
            if isinstance(v, str):
                try:
                    candidate = json.loads(v)
                    if isinstance(candidate, dict):
                        nested = candidate
                        break
                except (ValueError, TypeError):
                    pass
        if nested is None:
            break
        parsed = nested
        seen += 1

    return parsed if isinstance(parsed, dict) else {}


@st.cache_data(show_spinner=False, ttl=3600)
def summarize_reviews(_api_key: str, _base_url: str, model: str, movie: str,
                      review_lines: tuple) -> dict:
    """Cached per (model, movie, reviews): the same reviews never cost a second call.
    Raises on failure, and Streamlit does not cache exceptions, so a failure is retried."""
    client = OpenAI(api_key=_api_key, base_url=_base_url)
    extra = {"reasoning_effort": "low"} if "gpt-oss" in model else {}
    prompt = USER_TEMPLATE.format(movie=movie, count=len(review_lines),
                                  lines="\n".join(review_lines))

    response = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT},
                          {"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
                extra_body=extra,
            )
            break
        except openai.RateLimitError as e:
            if attempt == 2:
                raise
            m = re.search(r"try again in (\d+(?:\.\d+)?)(ms|s)\b", str(e))
            wait = float(m.group(1)) / (1000 if m.group(2) == "ms" else 1) if m else 3
            time.sleep(min(wait + 0.5, 15))

    raw = response.choices[0].message.content or ""
    parsed = _unwrap(_extract_json(raw))

    verdict = str(parsed.get("verdict", "")).strip()
    if not verdict:
        raise ValueError(f"The model returned an empty summary. Raw: {raw[:200]}")

    return {
        "verdict": verdict,
        "loved": _points(parsed.get("loved")),
        "complaints": _points(parsed.get("complaints")),
    }