"""Home page - featured banner + filter bar + paginated poster grid with loading skeletons."""
import html
import json
import traceback

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.data import get_movie_aggregates
from src.posters import (PLACEHOLDER, get_movie_details, get_movie_info,
                         get_poster_urls, get_trailer_keys, short_description)
from src.ui import star_rating
from src.pages.watchlist import save_button

COLUMNS_PER_ROW = 5
PAGE_SIZE = 20              # movies shown per page; "Load more" adds another page
MIN_REVIEWS_FEATURED = 3
FEATURED_COUNT = 5
POSTER_HEIGHT = 285

# False: cards use a plain <img> (fast). True: every card is an iframe with a hover trailer
# preview (nice, but 20+ iframes per page).
TRAILER_PREVIEWS = True

# "Highest rated" and "Most positive" use smoothed scores (see data.get_movie_aggregates),
# so a movie with one 5-star review no longer beats one with 40 good reviews.
SORTS = {
    "Most reviewed": ("review_count", False),
    "Highest rated": ("rating_score", False),
    "Most positive": ("pos_score", False),
    "Newest": ("year", False),
    "A - Z": ("movie", True),
}

SKELETON_CSS = """
<style>
@keyframes shimmer {
    0%   { background-position: -600px 0; }
    100% { background-position: 600px 0; }
}
.skel-card { margin-bottom: 12px; }
.skel-poster, .skel-line, .skel-banner {
    background: linear-gradient(90deg,
        rgba(30,30,45,0.6) 0%, rgba(60,60,90,0.7) 40%, rgba(30,30,45,0.6) 80%);
    background-size: 600px 100%;
    animation: shimmer 1.4s infinite linear;
}
.skel-poster { width: 100%; aspect-ratio: 2 / 3; border-radius: 12px; }
.skel-line { height: 12px; border-radius: 6px; margin-top: 10px; }
.skel-line.short { width: 60%; }
.skel-line.tiny  { width: 40%; height: 10px; margin-top: 8px; }
.skel-banner {
    width: 100%; height: 520px; border-radius: 24px;
    border: 1px solid rgba(168,85,247,0.15);
}
</style>
"""


def _render_skeleton_banner():
    st.markdown(SKELETON_CSS, unsafe_allow_html=True)
    st.markdown('<div class="skel-banner"></div>', unsafe_allow_html=True)


def _render_skeleton_grid(rows: int = 10):
    st.markdown(SKELETON_CSS, unsafe_allow_html=True)
    for start in range(0, rows, COLUMNS_PER_ROW):
        cols = st.columns(COLUMNS_PER_ROW, gap="medium")
        for col in cols:
            with col:
                st.markdown(
                    '<div class="skel-card"><div class="skel-poster"></div>'
                    '<div class="skel-line"></div><div class="skel-line short"></div>'
                    '<div class="skel-line tiny"></div></div>',
                    unsafe_allow_html=True,
                )


FILTER_CSS = """
<style>
div[data-testid="stTextInput"] input,
div[data-baseweb="select"] > div {
    background: rgba(30,30,45,0.75) !important;
    border: 1px solid rgba(168,85,247,0.28) !important;
    border-radius: 12px !important;
    color: #e5e7eb !important;
}
button[data-testid="stBaseButton-pills"], button[kind="pills"] {
    background: rgba(30,30,45,0.75) !important;
    border: 1px solid rgba(168,85,247,0.25) !important;
    color: #cbd5e1 !important;
    border-radius: 999px !important;
    padding: 4px 14px !important;
}
button[data-testid="stBaseButton-pillsActive"], button[kind="pillsActive"] {
    background: linear-gradient(135deg,#7c3aed,#db2777) !important;
    border: 1px solid transparent !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}
/* Buttons the banner clicks from JavaScript (no page reload). */
.st-key-banner_hidden { display: none !important; }
</style>
"""


