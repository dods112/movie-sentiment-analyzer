"""Movie Review Sentiment Analyzer — main app. Emoji-free."""
import pandas as pd
import streamlit as st

from src.ui import (
    SENTIMENT_COLORS,
    apply_page_config, inject_css, render_hero,
    section_title, render_empty_state, render_poster_card,
)
from src.data import load_data
from src.api import run_analysis
from src.posters import get_poster_url
from src import charts
from src.chatbot import render_chatbot

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]

# --- Init ---
apply_page_config()
inject_css()
render_hero()

# --- Secrets ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except (KeyError, FileNotFoundError):
    GROQ_API_KEY = ""

# --- Data ---
df = load_data()

# --- Sidebar: model + filters only ---
with st.sidebar:
    groq_model = st.selectbox("Model", options=GROQ_MODELS, index=0)

    st.markdown("---")

    all_genres = sorted(df["genre"].unique())
    all_movies = sorted(df["movie"].unique())

    if "genre_filter" not in st.session_state:
        st.session_state["genre_filter"] = all_genres
    if "movie_filter" not in st.session_state:
        st.session_state["movie_filter"] = all_movies

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Select all", use_container_width=True):
            st.session_state["genre_filter"] = all_genres
            st.session_state["movie_filter"] = all_movies
    with col_b:
        if st.button("Clear all", use_container_width=True):
            st.session_state["genre_filter"] = []
            st.session_state["movie_filter"] = []

    genre_filter = st.multiselect("Genre", options=all_genres, key="genre_filter")
    movie_filter = st.multiselect("Movie", options=all_movies, key="movie_filter")

# --- Filter the data ---
filtered_df = df[df["genre"].isin(genre_filter) & df["movie"].isin(movie_filter)]

# --- Reviews Selected card ---
st.markdown(f"""
<div style="
    background: linear-gradient(180deg, rgba(30,30,45,0.7), rgba(20,20,32,0.7));
    border: 1px solid rgba(168,85,247,0.18);
    border-radius: 16px;
    padding: 22px 26px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
">
    <div>
        <div style="
            font-size: 0.72rem;
            letter-spacing: 2.4px;
            text-transform: uppercase;
            color: rgba(229,231,235,0.55);
            font-weight: 600;
            margin-bottom: 6px;
        ">Reviews Selected</div>
        <div style="
            font-family: 'Poppins', sans-serif;
            font-size: 2.1rem;
            font-weight: 700;
            color: #ffffff;
            line-height: 1;
        ">{len(filtered_df)}</div>
    </div>
    <div style="
        text-align: right;
        font-size: 0.82rem;
        color: rgba(229,231,235,0.55);
        line-height: 1.6;
    ">
        of {len(df)} total reviews<br>
        {len(genre_filter)} genre(s) · {len(movie_filter)} movie(s)
    </div>
</div>
""", unsafe_allow_html=True)

# --- Run button ---
run_button = st.button(
    "Run GenAI Sentiment Analysis",
    type="primary",
    use_container_width=True,
    key="run_analysis_btn",
)

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

# --- Analysis trigger ---
if run_button:
    if not GROQ_API_KEY:
        st.error("No Groq API key found. Add `GROQ_API_KEY` to `.streamlit/secrets.toml`.")
    elif filtered_df.empty:
        st.warning("No reviews match your current filters.")
    else:
        reviews = filtered_df["review"].tolist()
        progress = st.progress(0.0, text="Starting analysis...")

        def cb(done, total):
            progress.progress(done / total, text=f"Analyzing review {done} of {total}...")

        results = run_analysis(
            GROQ_API_KEY, GROQ_BASE_URL, groq_model, reviews, progress_cb=cb,
        )
        progress.empty()

        results_df = filtered_df.reset_index(drop=True).copy()
        results_df["sentiment"] = [r["sentiment"] for r in results]
        results_df["confidence"] = [r["confidence"] for r in results]
        results_df["keywords"] = [", ".join(r["keywords"]) for r in results]

        st.session_state["results_df"] = results_df
        st.rerun()

# =========================================================
# 2 TABS: Dashboard + Ask the Data
# =========================================================
tab_dashboard, tab_chat = st.tabs(["Dashboard", "Ask the Data"])

