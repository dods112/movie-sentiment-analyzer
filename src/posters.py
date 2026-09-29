"""Fetch movie posters, backdrops and descriptions from TMDB - parallel, cached, graceful fallback."""
from concurrent.futures import ThreadPoolExecutor

import requests
import streamlit as st

TMDB_SEARCH = "https://api.themoviedb.org/3/search/movie"
TMDB_MOVIE = "https://api.themoviedb.org/3/movie"
TMDB_IMG = "https://image.tmdb.org/t/p/w342"
TMDB_BACKDROP = "https://image.tmdb.org/t/p/w1280"

NO_DESCRIPTION = "No description available for this movie yet."

# Emoji-free geometric fallback (soft gradient with diagonal lines)
PLACEHOLDER = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='342' height='513' viewBox='0 0 342 513'>"
    "<defs>"
    "<linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
    "<stop offset='0' stop-color='%236d28d9'/>"
    "<stop offset='1' stop-color='%23db2777'/>"
    "</linearGradient>"
    "<pattern id='p' width='20' height='20' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'>"
    "<line x1='0' y1='0' x2='0' y2='20' stroke='rgba(255,255,255,0.06)' stroke-width='2'/>"
    "</pattern>"
    "</defs>"
    "<rect width='100%25' height='100%25' fill='url(%23g)'/>"
    "<rect width='100%25' height='100%25' fill='url(%23p)'/>"
    "<text x='50%25' y='50%25' fill='rgba(255,255,255,0.75)' "
    "font-family='Poppins,sans-serif' font-size='22' font-weight='700' "
    "text-anchor='middle' dominant-baseline='middle' letter-spacing='2'>"
    "NO POSTER"
    "</text>"
    "</svg>"
)

# Process-wide cache shared by every session: (title, year) -> info dict.
# Only real answers are stored (including "TMDB has nothing for this title"),
# so a network hiccup is retried next time.
_CACHE: dict = {}


def _blank() -> dict:
    return {"id": None, "poster": PLACEHOLDER, "backdrop": None, "overview": ""}


def _tmdb_key() -> str:
    try:
        return st.secrets.get("TMDB_API_KEY", "")
    except Exception:  # no secrets.toml at all
        return ""


def _year(year):
    try:
        return int(year)
    except (TypeError, ValueError):
        return None


def _search(title: str, year, api_key: str) -> list:
    params = {"api_key": api_key, "query": title}
    if year:
        params["year"] = year
    r = requests.get(TMDB_SEARCH, params=params, timeout=6)
    r.raise_for_status()
    return r.json().get("results") or []


def _fetch(title: str, year, api_key: str):
    """Returns an info dict, or None on a transient error (so it is retried later)."""
    try:
        results = _search(title, year, api_key)
        if not results and year:
            # The year in the CSV may not match TMDB's release year: try once without it.
            results = _search(title, None, api_key)
    except Exception:
        return None

    if not results:
        return _blank()

    top = results[0]
    poster = top.get("poster_path")
    backdrop = top.get("backdrop_path")
    return {
        "id": top.get("id"),
        "poster": f"{TMDB_IMG}{poster}" if poster else PLACEHOLDER,
        "backdrop": f"{TMDB_BACKDROP}{backdrop}" if backdrop else None,
        "overview": (top.get("overview") or "").strip(),
    }


def get_movie_info(title: str, year=None) -> dict:
    """{"poster", "backdrop", "overview"} for one movie (never raises)."""
    api_key = _tmdb_key()
    if not api_key:
        return _blank()
    key = (title, _year(year))
    if key not in _CACHE:
        info = _fetch(title, key[1], api_key)
        if info is None:
            return _blank()
        _CACHE[key] = info
    return _CACHE[key]


def short_description(overview: str, limit: int = 420) -> str:
    """Trim a long description at a word boundary; empty text becomes a friendly fallback."""
    text = " ".join((overview or "").split())
    if not text:
        return NO_DESCRIPTION
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:-")
    return cut + "..."