def _empty(message: str):
    st.markdown(
        "<div style='text-align:center;padding:60px 20px;'>"
        f"<p style='font-size:1.2rem;color:#94a3b8;'>{html.escape(message)}</p></div>",
        unsafe_allow_html=True,
    )


def _reset_filters():
    st.session_state["home_search"] = ""
    st.session_state["home_genres"] = []
    st.session_state["home_sort"] = next(iter(SORTS))


def _more():
    st.session_state["home_shown"] = st.session_state.get("home_shown", PAGE_SIZE) + PAGE_SIZE


def _open_movie(title: str):
    st.session_state["selected_movie"] = title
    st.session_state["page"] = "Movie Detail"


def _genre_selector(genres: list, counts: dict) -> list:
    fmt = lambda g: f"{g} ({counts[g]})"
    if hasattr(st, "pills"):
        picked = st.pills(
            "Genre", genres, selection_mode="multi", format_func=fmt,
            key="home_genres", label_visibility="collapsed",
        )
        return list(picked or [])
    return st.multiselect(
        "Genre", genres, format_func=fmt, key="home_genres",
        placeholder="All genres", label_visibility="collapsed",
    )


BANNER_HTML = """
<!doctype html>
<html><head><meta charset="utf-8"><style>
  html, body { margin:0; padding:0; background:transparent; overflow:hidden;
               height: 520px;
               font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
  .stage { position: relative; width: 100%; height: 520px; border-radius: 24px;
           overflow: hidden; border: 1px solid rgba(168,85,247,0.25); background: #0a0a12; }
  .slide { position:absolute; inset:0; opacity:0; transition: opacity .5s ease;
           pointer-events:none; }
  .slide.on { opacity:1; pointer-events:auto; }
  .slide .bg { position:absolute; inset:0; background-size: cover;
    background-position: center 22%; filter: brightness(.55) saturate(1.05); }
  .slide .grad { position:absolute; inset:0; background:
      linear-gradient(0deg, rgba(10,10,15,.97) 4%, rgba(10,10,15,.55) 55%, rgba(10,10,15,.15) 100%),
      linear-gradient(180deg, rgba(10,10,15,.6) 0%, rgba(10,10,15,0) 18%),
      linear-gradient(90deg, rgba(10,10,15,.8) 0%, transparent 55%); }
  .slide iframe.trailer {
    position:absolute; inset:0; width: 200%; height: 200%; left: -50%; top: -50%;
    border:0; pointer-events:none; opacity:0; transition: opacity .5s ease; z-index: 1;
  }
  .slide.on iframe.trailer { opacity:1; }
  .slide .content { position:absolute; left:0; right:0; bottom:0;
    padding: 30px 44px 28px; z-index: 10; }
  .slide .eyebrow { font-size:.68rem; letter-spacing:2.4px; text-transform:uppercase;
    color: rgba(233,213,255,.85); font-weight:700; margin-bottom:8px; }
  .slide h2 { margin:0 0 10px 0; font-family:'Poppins', sans-serif; font-weight:800;
    color:#fff; font-size:2.2rem; letter-spacing:-.6px; line-height:1.1;
    overflow-wrap:anywhere; max-width: 720px; }
  .slide .row { display:flex; flex-wrap:wrap; align-items:center; gap:12px; margin-bottom:8px; }
  .slide .stars { color:#facc15; font-size:1.05rem; }
  .slide .rating { color:#fff; font-weight:700; font-size:1.05rem; }
  .slide .meta { color: rgba(229,231,235,.75); font-size:.82rem; }
  .slide .synopsis { color: rgba(229,231,235,.85); font-size:.92rem; line-height:1.55;
    max-width: 640px; margin: 10px 0 16px;
    display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
  .slide .actions { display:flex; gap:10px; flex-wrap:wrap; }
  .slide .btn { border:none; cursor:pointer; padding: 11px 22px; border-radius:999px;
    font-weight:700; font-size:.85rem; color:#fff;
    background: linear-gradient(135deg,#7c3aed,#db2777);
    box-shadow: 0 8px 22px rgba(124,58,237,.45); text-decoration:none; }
  .slide .btn.ghost { background: rgba(255,255,255,.08);
    border:1px solid rgba(255,255,255,.18); box-shadow:none; }
  .nav { position:absolute; top:50%; transform:translateY(-50%);
    width:46px; height:46px; border-radius:50%;
    background: rgba(20,20,32,.75); border:1px solid rgba(168,85,247,.35);
    color:#e9d5ff; font-size:22px; font-weight:700; cursor:pointer; z-index:20;
    display:flex; align-items:center; justify-content:center; }
  .nav.prev { left: 14px; } .nav.next { right: 14px; }
  .dots { position:absolute; bottom: 14px; left:0; right:0;
    display:flex; justify-content:center; gap:8px; z-index:20; }
  .dot { width:8px; height:8px; border-radius:50%;
    background: rgba(255,255,255,.3); transition: all .25s ease; cursor:pointer; }
  .dot.on { background:#a855f7; width:24px; border-radius:999px; }
</style></head><body>
<div class="stage" id="stage">
  <button class="nav prev" id="prev" aria-label="Previous">&#8249;</button>
  <button class="nav next" id="next" aria-label="Next">&#8250;</button>
  <div class="dots" id="dots"></div>
</div>
<script>
const MOVIES = __MOVIES__;
const stage = document.getElementById('stage');
const dotsEl = document.getElementById('dots');
const slides = []; const dots = []; const players = {};
let current = -1;
function esc(s){ return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function openMovie(i, title) {
  // Preferred: click a hidden Streamlit button (keeps the session, no page reload).
  try {
    const b = window.parent.document.querySelector('.st-key-banner_open_' + i + ' button');
    if (b) { b.click(); return; }
  } catch (e) {}
  // Fallback: the old query-param route (reloads the app).
  const url = new URL(window.parent.location.href);
  url.searchParams.set('open_movie', title);
  window.parent.location.href = url.toString();
}
function makeSlide(m, i) {
  const el = document.createElement('div');
  el.className = 'slide';
  el.innerHTML = `
    <div class="bg" style="background-image:url('${esc(m.backdrop)}');"></div>
    <div class="grad"></div>
    <div class="content">
      <div class="eyebrow">${esc(m.eyebrow)}</div>
      <h2>${esc(m.title)}</h2>
      <div class="row">
        <span class="stars">${m.stars_html}</span>
        <span class="rating">${esc(m.rating)}</span>
        <span class="meta">${esc(m.meta)}</span>
      </div>
      <div class="synopsis">${esc(m.synopsis)}</div>
      <div class="actions">
        <button class="btn" data-open="1">View reviews</button>
        ${m.trailer ? `<a class="btn ghost" href="${esc(m.trailer)}" target="_blank" rel="noopener">Watch on YouTube</a>` : ``}
      </div>
    </div>`;
  el.querySelector('[data-open]').addEventListener('click', (ev) => {
    ev.preventDefault(); ev.stopPropagation();
    openMovie(i, m.title);
  });
  return el;
}
function ensurePlayer(i) {
  const key = MOVIES[i] && MOVIES[i].trailer_key;
  if (!key || players[i]) return;
  const f = document.createElement('iframe');
  f.className = 'trailer'; f.allow = 'autoplay; encrypted-media';
  f.src = `https://www.youtube.com/embed/${encodeURIComponent(key)}?autoplay=1&mute=1&controls=0&loop=1&playlist=${encodeURIComponent(key)}&modestbranding=1&playsinline=1&rel=0&showinfo=0&iv_load_policy=3`;
  slides[i].insertBefore(f, slides[i].querySelector('.content'));
  players[i] = f;
}
function goTo(i) {
  if (i === current) return;
  i = Math.max(0, Math.min(slides.length - 1, i));
  slides.forEach((s, k) => s.classList.toggle('on', k === i));
  dots.forEach((d, k) => d.classList.toggle('on', k === i));
  current = i; ensurePlayer(i);
}
MOVIES.forEach((m, i) => {
  const s = makeSlide(m, i); stage.appendChild(s); slides.push(s);
  const d = document.createElement('div'); d.className = 'dot';
  d.addEventListener('click', () => goTo(i));
  dotsEl.appendChild(d); dots.push(d);
});
document.getElementById('prev').addEventListener('click', () => goTo(current - 1));
document.getElementById('next').addEventListener('click', () => goTo(current + 1));
goTo(0);
</script></body></html>
"""


