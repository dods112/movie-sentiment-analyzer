"""My List: movies the user saved.

Kept in st.session_state and mirrored to data/watchlist.json so it survives restarts.
The file is shared by everyone using the same deployment (there are no user accounts).
"""
import json
import os

import streamlit as st

WATCHLIST_PATH = "data/watchlist.json"
_KEY = "watchlist"


def _load() -> list:
    try:
        with open(WATCHLIST_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    return [t for t in data if isinstance(t, str)] if isinstance(data, list) else []


def _save(items: list):
    try:
        folder = os.path.dirname(WATCHLIST_PATH)
        if folder:
            os.makedirs(folder, exist_ok=True)
        tmp = WATCHLIST_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, WATCHLIST_PATH)
    except OSError:
        pass


def get_watchlist() -> list:
    """Saved movie titles, in the order they were added."""
    if _KEY not in st.session_state:
        st.session_state[_KEY] = _load()
    return st.session_state[_KEY]


def is_saved(title: str) -> bool:
    return title in get_watchlist()


def toggle(title: str):
    """Add or remove a movie. Safe to use as a button on_click callback."""
    items = list(get_watchlist())
    if title in items:
        items.remove(title)
    else:
        items.append(title)
    st.session_state[_KEY] = items
    _save(items)


def clear():
    st.session_state[_KEY] = []
    _save([])


def save_button(title: str, key: str, labels: tuple = ("Save", "Saved")):
    """Toggle button. Highlighted (primary) when the movie is on the list."""
    saved = is_saved(title)
    st.button(
        labels[1] if saved else labels[0], key=key, width="stretch",
        type="primary" if saved else "secondary",
        on_click=toggle, args=(title,),
    )


# ------------------------------------------------------------------ NEW: the page
def render_page(df, api_key: str, base_url: str, model: str):
    """My List page: grid of saved movies (reuses the Home card grid)."""
    from src.data import get_movie_aggregates
    from src.pages.home import COLUMNS_PER_ROW, render_card
    from src.posters import PLACEHOLDER, get_poster_urls, get_trailer_keys
    from src.ui import section_title

    section_title("My List")

    saved = get_watchlist()
    if not saved:
        st.markdown(
            "<div style='text-align:center;padding:60px 20px;'>"
            "<p style='font-size:1.1rem;color:#94a3b8;'>"
            "Nothing saved yet. Tap <b>Save</b> on any movie to add it here."
            "</p></div>",
            unsafe_allow_html=True,
        )
        return

    agg = get_movie_aggregates(df)
    rows = agg[agg["movie"].isin(saved)].copy()
    rows["__order"] = rows["movie"].map({m: i for i, m in enumerate(saved)})
    rows = rows.sort_values("__order").drop(columns="__order")
    rows = rows.to_dict("records")

    if not rows:
        st.info("Saved movies are no longer in the dataset.")
        return

    items = [(r["movie"], r["year"]) for r in rows]
    posters = get_poster_urls(items)
    trailers = get_trailer_keys(items)

    st.caption(f"{len(rows)} saved movie{'s' if len(rows) != 1 else ''}")

    col_clear, _ = st.columns([1, 4])
    with col_clear:
        if st.button("Clear all", key="wl_clear_all", width="stretch"):
            clear()
            st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    for start in range(0, len(rows), COLUMNS_PER_ROW):
        cols = st.columns(COLUMNS_PER_ROW, gap="medium")
        for offset, (col, row) in enumerate(zip(cols, rows[start:start + COLUMNS_PER_ROW])):
            with col:
                render_card(
                    row,
                    key=f"wl_{start + offset}_{row['movie']}",
                    poster_url=posters.get(row["movie"], PLACEHOLDER),
                    trailer_key=trailers.get(row["movie"]),
                )
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)