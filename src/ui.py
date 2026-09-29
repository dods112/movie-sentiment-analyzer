"""Visual theme + reusable UI components. Cinematic dark, editorial, emoji-free."""
import html

import streamlit as st

SENTIMENT_COLORS = {
    "Positive": "#22c55e",
    "Negative": "#ef4444",
    "Neutral":  "#94a3b8",
    "Error":    "#f59e0b",
}


def _esc(value) -> str:
    """Escape text before putting it inside HTML (titles/reviews come from user data)."""
    return html.escape(str(value), quote=True)


def apply_page_config():
    st.set_page_config(
        page_title="Movie Review Sentiment Analyzer",
        page_icon="data:image/svg+xml,"
                  "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
                  "<rect width='32' height='32' rx='8' fill='%236d28d9'/>"
                  "<rect x='7' y='9' width='18' height='14' rx='2' fill='none' "
                  "stroke='white' stroke-width='1.8'/>"
                  "<circle cx='11' cy='13' r='1' fill='white'/>"
                  "<circle cx='21' cy='13' r='1' fill='white'/>"
                  "<circle cx='11' cy='19' r='1' fill='white'/>"
                  "<circle cx='21' cy='19' r='1' fill='white'/>"
                  "</svg>",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700;800&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 4rem;
            max-width: 1300px;
        }

        /* ---------- HERO ---------- */
        .hero {
            position: relative;
            background:
                radial-gradient(1200px 400px at 20% -10%, rgba(168,85,247,0.35), transparent 60%),
                radial-gradient(900px 400px at 90% 10%, rgba(219,39,119,0.28), transparent 55%),
                linear-gradient(135deg, #0f0f18 0%, #1a1026 60%, #0f0f18 100%);
            border: 1px solid rgba(168,85,247,0.25);
            border-radius: 24px;
            padding: 44px 48px;
            margin-bottom: 34px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(109,40,217,0.35),
                        inset 0 1px 0 rgba(255,255,255,0.05);
        }
        .hero h1 {
            font-family: 'Poppins', sans-serif;
            font-size: 2.3rem;
            font-weight: 800;
            letter-spacing: -0.6px;
            margin: 0 0 10px 0;
            background: linear-gradient(90deg, #ffffff, #e9d5ff 60%, #fbcfe8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero .subtitle {
            color: rgba(229,231,235,0.72);
            margin: 0;
            font-size: 1rem;
            max-width: 720px;
            line-height: 1.6;
        }
        .hero .eyebrow {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 2.4px;
            text-transform: uppercase;
            color: rgba(233,213,255,0.75);
            margin-bottom: 14px;
        }
        .hero-badges {
            margin-top: 22px;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .hero-badge {
            display: inline-block;
            background: rgba(168,85,247,0.12);
            border: 1px solid rgba(168,85,247,0.35);
            color: #e9d5ff;
            border-radius: 999px;
            padding: 6px 14px;
            font-size: 0.78rem;
            font-weight: 500;
            letter-spacing: 0.2px;
            backdrop-filter: blur(6px);
        }

        /* ---------- METRIC CARDS ---------- */
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(30,30,45,0.9), rgba(20,20,32,0.9));
            border-radius: 16px;
            padding: 18px 20px;
            border: 1px solid rgba(168,85,247,0.18);
            transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            border-color: rgba(168,85,247,0.5);
            box-shadow: 0 10px 30px rgba(168,85,247,0.18);
        }
        div[data-testid="stMetricLabel"] {
            color: rgba(229,231,235,0.65) !important;
            font-size: 0.78rem !important;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            font-weight: 600 !important;
        }
        div[data-testid="stMetricValue"] {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
        }

        /* ---------- TABS ---------- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: rgba(22,22,31,0.7);
            padding: 6px;
            border-radius: 14px;
            border: 1px solid rgba(168,85,247,0.15);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 10px 18px;
            font-weight: 600;
            color: rgba(229,231,235,0.6);
            background: transparent;
            letter-spacing: 0.2px;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(168,85,247,0.25), rgba(219,39,119,0.2)) !important;
            color: #ffffff !important;
        }

        /* ---------- SECTION TITLES ---------- */
        .section-title {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 1.05rem;
            letter-spacing: -0.2px;
            margin: 8px 0 14px 0;
            color: #f3f4f6;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-title::before {
            content: "";
            display: inline-block;
            width: 4px;
            height: 18px;
            border-radius: 2px;
            background: linear-gradient(180deg, #a855f7, #db2777);
        }

        /* ---------- POSTER CARDS ---------- */
        .poster-card {
            background: linear-gradient(180deg, rgba(30,30,45,0.85), rgba(15,15,25,0.85));
            border: 1px solid rgba(168,85,247,0.2);
            border-radius: 18px;
            overflow: hidden;
            transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
            height: 100%;
        }
        .poster-card:hover {
            transform: translateY(-6px) scale(1.02);
            border-color: rgba(219,39,119,0.6);
            box-shadow: 0 20px 40px rgba(219,39,119,0.25);
        }
        .poster-card img {
            width: 100%;
            display: block;
            aspect-ratio: 2 / 3;
            object-fit: cover;
        }
        .poster-card .meta { padding: 14px 16px; }
        .poster-card .title {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 0.95rem;
            color: #ffffff;
            margin: 0 0 4px 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .poster-card .sub {
            font-size: 0.76rem;
            color: rgba(229,231,235,0.55);
            letter-spacing: 0.2px;
        }
        .poster-card .pill {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 999px;
            margin-top: 10px;
            letter-spacing: 0.2px;
        }

        /* ---------- SIDEBAR ---------- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d0d15, #131320);
            border-right: 1px solid rgba(168,85,247,0.15);
        }
        section[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }
        section[data-testid="stSidebar"] h3 {
            font-family: 'Poppins', sans-serif;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: rgba(229,231,235,0.6);
        }

        /* ---------- BUTTONS ---------- */
        .stButton > button {
            border-radius: 12px;
            font-weight: 600;
            letter-spacing: 0.3px;
            transition: all .2s ease;
            border: 1px solid rgba(168,85,247,0.3);
        }
        .stButton > button:hover {
            border-color: rgba(219,39,119,0.7);
            box-shadow: 0 8px 24px rgba(168,85,247,0.25);
            transform: translateY(-1px);
        }

        /* ---------- EMPTY STATE ---------- */
        .empty-state {
            text-align: center;
            padding: 64px 24px;
            border-radius: 20px;
            border: 1.5px dashed rgba(168,85,247,0.35);
            background:
                radial-gradient(600px 200px at 50% 0%, rgba(168,85,247,0.12), transparent 70%),
                rgba(20,20,30,0.5);
        }
        .empty-state .eyebrow {
            font-size: 0.72rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: rgba(233,213,255,0.6);
            margin-bottom: 14px;
        }
        .empty-state .headline {
            font-family: 'Poppins', sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 10px;
        }
        .empty-state .body {
            color: rgba(229,231,235,0.6);
            max-width: 460px;
            margin: 0 auto;
            line-height: 1.6;
        }
        .empty-state .body b { color: #e9d5ff; font-weight: 600; }

        /* ---------- CHAT ---------- */
        .chat-answer {
            background: linear-gradient(135deg, rgba(109,40,217,0.15), rgba(219,39,119,0.08));
            border-left: 4px solid #a855f7;
            border-radius: 12px;
            padding: 16px 20px;
            margin-top: 12px;
            color: #e5e7eb;
            line-height: 1.65;
        }
        .chat-question-echo {
            font-size: 0.85rem;
            color: rgba(229,231,235,0.5);
            margin-top: 16px;
            font-style: italic;
        }

        /* ---------- MOBILE (general) ---------- */
        @media (max-width: 768px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
            .hero { padding: 28px 22px; border-radius: 18px; }
            .hero h1 { font-size: 1.7rem; }
            .empty-state { padding: 40px 18px; }
        }
    </style>
    """, unsafe_allow_html=True)


def render_hero():
    st.markdown(
        '<div class="hero">'
        '<div class="eyebrow">GenAI Sentiment Dashboard</div>'
        '<h1>Movie Review Sentiment Analyzer</h1>'
        '<p class="subtitle">Sentiment classification, keyword extraction, and trend '
        'visualization across your movie review dataset - powered by Groq.</p>'
        '<div class="hero-badges">'
        '<span class="hero-badge">Groq Inference</span>'
        '<span class="hero-badge">Poster Wall</span>'
        '<span class="hero-badge">Interactive Charts</span>'
        '<span class="hero-badge">Ask the Data</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )


def section_title(text: str):
    st.markdown(f'<div class="section-title">{_esc(text)}</div>', unsafe_allow_html=True)


def render_empty_state():
    st.markdown(
        '<div class="empty-state">'
        '<div class="eyebrow">Awaiting Analysis</div>'
        '<div class="headline">No results yet</div>'
        '<div class="body">Run <b>sentiment analysis</b> on the Dashboard, or post a '
        'review, to see results here.</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def sentiment_dot(color: str) -> str:
    """Return a small inline colored dot for use in labels."""
    return (
        f"<span style='display:inline-block;width:8px;height:8px;"
        f"border-radius:50%;background:{color};margin-right:8px;"
        f"vertical-align:middle;'></span>"
    )


def render_poster_card(title: str, year, genre: str, poster_url: str,
                       total: int, pos: int, neg: int, neu: int):
    total = max(total, 1)
    pos_pct, neg_pct, neu_pct = pos / total, neg / total, neu / total

    if pos >= neg and pos >= neu:
        label, color = f"Positive | {pos_pct:.0%}", SENTIMENT_COLORS["Positive"]
    elif neg >= pos and neg >= neu:
        label, color = f"Negative | {neg_pct:.0%}", SENTIMENT_COLORS["Negative"]
    else:
        label, color = f"Neutral | {neu_pct:.0%}", SENTIMENT_COLORS["Neutral"]

    year_txt = f" | {int(year)}" if year is not None and str(year) != "<NA>" else ""
    dot = sentiment_dot(color)

    st.markdown(
        '<div class="poster-card">'
        f'<img src="{_esc(poster_url)}" alt="{_esc(title)} poster" loading="lazy"/>'
        '<div class="meta">'
        f'<div class="title">{_esc(title)}</div>'
        f'<div class="sub">{_esc(genre)}{year_txt} | {total} review{"s" if total != 1 else ""}</div>'
        f'<span class="pill" style="background:{color}22; color:{color}; border:1px solid {color}66;">'
        f'{dot}{label}</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------
# MOVIE-DB STYLE TOP NAV + BACKDROP HERO
# ---------------------------------------------------------------

def inject_moviedb_css():
    """Extra CSS for the top-nav + backdrop hero look. Call once, after inject_css()."""
    st.markdown("""
    <style>
        /* ---------- TOP NAV ---------- */
        .topnav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 18px 8px;
        }
        .topnav .brand {
            font-family: 'Poppins', sans-serif;
            font-weight: 800;
            font-size: 1.25rem;
            letter-spacing: 1px;
            color: #ffffff;
        }
        .topnav .brand span { color: #a855f7; }
        .topnav .links {
            display: flex;
            gap: 28px;
        }
        .topnav .links a {
            color: rgba(229,231,235,0.75);
            text-decoration: none;
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: 1.2px;
            text-transform: uppercase;
        }
        .topnav .links a:hover { color: #a855f7; }
        .topnav .user {
            display: flex;
            align-items: center;
            gap: 10px;
            color: rgba(229,231,235,0.8);
            font-size: 0.85rem;
            font-weight: 600;
        }
        .topnav .avatar {
            width: 34px; height: 34px;
            border-radius: 50%;
            background: linear-gradient(135deg, #a855f7, #db2777);
            display: flex; align-items: center; justify-content: center;
            color: white; font-weight: 700; font-size: 0.85rem;
        }

        /* ---------- HIDE UNUSED SIDEBAR (navigation is the top bar) ---------- */
        section[data-testid="stSidebar"],
        div[data-testid="stSidebarCollapsedControl"],
        button[data-testid="stExpandSidebarButton"] { display: none !important; }

        /* ---------- ACTIVE NAV BUTTON (type="primary") ---------- */
        button[data-testid="stBaseButton-primary"], .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #7c3aed, #db2777) !important;
            color: #ffffff !important;
            border: 1px solid transparent !important;
        }

        /* ---------- MOVIE CARD (fixed-height slots so every row lines up) ---------- */
        .mcard img {
            width: 100%; display: block; aspect-ratio: 2 / 3; object-fit: cover;
            border-radius: 12px; box-shadow: 0 4px 14px rgba(0,0,0,0.45);
            transition: transform .2s ease, box-shadow .2s ease;
        }
        .mcard img:hover { transform: translateY(-3px); box-shadow: 0 12px 28px rgba(168,85,247,0.3); }
        .mcard .mtitle {
            font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 0.95rem;
            color: #ffffff; line-height: 1.3; margin-top: 10px;
            height: 2.6em; overflow: hidden;
            display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
        }
        .mcard .msub, .mcard .mrating {
            font-size: 0.78rem; color: rgba(229,231,235,0.6); margin-top: 2px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .mcard .mrating { color: #cbd5e1; margin-top: 6px; }
        .mcard .mslot { height: 30px; margin: 8px 0 10px; display: flex; align-items: center; }
        .mcard .mbadge {
            color: #ffffff; padding: 4px 10px; border-radius: 6px;
            font-size: 0.75rem; font-weight: 600;
        }
        .mcard .mbadge.muted { background: rgba(148,163,184,0.18); color: #94a3b8; }

        /* ---------- BACKDROP HERO ---------- */
        .backdrop-hero {
            position: relative;
            border-radius: 24px;
            overflow: hidden;
            margin-bottom: 30px;
            min-height: 460px;
            display: flex;
            align-items: flex-end;
            border: 1px solid rgba(168,85,247,0.2);
        }
        .backdrop-hero .bg-img {
            position: absolute; inset: 0;
            background-size: cover;
            background-position: center 20%;
            filter: brightness(0.55) saturate(1.1);
            transform: scale(1.02);
        }
        .backdrop-hero .bg-gradient {
            position: absolute; inset: 0;
            background: linear-gradient(0deg, rgba(10,10,15,0.97) 5%, rgba(10,10,15,0.55) 55%, rgba(10,10,15,0.15) 100%),
                        linear-gradient(90deg, rgba(10,10,15,0.75) 0%, transparent 55%);
        }
        .backdrop-hero .content {
            position: relative;
            padding: 40px 44px 34px 44px;
            width: 100%;
            box-sizing: border-box;
        }
        .backdrop-hero .eyebrow {
            color: rgba(233,213,255,0.85);
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .backdrop-hero h1 {
            font-family: 'Poppins', sans-serif;
            font-size: 2.6rem;
            font-weight: 800;
            color: #ffffff;
            margin: 0 0 10px 0;
            letter-spacing: -0.5px;
            text-shadow: 0 4px 20px rgba(0,0,0,0.5);
            overflow-wrap: anywhere;
        }
        .backdrop-hero .rating-row {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 14px;
            margin-bottom: 14px;
        }
        .backdrop-hero .star {
            color: #facc15;
            font-size: 1.1rem;
        }
        .backdrop-hero .rating-val {
            color: #ffffff;
            font-weight: 700;
            font-size: 1.05rem;
        }
        .backdrop-hero .meta-line {
            color: rgba(229,231,235,0.65);
            font-size: 0.82rem;
            letter-spacing: 0.3px;
        }
        .backdrop-hero .synopsis {
            color: rgba(229,231,235,0.85);
            max-width: 620px;
            line-height: 1.6;
            font-size: 0.95rem;
            margin: 16px 0;
        }
        .backdrop-hero .credit-line {
            font-size: 0.8rem;
            color: rgba(229,231,235,0.55);
            margin-top: 4px;
        }
        .backdrop-hero .credit-line b { color: rgba(233,213,255,0.85); font-weight: 600; }

        .backdrop-hero .play-btn {
            display: inline-block; margin-top: 16px; padding: 10px 20px;
            border-radius: 999px; font-weight: 700; font-size: 0.85rem;
            color: #ffffff !important; text-decoration: none !important;
            background: linear-gradient(135deg, #7c3aed, #db2777);
            box-shadow: 0 8px 22px rgba(124,58,237,0.45);
            transition: transform .15s ease;
        }
        .backdrop-hero .play-btn:hover { transform: translateY(-2px); }

        /* ---------- STAR RATING (fractional stars) ---------- */
        .stars {
            position: relative; display: inline-block; white-space: nowrap;
            color: rgba(148,163,184,0.35); letter-spacing: 1px; line-height: 1;
            vertical-align: middle; font-size: 0.95em;
        }
        .stars i {
            position: absolute; left: 0; top: 0; height: 100%; overflow: hidden;
            white-space: nowrap; color: #facc15; font-style: normal;
        }

        /* ---------- COMPACT HERO (home page banner) ---------- */
        .backdrop-hero.compact { min-height: 380px; margin-bottom: 14px; }
        .backdrop-hero.compact h1 { font-size: 2.2rem; }

        /* ---------- STAT STRIP ---------- */
        .stat-strip {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
            margin-top: -54px;
            position: relative;
            z-index: 5;
            padding: 0 44px;
            box-sizing: border-box;
        }
        .stat-card {
            border-radius: 16px;
            padding: 20px 22px;
            min-height: 100px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            box-shadow: 0 14px 30px rgba(0,0,0,0.35);
            border: 1px solid rgba(255,255,255,0.08);
            min-width: 0;
        }
        .stat-card .label {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: rgba(255,255,255,0.85);
            margin-bottom: 4px;
        }
        .stat-card .value {
            font-family: 'Poppins', sans-serif;
            font-size: 1.8rem;
            font-weight: 800;
            color: #ffffff;
        }

        /* ---------- RESPONSIVE ---------- */
        /* Tablets and phones: tighter hero, smaller cards (still 3 across). */
        @media (max-width: 768px) {
            .topnav { padding: 12px 4px; }
            .topnav .links { display: none; }

            .backdrop-hero { min-height: 340px; border-radius: 18px; }
            .backdrop-hero .content { padding: 24px 20px 44px 20px; }
            .backdrop-hero h1 { font-size: 1.7rem; }
            .backdrop-hero .synopsis { font-size: 0.88rem; margin: 10px 0; }

            .stat-strip { padding: 0 14px; gap: 8px; margin-top: -34px; }
            .stat-card { padding: 14px 12px; min-height: 76px; border-radius: 12px; }
            .stat-card .label { font-size: 0.6rem; letter-spacing: 1px; }
            .stat-card .value { font-size: 1.4rem; }
        }
        /* Very small phones: stack the three cards. */
        @media (max-width: 420px) {
            .stat-strip { grid-template-columns: 1fr; }
            .stat-card { min-height: 64px; }
        }
    </style>
    """, unsafe_allow_html=True)


def render_topnav(brand: str = "MOVIE DB", username: str = "Guest",
                  links: list[str] | None = None):
    """
    Brand + user badge. `links` is empty by default: the old default links were
    static (they did nothing), and real navigation is the Streamlit buttons under the bar.
    """
    links = links or []
    initial = _esc((username or "G")[0].upper())
    has_db = brand.endswith(" DB")
    brand_main = _esc(brand[:-3] if has_db else brand)
    brand_tail = " DB" if has_db else ""
    links_html = "".join(f'<a href="#">{_esc(l)}</a>' for l in links)
    st.markdown(
        '<div class="topnav">'
        f'<div class="brand">{brand_main}<span>{brand_tail}</span></div>'
        f'<div class="links">{links_html}</div>'
        f'<div class="user"><span>{_esc(username)}</span><div class="avatar">{initial}</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )


def star_rating(value, max_stars: int = 5) -> str:
    """Star icons for a rating, with partial fill (3.6 of 5 fills 72% of the row)."""
    try:
        v = max(0.0, min(float(value), float(max_stars)))
    except (TypeError, ValueError):
        v = 0.0
    pct = 100 * v / max_stars
    row = "&#9733;" * max_stars
    return (f'<span class="stars" role="img" aria-label="{v:.1f} out of {max_stars}">'
            f'{row}<i style="width:{pct:.0f}%">{row}</i></span>')


def render_backdrop_hero(title: str, backdrop_url: str, rating: float,
                         rating_count: int, meta_line: str, synopsis: str,
                         director: str = "", stars: str = "", trailer_url: str = "",
                         eyebrow: str = "Featured | GenAI Sentiment Spotlight",
                         compact: bool = False):
    """
    rating: 0-10 scale (the movie page passes avg 1-5 rating * 2)
    rating_count: number of reviews
    meta_line: e.g. "Action | 2010"
    """
    credits = ""
    if director:
        credits += f'<div class="credit-line"><b>Director:</b> {_esc(director)}</div>'
    if stars:
        credits += f'<div class="credit-line"><b>Stars:</b> {_esc(stars)}</div>'

    if trailer_url:
        credits += (f'<a class="play-btn" href="{_esc(trailer_url)}" target="_blank" '
                    'rel="noopener noreferrer">&#9654; Watch Trailer</a>')

    plural = "s" if rating_count != 1 else ""
    st.markdown(
        f'<div class="backdrop-hero{" compact" if compact else ""}">'
        f'<div class="bg-img" style="background-image:url(\'{_esc(backdrop_url)}\');"></div>'
        '<div class="bg-gradient"></div>'
        '<div class="content">'
        f'<div class="eyebrow">{_esc(eyebrow)}</div>'
        f'<h1>{_esc(title)}</h1>'
        '<div class="rating-row">'
        f'{star_rating(rating / 2)}'
        f'<span class="rating-val">{rating:.1f}/10</span>'
        f'<span class="meta-line">based on {rating_count} review{plural}</span>'
        '</div>'
        f'<div class="meta-line">{_esc(meta_line)}</div>'
        f'<div class="synopsis">{_esc(synopsis)}</div>'
        f'{credits}'
        '</div></div>',
        unsafe_allow_html=True,
    )


def render_stat_strip(stats: list[tuple[str, str, str]]):
    """
    stats: list of (label, value, css_gradient) tuples, e.g.
        [("Positive", "18", "linear-gradient(135deg,#16a34a,#22c55e)"), ...]
    """
    cards = "".join(
        f'<div class="stat-card" style="background:{grad};">'
        f'<div class="label">{_esc(label)}</div><div class="value">{_esc(value)}</div></div>'
        for label, value, grad in stats
    )
    st.markdown(f'<div class="stat-strip">{cards}</div>', unsafe_allow_html=True)