def _featured_rows(agg: pd.DataFrame, n: int) -> list:
    """Top movies by smoothed rating, so the banner label 'Top rated' is true."""
    pool = agg[agg["review_count"] >= MIN_REVIEWS_FEATURED]
    if pool.empty:
        pool = agg
    pool = pool.sort_values(["rating_score", "pos_score", "review_count"], ascending=False)
    return pool.head(n).to_dict("records")


def _build_banner_movies(rows: list, trailers: dict) -> list:
    out = []
    for row in rows:
        title = str(row["movie"])
        year = row.get("year")
        year_int = int(year) if pd.notna(year) else None
        genre = str(row.get("genre") or "")
        avg_rating = float(row["avg_rating"])
        meta = " | ".join(p for p in (genre, str(year_int) if year_int else "") if p)

        try:
            info = get_movie_info(title, year_int)
        except Exception:
            info = {"backdrop": None, "poster": None, "overview": ""}
        try:
            details = get_movie_details(title, year_int)
        except Exception:
            details = {"runtime": None, "trailer": None}

        backdrop = info.get("backdrop") or info.get("poster") or PLACEHOLDER
        synopsis = short_description(info.get("overview", ""), 260)

        out.append({
            "title": title,
            "backdrop": backdrop,
            "eyebrow": "Top rated by reviewers",
            "rating": f"{avg_rating * 2:.1f}/10",
            "stars_html": star_rating(avg_rating),
            "meta": f"{meta} | {int(row['review_count'])} reviews",
            "synopsis": synopsis,
            "trailer": details.get("trailer") or "",
            "trailer_key": trailers.get(title) or "",
        })
    return out


