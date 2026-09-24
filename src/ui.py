"""Visual theme + reusable UI components. Cinematic dark, editorial, emoji-free."""
import streamlit as st

SENTIMENT_COLORS = {
    "Positive": "#22c55e",
    "Negative": "#ef4444",
    "Neutral":  "#94a3b8",
    "Error":    "#f59e0b",
}


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
        initial_sidebar_state="expanded",
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
    </style>
    """, unsafe_allow_html=True)


def render_hero():
    st.markdown("""
    <div class="hero">
        <div class="eyebrow">GenAI Sentiment Dashboard</div>
        <h1>Movie Review Sentiment Analyzer</h1>
        <p class="subtitle">
            Sentiment classification, keyword extraction, and trend visualization
            across your movie review dataset — powered by Groq.
        </p>
        <div class="hero-badges">
            <span class="hero-badge">Groq Inference</span>
            <span class="hero-badge">Poster Wall</span>
            <span class="hero-badge">Interactive Charts</span>
            <span class="hero-badge">Ask the Data</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_title(text: str):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def render_empty_state():
    st.markdown("""
    <div class="empty-state">
        <div class="eyebrow">Awaiting Analysis</div>
        <div class="headline">No results yet</div>
        <div class="body">
            Choose your filters in the sidebar, then run
            <b>GenAI Sentiment Analysis</b> to populate the dashboard.
        </div>
    </div>
    """, unsafe_allow_html=True)


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
        label, color = f"Positive · {pos_pct:.0%}", SENTIMENT_COLORS["Positive"]
    elif neg >= pos and neg >= neu:
        label, color = f"Negative · {neg_pct:.0%}", SENTIMENT_COLORS["Negative"]
    else:
        label, color = f"Neutral · {neu_pct:.0%}", SENTIMENT_COLORS["Neutral"]

    year_txt = f" · {int(year)}" if year is not None and str(year) != "<NA>" else ""
    dot = sentiment_dot(color)

    st.markdown(f"""
    <div class="poster-card">
        <img src="{poster_url}" alt="{title} poster" loading="lazy"/>
        <div class="meta">
            <div class="title">{title}</div>
            <div class="sub">{genre}{year_txt} · {total} review{'s' if total != 1 else ''}</div>
            <span class="pill" style="background:{color}22; color:{color}; border:1px solid {color}66;">
                {dot}{label}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)