# ---------------------------------------------------------
# TAB 1: Dashboard
# ---------------------------------------------------------
with tab_dashboard:
    if "results_df" not in st.session_state:
        render_empty_state()
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Preview dataset before analysis", expanded=True):
            st.dataframe(filtered_df, use_container_width=True)
            st.caption(f"{len(filtered_df)} reviews shown out of {len(df)} total.")
    else:
        results_df = st.session_state["results_df"]
        total = len(results_df)
        pos = int((results_df["sentiment"] == "Positive").sum())
        neg = int((results_df["sentiment"] == "Negative").sum())
        neu = int((results_df["sentiment"] == "Neutral").sum())
        avg_conf = results_df["confidence"].mean()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total reviews", total)
        m2.metric("Positive", pos, f"{pos/total:.0%}" if total else "0%")
        m3.metric("Negative", neg, f"{neg/total:.0%}" if total else "0%")
        m4.metric("Neutral", neu, f"{neu/total:.0%}" if total else "0%")
        m5.metric("Avg. confidence",
                  f"{avg_conf:.0%}" if pd.notna(avg_conf) else "—")

        st.markdown("<br>", unsafe_allow_html=True)

        # Movie Spotlight (poster wall)
        section_title("Movie Spotlight")
        movie_meta = (
            results_df.groupby(["movie", "genre", "year"], dropna=False)
            .size().reset_index(name="total")
        )
        piv = (
            results_df.groupby(["movie", "sentiment"]).size()
            .unstack(fill_value=0).reset_index()
        )
        for s in ("Positive", "Negative", "Neutral"):
            if s not in piv.columns:
                piv[s] = 0
        movie_meta = movie_meta.merge(piv, on="movie", how="left")

        cols = st.columns(5, gap="medium")
        for i, row in movie_meta.iterrows():
            poster = get_poster_url(row["movie"], row.get("year"))
            with cols[i % 5]:
                render_poster_card(
                    title=row["movie"],
                    year=row.get("year"),
                    genre=row["genre"],
                    poster_url=poster,
                    total=int(row["total"]),
                    pos=int(row["Positive"]),
                    neg=int(row["Negative"]),
                    neu=int(row["Neutral"]),
                )
            if (i + 1) % 5 == 0 and i + 1 < len(movie_meta):
                cols = st.columns(5, gap="medium")
                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        # Sentiment Distribution + Confidence
        col1, col2 = st.columns([1, 1.4])
        with col1:
            section_title("Sentiment Distribution")
            st.plotly_chart(charts.sentiment_pie(results_df),
                            use_container_width=True)
        with col2:
            section_title("Confidence Distribution")
            hist = charts.confidence_histogram(results_df)
            if hist is not None:
                st.altair_chart(hist, use_container_width=True)
            else:
                st.info("No confidence scores available.")

        st.markdown("<br>", unsafe_allow_html=True)

        section_title("Sentiment by Movie")
        st.altair_chart(charts.sentiment_by_movie(results_df),
                        use_container_width=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            section_title("Sentiment by Genre")
            st.plotly_chart(charts.sentiment_by_genre(results_df),
                            use_container_width=True)
        with col2:
            section_title("Positive Rate by Genre")
            st.altair_chart(charts.positive_rate_by_genre(results_df),
                            use_container_width=True)

        line = charts.reviews_over_time(results_df)
        if line is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            section_title("Reviews Over Time")
            st.altair_chart(line, use_container_width=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        section_title("Top Keywords")
        fig, counts = charts.top_keywords(results_df)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("Quick frequency table"):
                st.bar_chart(counts.set_index("Keyword"))
        else:
            st.info("No keywords extracted yet.")

        st.markdown("<br><br>", unsafe_allow_html=True)

        section_title("Full Results Table")
        st.dataframe(
            results_df,
            use_container_width=True,
            column_config={
                "confidence": st.column_config.ProgressColumn(
                    "confidence", min_value=0, max_value=1, format="%.2f",
                ),
            },
        )
        st.download_button(
            "Download results as CSV",
            data=results_df.to_csv(index=False).encode("utf-8"),
            file_name="sentiment_results.csv",
            mime="text/csv",
        )

# ---------------------------------------------------------
# TAB 2: Ask the Data (Messenger-style)
# ---------------------------------------------------------
with tab_chat:
    context_df = st.session_state.get("results_df", filtered_df)
    render_chatbot(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        model=groq_model,
        context_df=context_df,
    )