def _render_featured_banner(rows: list, trailers: dict) -> bool:
    try:
        movies = _build_banner_movies(rows, trailers)
    except Exception as e:
        st.error(f"Feature build failed: {e}")
        st.code(traceback.format_exc())
        return False

    if not movies:
        return False

    doc = BANNER_HTML.replace("__MOVIES__", json.dumps(movies, ensure_ascii=False))
    components.html(doc, height=520, scrolling=False)

    # Hidden buttons the banner triggers from JS; they run the callback in the same session.
    with st.container(key="banner_hidden"):
        for i, m in enumerate(movies):
            st.button(m["title"], key=f"banner_open_{i}",
                      on_click=_open_movie, args=(m["title"],))
    return True


PLAYER_HTML = """
<style>
html,body{margin:0;height:100%;background:transparent;overflow:hidden}
#box{position:relative;width:100%;height:100%;border-radius:12px;overflow:hidden;
     background:#12121c;cursor:pointer}
#box img{width:100%;height:100%;object-fit:cover;display:block}
#box iframe{position:absolute;top:0;left:50%;transform:translateX(-50%);
            height:100%;aspect-ratio:16/9;border:0;pointer-events:none}
.tag{position:absolute;left:8px;bottom:8px;background:rgba(0,0,0,.65);color:#fff;
     font:600 11px Inter,Arial,sans-serif;padding:4px 9px;border-radius:999px}
</style>
<div id="box"><img src="__POSTER__" alt="__ALT__"><span class="tag" id="tag"></span></div>
<script>
const KEY="__KEY__", box=document.getElementById('box'), tag=document.getElementById('tag');
let frame=null, timer=null;
tag.textContent = KEY ? 'Trailer' : '';
tag.style.display = KEY ? 'block' : 'none';
function play(){ if(frame||!KEY) return;
  frame=document.createElement('iframe');
  frame.src='https://www.youtube.com/embed/'+KEY+'?autoplay=1&mute=1&controls=0&loop=1&playlist='+KEY+'&modestbranding=1&playsinline=1&rel=0';
  frame.allow='autoplay; encrypted-media';
  box.insertBefore(frame, tag); tag.textContent='Muted preview'; }
function stop(){ clearTimeout(timer); if(frame){frame.remove(); frame=null;} if(KEY) tag.textContent='Trailer'; }
if(KEY){
  box.addEventListener('mouseenter',()=>{timer=setTimeout(play,350);});
  box.addEventListener('mouseleave',stop);
  box.addEventListener('click',()=>frame?stop():play());
}
</script>
"""


