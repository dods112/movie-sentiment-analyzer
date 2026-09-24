"""Groq API calls for sentiment analysis. Async + concurrent."""
import asyncio
import json
import re
from typing import Any

from openai import AsyncOpenAI


VALID_SENTIMENTS = {"Positive", "Negative", "Neutral"}

SYSTEM_PROMPT = (
    "You are a precise sentiment analysis engine. "
    "Always return valid JSON only — no prose, no markdown fences."
)

USER_TEMPLATE = """Analyze the following movie review.
Respond ONLY with valid JSON in this exact format:
{{"sentiment": "Positive" | "Negative" | "Neutral", "confidence": 0-1 float, "keywords": ["kw1", "kw2", "kw3"]}}

Review: \"\"\"{review}\"\"\""""


def _extract_json(raw: str) -> dict[str, Any]:
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response: {raw[:120]}")
    return json.loads(match.group(0))


def _normalize(parsed: dict[str, Any]) -> dict[str, Any]:
    sentiment = str(parsed.get("sentiment", "Neutral")).strip().title()
    if sentiment not in VALID_SENTIMENTS:
        sentiment = "Neutral"

    try:
        confidence = float(parsed.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.0

    kws = parsed.get("keywords", [])
    if not isinstance(kws, list):
        kws = []
    kws = [str(k).strip() for k in kws if str(k).strip()][:5]

    return {"sentiment": sentiment, "confidence": confidence, "keywords": kws}


async def analyze_one(client: AsyncOpenAI, review: str, model: str) -> dict[str, Any]:
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_TEMPLATE.format(review=review)},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        return _normalize(_extract_json(content))
    except Exception as e:
        return {"sentiment": "Error", "confidence": 0.0, "keywords": [str(e)[:80]]}


async def analyze_many(
    api_key: str,
    base_url: str,
    model: str,
    reviews: list[str],
    progress_cb=None,
    concurrency: int = 8,
) -> list[dict[str, Any]]:
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    sem = asyncio.Semaphore(concurrency)
    results: list[dict[str, Any]] = [None] * len(reviews)  # type: ignore
    done = 0

    async def worker(i: int, text: str):
        nonlocal done
        async with sem:
            results[i] = await analyze_one(client, text, model)
        done += 1
        if progress_cb:
            progress_cb(done, len(reviews))

    await asyncio.gather(*(worker(i, r) for i, r in enumerate(reviews)))
    return [r or {"sentiment": "Error", "confidence": 0.0, "keywords": []} for r in results]


def run_analysis(api_key: str, base_url: str, model: str, reviews: list[str], progress_cb=None):
    return asyncio.run(analyze_many(api_key, base_url, model, reviews, progress_cb))