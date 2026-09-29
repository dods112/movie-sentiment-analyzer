"""Groq API calls for sentiment analysis. Async + concurrent."""
import asyncio
import json
import re
from typing import Any

import openai
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


MAX_RETRIES = 6


def _retry_delay(err: Exception, attempt: int) -> float:
    """Seconds to wait after a 429: use Groq's 'try again in ...' hint, else exponential backoff."""
    m = re.search(r"try again in (\d+(?:\.\d+)?)(ms|s)\b", str(err))
    if m:
        wait = float(m.group(1)) / (1000 if m.group(2) == "ms" else 1)
        return min(wait + 0.5, 30)
    return min(2 ** attempt, 30)


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
    extra = {"reasoning_effort": "low"} if "gpt-oss" in model else {}  # fewer hidden tokens
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_TEMPLATE.format(review=review)},
                ],
                temperature=0,
                response_format={"type": "json_object"},
                extra_body=extra,
            )
            content = response.choices[0].message.content or ""
            return _normalize(_extract_json(content))
        except openai.RateLimitError as e:
            # A daily limit will not clear by waiting a few seconds, so give up right away.
            if "per day" in str(e).lower() or attempt == MAX_RETRIES:
                return {"sentiment": "Error", "confidence": 0.0, "keywords": [str(e)[:80]]}
            await asyncio.sleep(_retry_delay(e, attempt))
        except Exception as e:
            return {"sentiment": "Error", "confidence": 0.0, "keywords": [str(e)[:80]]}
    return {"sentiment": "Error", "confidence": 0.0, "keywords": ["retries exhausted"]}


async def analyze_many(
    api_key: str,
    base_url: str,
    model: str,
    reviews: list[str],
    progress_cb=None,
    concurrency: int = 3,
) -> list[dict[str, Any]]:
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, max_retries=0)
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