def _poster_player(poster_url: str, title: str, trailer_key):
    doc = (PLAYER_HTML
           .replace("__POSTER__", html.escape(poster_url or PLACEHOLDER, quote=True))
           .replace("__ALT__", html.escape(title, quote=True))
           .replace("__KEY__", html.escape(trailer_key or "", quote=True)))
    components.html(doc, height=POSTER_HEIGHT, scrolling=False)


def _poster_image(poster_url: str, title: str):
    """Lightweight poster: a plain lazy-loaded <img> (styled by .mcard img in ui.py)."""
    st.markdown(
        '<div class="mcard">'
        f'<img src="{html.escape(poster_url or PLACEHOLDER, quote=True)}" '
        f'alt="{html.escape(title, quote=True)} poster" loading="lazy"/></div>',
        unsafe_allow_html=True,
    )


def render_card(row: dict, key: str, poster_url: str, trailer_key=None):
    title = html.escape(str(row["movie"]))
    year = row.get("year")
    year_int = int(year) if pd.notna(year) else None
    genre = html.escape(str(row.get("genre") or ""))
    sub = f"{year_int} | {genre}" if year_int else genre

    avg_rating = float(row.get("avg_rating") or 0)
    rating_txt = (f"{star_rating(avg_rating)} {avg_rating:.1f}" if avg_rating > 0
                  else "No rating")
    count = int(row["review_count"])
    plural = "s" if count != 1 else ""

    analyzed = int(row["positive"]) + int(row["negative"]) + int(row["neutral"])
    if analyzed > 0:
        pos_pct = round(100 * int(row["positive"]) / analyzed)
        color = "#22c55e" if pos_pct >= 60 else "#f59e0b" if pos_pct >= 40 else "#ef4444"
        badge = f'<span class="mbadge" style="background:{color};">{pos_pct}% positive</span>'
    else:
        badge = '<span class="mbadge muted">Not analyzed</span>'

    if TRAILER_PREVIEWS:
        _poster_player(poster_url, str(row["movie"]), trailer_key)
    else:
        _poster_image(poster_url, str(row["movie"]))

    st.markdown(
        '<div class="mcard">'
        f'<div class="mtitle" title="{title}">{title}</div>'
        f'<div class="msub">{sub}</div>'
        f'<div class="mrating">{rating_txt} | {count} review{plural}</div>'
        f'<div class="mslot">{badge}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_view, col_save = st.columns(2, gap="small")
    with col_view:
        st.button("View", width="stretch", key=key,
                  on_click=_open_movie, args=(str(row["movie"]),))
    with col_save:
        save_button(str(row["movie"]), key=f"{key}_save")


def render_grid(rows: list, posters: dict, trailers: dict, key_prefix: str = "movie"):
    for start in range(0, len(rows), COLUMNS_PER_ROW):
        cols = st.columns(COLUMNS_PER_ROW, gap="medium")
        for offset, (col, row) in enumerate(zip(cols, rows[start:start + COLUMNS_PER_ROW])):
            with col:
                render_card(
                    row,
                    key=f"{key_prefix}_{start + offset}_{row['movie']}",
                    poster_url=posters.get(row["movie"], PLACEHOLDER),
                    trailer_key=trailers.get(row["movie"]),
                )
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)


