"""Movie Review Sentiment Analyzer - router for the 4-page app."""
import streamlit as st

from src.ui import apply_page_config, inject_css, inject_moviedb_css, render_topnav
from src.data import load_data

# --- Config ---
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]
MODEL = GROQ_MODELS[0]

apply_page_config()
inject_css()
inject_moviedb_css()

# --- Secrets ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except (KeyError, FileNotFoundError):
    GROQ_API_KEY = ""

# --- Router state ---
if "page" not in st.session_state:
    st.session_state["page"] = "Home"
if "selected_movie" not in st.session_state:
    st.session_state["selected_movie"] = None

if st.session_state["page"] == "Movie Detail" and not st.session_state["selected_movie"]:
    st.session_state["page"] = "Home"

# --- Handle banner / grid click: ?open_movie=Title ---
open_movie = st.query_params.get("open_movie")
if open_movie:
    st.session_state["selected_movie"] = open_movie
    st.session_state["page"] = "Movie Detail"
    st.query_params.clear()
    st.rerun()

# --- Data ---
df = load_data()

# --- Top nav ---
render_topnav(username="Merl")

nav_cols = st.columns([1, 1, 1, 1, 2])
nav_items = [
    ("Home", "nav_home"),
    ("Dashboard", "nav_dashboard"),
    ("Ask the Data", "nav_chat"),
    ("My List", "nav_watchlist"),
]
for col, (label, key) in zip(nav_cols, nav_items):
    with col:
        active = st.session_state["page"] == label or (
            label == "Home" and st.session_state["page"] == "Movie Detail"
        )
        if st.button(label, width="stretch", key=key,
                     type="primary" if active else "secondary"):
            st.session_state["page"] = label
            st.rerun()

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# --- Page routing ---
page = st.session_state["page"]

if page == "Home":
    from src.pages.home import render_page
    render_page(df, GROQ_API_KEY, GROQ_BASE_URL, MODEL)

elif page == "Movie Detail":
    from src.pages.movie_detail import render_page
    render_page(df, st.session_state["selected_movie"], GROQ_API_KEY, GROQ_BASE_URL, MODEL)

elif page == "Dashboard":
    from src.pages.dashboard import render_page
    render_page(df, GROQ_API_KEY, GROQ_BASE_URL, MODEL)

elif page == "Ask the Data":
    from src.pages.ask_data import render_page
    render_page(df, GROQ_API_KEY, GROQ_BASE_URL, MODEL)

elif page == "My List":
    from src.pages.watchlist import render_page
    render_page(df, GROQ_API_KEY, GROQ_BASE_URL, MODEL)

# --- Floating chat ---
if page != "Ask the Data":
    from src.floating_chat import render_floating_chat
    focus = st.session_state["selected_movie"] if page == "Movie Detail" else None
    render_floating_chat(df, GROQ_API_KEY, GROQ_BASE_URL, MODEL, focus_movie=focus)