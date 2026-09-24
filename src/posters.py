"""Fetch movie posters from TMDB with graceful fallback."""
import requests
import streamlit as st

TMDB_SEARCH = "https://api.themoviedb.org/3/search/movie"
TMDB_IMG = "https://image.tmdb.org/t/p/w342"

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


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def get_poster_url(title: str, year: int | None = None) -> str:
    api_key = st.secrets.get("TMDB_API_KEY", "")
    if not api_key:
        return PLACEHOLDER

    params = {"api_key": api_key, "query": title}
    if year:
        params["year"] = int(year)

    try:
        r = requests.get(TMDB_SEARCH, params=params, timeout=6)
        r.raise_for_status()
        results = r.json().get("results") or []
        if not results:
            return PLACEHOLDER
        path = results[0].get("poster_path")
        return f"{TMDB_IMG}{path}" if path else PLACEHOLDER
    except Exception:
        return PLACEHOLDER