def _fetch_media(items: list, want_trailers: bool):
    """Posters (and optionally trailer keys) for just these (title, year) pairs."""
    try:
        posters = get_poster_urls(items)
    except Exception as e:
        posters = {}
        st.warning(f"TMDB poster fetch failed: {e}")
    trailers = {}
    if want_trailers:
        try:
            trailers = get_trailer_keys(items)  # call after get_poster_urls (reuses TMDB ids)
        except Exception as e:
            st.warning(f"TMDB trailer fetch failed: {e}")
    return posters, trailers


def render_page(df: pd.DataFrame, api_key: str, base_url: str, model: str):
    agg = get_movie_aggregates(df)

    if agg.empty:
        _empty("No movies yet. Add data/movie_reviews.csv to get started.")
        return

    st.markdown(FILTER_CSS, unsafe_allow_html=True)
    cache_ready = bool(st.session_state.get("_posters_loaded"))

    # --- Featured banner (only when no search/genre filter is active) ---
    if not (st.session_state.get("home_search", "").strip()
            or st.session_state.get("home_genres")):
        banner_slot = st.empty()
        if not cache_ready:
            with banner_slot.container():
                _render_skeleton_banner()
        featured = _featured_rows(agg, FEATURED_COUNT)
        _, banner_trailers = _fetch_media([(r["movie"], r["year"]) for r in featured], True)
        banner_slot.empty()
        _render_featured_banner(featured, banner_trailers)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # --- Filters ---
    genre_counts = agg["genre"].value_counts().to_dict()
    genres = sorted(genre_counts)

    col_search, col_sort = st.columns([3, 1.2])
    with col_search:
        search_query = st.text_input(
            "Search movies", placeholder="Search by title...",
            label_visibility="collapsed", key="home_search",
        )
    with col_sort:
        sort_label = st.selectbox(
            "Sort by", list(SORTS), key="home_sort", label_visibility="collapsed",
        )

    selected_genres = _genre_selector(genres, genre_counts)

    filtered = agg
    if selected_genres:
        filtered = filtered[filtered["genre"].isin(selected_genres)]
    query = search_query.strip()
    if query:
        filtered = filtered[filtered["movie"].str.contains(query, case=False, na=False, regex=False)]

    sort_col, ascending = SORTS[sort_label]
    filtered = filtered.sort_values(
        [sort_col, "movie"], ascending=[ascending, True], na_position="last"
    )

    # Start again from page 1 whenever the filters or sort change.
    sig = (query, tuple(selected_genres), sort_label)
    if st.session_state.get("_home_sig") != sig:
        st.session_state["_home_sig"] = sig
        st.session_state["home_shown"] = PAGE_SIZE
    shown = st.session_state.setdefault("home_shown", PAGE_SIZE)

    filters_active = bool(selected_genres or query)
    col_count, col_clear = st.columns([5, 1])
    with col_count:
        st.caption(f"Showing {min(shown, len(filtered))} of {len(filtered)} movies "
                   f"({len(agg)} total)")
    with col_clear:
        if filters_active:
            st.button("Clear filters", width="stretch", key="home_clear", on_click=_reset_filters)

    if filtered.empty:
        st.info("No movies match your filters.")
        return

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # --- Grid: fetch posters only for the movies on screen ---
    rows = filtered.to_dict("records")
    visible = rows[:shown]
    items = [(r["movie"], r["year"]) for r in visible]

    grid_slot = st.empty()
    if not cache_ready:
        with grid_slot.container():
            _render_skeleton_grid(rows=10)
    posters, trailers = _fetch_media(items, TRAILER_PREVIEWS)
    grid_slot.empty()
    st.session_state["_posters_loaded"] = True

    render_grid(visible, posters, trailers)

    if len(rows) > shown:
        col_more, _ = st.columns([1, 3])
        with col_more:
            st.button(f"Load more ({len(rows) - shown} left)", key="home_more",
                      width="stretch", on_click=_more)