def get_poster_url(title: str, year=None) -> str:
    return get_movie_info(title, year)["poster"]


def get_poster_urls(items) -> dict:
    """items: iterable of (title, year). Fetches uncached movies in parallel.
    Returns {title: poster_url}."""
    keys = [(t, _year(y)) for t, y in items]
    api_key = _tmdb_key()

    missing = [k for k in dict.fromkeys(keys) if k not in _CACHE]
    if missing and api_key:
        with ThreadPoolExecutor(max_workers=8) as pool:
            fetched = list(pool.map(lambda k: _fetch(k[0], k[1], api_key), missing))
        for k, info in zip(missing, fetched):
            if info is not None:
                _CACHE[k] = info

    return {t: _CACHE.get((t, y), _blank())["poster"] for t, y in keys}


# ---------------------------------------------------------------- cast, runtime, trailer
_DETAILS: dict = {}  # tmdb id -> details dict


def _blank_details() -> dict:
    return {"runtime": None, "cast": [], "director": "", "trailer": None}


def _fetch_details(movie_id, api_key: str):
    """One call returns details + credits + videos. None on a transient error (retried later)."""
    try:
        r = requests.get(
            f"{TMDB_MOVIE}/{movie_id}",
            params={"api_key": api_key, "append_to_response": "credits,videos"},
            timeout=6,
        )
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    credits = data.get("credits") or {}
    cast = [c["name"] for c in (credits.get("cast") or [])[:6] if c.get("name")]
    director = next((c["name"] for c in (credits.get("crew") or [])
                     if c.get("job") == "Director" and c.get("name")), "")

    videos = [v for v in ((data.get("videos") or {}).get("results") or [])
              if v.get("site") == "YouTube" and v.get("key")]
    trailers = [v for v in videos if v.get("type") == "Trailer"]
    pick = (next((v for v in trailers if v.get("official")), None)
            or (trailers[0] if trailers else None)
            or (videos[0] if videos else None))
    return {
        "runtime": data.get("runtime") or None,
        "cast": cast,
        "director": director,
        "trailer": f"https://www.youtube.com/watch?v={pick['key']}" if pick else None,
    }


def get_movie_details(title: str, year=None) -> dict:
    """{"runtime" (minutes), "cast" (names), "director", "trailer" (YouTube URL)}. Never raises."""
    api_key = _tmdb_key()
    movie_id = get_movie_info(title, year).get("id")
    if not api_key or not movie_id:
        return _blank_details()
    if movie_id not in _DETAILS:
        details = _fetch_details(movie_id, api_key)
        if details is None:
            return _blank_details()
        _DETAILS[movie_id] = details
    return _DETAILS[movie_id]


def format_runtime(minutes) -> str:
    """148 -> '2h 28m'; missing -> ''."""
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        return ""
    if m <= 0:
        return ""
    h, r = divmod(m, 60)
    return f"{h}h {r:02d}m" if h and r else f"{h}h" if h else f"{r}m"


def get_trailer_keys(items) -> dict:
    """items: iterable of (title, year). Returns {title: youtube_video_id or None}.
    Call after get_poster_urls (it reuses the TMDB ids found there); details are fetched
    in parallel and cached, so later reruns cost nothing."""
    keys = [(t, _year(y)) for t, y in items]
    api_key = _tmdb_key()
    if not api_key:
        return {t: None for t, _ in keys}

    ids = {k: (_CACHE.get(k) or {}).get("id") for k in keys}
    missing = list({i for i in ids.values() if i and i not in _DETAILS})
    if missing:
        with ThreadPoolExecutor(max_workers=8) as pool:
            fetched = list(pool.map(lambda i: _fetch_details(i, api_key), missing))
        for i, d in zip(missing, fetched):
            if d is not None:
                _DETAILS[i] = d

    out = {}
    for (title, year), k in zip(keys, keys):
        url = (_DETAILS.get(ids[k]) or {}).get("trailer") or ""
        out[title] = url.split("v=", 1)[1] if "v=" in url else None
    return out