"""Dashboard page - filters, KPI cards, insight highlights and tabbed analytics."""
import html

import pandas as pd
import streamlit as st

from src import charts
from src.api import run_analysis
from src.data import VALID_SENTIMENTS, write_analysis
from src.ui import SENTIMENT_COLORS, section_title

DASH_CSS = """
<style>
.kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:14px; margin:4px 0 14px; }
.kpi {
    background:linear-gradient(180deg,rgba(30,30,45,0.9),rgba(20,20,32,0.9));
    border:1px solid rgba(168,85,247,0.18); border-top:3px solid var(--accent,#a855f7);
    border-radius:14px; padding:16px 18px; box-shadow:0 4px 20px rgba(0,0,0,0.25);
    transition:transform .2s ease, box-shadow .2s ease;
}
.kpi:hover { transform:translateY(-3px); box-shadow:0 10px 30px rgba(168,85,247,0.18); }
.kpi-label { font-size:0.72rem; font-weight:600; letter-spacing:0.6px; text-transform:uppercase; color:rgba(229,231,235,0.6); }
.kpi-value { font-family:'Poppins',sans-serif; font-weight:700; font-size:1.9rem; color:#fff; line-height:1.25; margin-top:4px; }
.kpi-sub { font-size:0.8rem; color:var(--accent,#a855f7); min-height:1.1em; }

.sent-bar { display:flex; height:12px; border-radius:999px; overflow:hidden; background:rgba(255,255,255,0.06); }
.sent-legend { display:flex; gap:18px; flex-wrap:wrap; margin:8px 0 6px; font-size:0.8rem; color:#cbd5e1; }
.sent-legend i { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; }

.insight-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px; margin:6px 0 10px; }
.insight {
    background:rgba(30,30,45,0.6); border:1px solid rgba(168,85,247,0.2);
    border-radius:14px; padding:14px 16px;
}
.insight-tag { font-size:0.7rem; font-weight:700; letter-spacing:0.8px; text-transform:uppercase; color:var(--accent,#a855f7); }
.insight-name { font-family:'Poppins',sans-serif; font-weight:700; color:#fff; font-size:1.02rem; margin:6px 0 2px; }
.insight-detail { font-size:0.82rem; color:#94a3b8; }
</style>
"""


# ------------------------------------------------------------------ analysis panel
def _analysis_panel(df: pd.DataFrame, api_key: str, base_url: str, model: str, expanded: bool):
    """Let the user run sentiment analysis on reviews that don't have it yet."""
    if "sentiment" in df.columns:
        pending = df[~df["sentiment"].isin(VALID_SENTIMENTS)]
    else:
        pending = df

    if pending.empty:
        return

    with st.expander(f"Analyze {len(pending)} unanalyzed review(s)", expanded=expanded):
        st.caption(
            "Runs the AI on reviews that have no sentiment yet (including ones that "
            "failed earlier) and saves the results to your CSV."
        )
        if not st.button("Run sentiment analysis", key="run_batch_analysis"):
            return
        if not api_key:
            st.error("No Groq API key found. Add GROQ_API_KEY to .streamlit/secrets.toml.")
            return

        bar = st.progress(0.0, text="Starting...")

        def on_progress(done: int, total: int):
            bar.progress(done / total, text=f"Analyzing {done}/{total}")

        rows = list(pending.itertuples(index=False))
        results = run_analysis(api_key, base_url, model, [r.review for r in rows], on_progress)

        ok, failed, last_error = {}, 0, ""
        for r, res in zip(rows, results):
            if res["sentiment"] == "Error":
                failed += 1
                last_error = res["keywords"][0] if res["keywords"] else ""
            else:
                ok[(str(r.review).strip(), str(r.movie).strip())] = res

        bar.empty()
        if ok and write_analysis(ok):
            msg = f"Analyzed and saved {len(ok)} review(s)."
            if failed:
                msg += f" {failed} failed and can be retried. ({last_error})"
            st.session_state["dash_flash"] = msg
            st.rerun()
        elif not ok:
            st.error(f"All {failed} analyses failed. ({last_error})")


# ------------------------------------------------------------------ small HTML helpers
def _kpi(label: str, value, sub: str = "", accent: str = "#a855f7") -> str:
    return (
        f'<div class="kpi" style="--accent:{accent};">'
        f'<div class="kpi-label">{html.escape(label)}</div>'
        f'<div class="kpi-value">{html.escape(str(value))}</div>'
        f'<div class="kpi-sub">{html.escape(sub)}</div></div>'
    )


def _insight(tag: str, name: str, detail: str, accent: str) -> str:
    return (
        f'<div class="insight" style="--accent:{accent};">'
        f'<div class="insight-tag">{html.escape(tag)}</div>'
        f'<div class="insight-name">{html.escape(name)}</div>'
        f'<div class="insight-detail">{html.escape(detail)}</div></div>'
    )


def _sentiment_bar(pos: int, neu: int, neg: int) -> str:
    total = max(pos + neu + neg, 1)
    parts = [("Positive", pos), ("Neutral", neu), ("Negative", neg)]
    segs = "".join(
        f'<div style="width:{100 * n / total:.2f}%;background:{SENTIMENT_COLORS[name]};"></div>'
        for name, n in parts if n
    )
    legend = "".join(
        f'<span><i style="background:{SENTIMENT_COLORS[name]};"></i>{name} {100 * n / total:.0f}%</span>'
        for name, n in parts
    )
    return f'<div class="sent-bar">{segs}</div><div class="sent-legend">{legend}</div>'


def _insights_html(d: pd.DataFrame) -> str:
    """Highlights computed from the filtered data."""
    by_movie = d.groupby("movie").agg(
        n=("review", "size"),
        pos=("sentiment", lambda s: (s == "Positive").mean()),
        neg=("sentiment", lambda s: (s == "Negative").mean()),
    )
    loved = by_movie.sort_values(["pos", "n"], ascending=False).iloc[0]
    loved_name = by_movie.sort_values(["pos", "n"], ascending=False).index[0]
    crit = by_movie.sort_values(["neg", "n"], ascending=False)
    busiest = by_movie.sort_values("n", ascending=False)

    cards = [
        _insight("Most loved", loved_name, f"{loved['pos']:.0%} positive, {int(loved['n'])} reviews",
                 SENTIMENT_COLORS["Positive"]),
    ]
    if crit.iloc[0]["neg"] > 0:
        cards.append(_insight("Most criticized", crit.index[0],
                              f"{crit.iloc[0]['neg']:.0%} negative, {int(crit.iloc[0]['n'])} reviews",
                              SENTIMENT_COLORS["Negative"]))
    cards.append(_insight("Most reviewed", busiest.index[0], f"{int(busiest.iloc[0]['n'])} reviews", "#a855f7"))

    if d["genre"].nunique() > 1:
        g = d.groupby("genre")["sentiment"].apply(lambda s: (s == "Positive").mean()).sort_values(ascending=False)
        cards.append(_insight("Happiest genre", str(g.index[0]), f"{g.iloc[0]:.0%} positive reviews", "#db2777"))

    return f'<div class="insight-grid">{"".join(cards)}</div>'


def _reset_filters():
    st.session_state["dash_genres"] = []
    st.session_state["dash_movies"] = []
    st.session_state["dash_sents"] = []


# ------------------------------------------------------------------ page
def render_page(df: pd.DataFrame, api_key: str, base_url: str, model: str):
    st.markdown(DASH_CSS, unsafe_allow_html=True)

    flash = st.session_state.pop("dash_flash", None)
    if flash:
        st.success(flash)

    if df.empty:
        st.info("No reviews yet. Add data/movie_reviews.csv first.")
        return

    if "sentiment" in df.columns:
        all_results = df[df["sentiment"].isin(VALID_SENTIMENTS)].copy()
    else:
        all_results = pd.DataFrame()

    _analysis_panel(df, api_key, base_url, model, expanded=all_results.empty)

    if all_results.empty:
        st.markdown(
            "<div style='text-align:center;padding:60px 20px;'>"
            "<p style='font-size:1.1rem;color:#94a3b8;'>"
            "No analyzed reviews yet. Analyze the existing ones above, or write a new review "
            "on a movie page."
            "</p></div>",
            unsafe_allow_html=True,
        )
        return

    # --- Filters ---
    f_genre, f_movie, f_sent, f_reset = st.columns([1.3, 1.6, 1.2, 0.6], vertical_alignment="bottom")
    sel_genres = f_genre.multiselect("Genre", sorted(all_results["genre"].unique()),
                                     placeholder="All genres", key="dash_genres")
    sel_movies = f_movie.multiselect("Movie", sorted(all_results["movie"].unique()),
                                     placeholder="All movies", key="dash_movies")
    sel_sents = f_sent.multiselect("Sentiment", VALID_SENTIMENTS,
                                   placeholder="All sentiments", key="dash_sents")
    f_reset.button("Reset", key="dash_reset", width="stretch", on_click=_reset_filters)

    results_df = all_results
    if sel_genres:
        results_df = results_df[results_df["genre"].isin(sel_genres)]
    if sel_movies:
        results_df = results_df[results_df["movie"].isin(sel_movies)]
    if sel_sents:
        results_df = results_df[results_df["sentiment"].isin(sel_sents)]

    st.caption(f"Showing {len(results_df)} of {len(all_results)} analyzed reviews "
               f"({len(df) - len(all_results)} not analyzed yet)")

    if results_df.empty:
        st.info("No reviews match these filters.")
        return

    # --- KPI cards ---
    total = len(results_df)
    pos = int((results_df["sentiment"] == "Positive").sum())
    neg = int((results_df["sentiment"] == "Negative").sum())
    neu = int((results_df["sentiment"] == "Neutral").sum())
    avg_conf = results_df["confidence"].mean() if "confidence" in results_df.columns else float("nan")
    avg_rating = results_df["rating"].mean() if "rating" in results_df.columns else float("nan")

    st.markdown(
        '<div class="kpi-grid">'
        + _kpi("Total reviews", total, f"{results_df['movie'].nunique()} movies", "#a855f7")
        + _kpi("Positive", pos, f"{pos / total:.0%}", SENTIMENT_COLORS["Positive"])
        + _kpi("Neutral", neu, f"{neu / total:.0%}", SENTIMENT_COLORS["Neutral"])
        + _kpi("Negative", neg, f"{neg / total:.0%}", SENTIMENT_COLORS["Negative"])
        + _kpi("Avg. confidence", f"{avg_conf:.0%}" if pd.notna(avg_conf) else "-", "AI certainty", "#db2777")
        + _kpi("Avg. rating", f"{avg_rating:.1f} / 5" if pd.notna(avg_rating) else "-", "star rating", "#f59e0b")
        + "</div>"
        + _sentiment_bar(pos, neu, neg),
        unsafe_allow_html=True,
    )

    section_title("Highlights")
    st.markdown(_insights_html(results_df), unsafe_allow_html=True)

    # --- Tabs ---
    tab_over, tab_movies, tab_genres, tab_kw, tab_data = st.tabs(
        ["Overview", "Movies", "Genres", "Keywords", "Data"]
    )

    with tab_over:
        col1, col2 = st.columns([1, 1.4], gap="large")
        with col1:
            section_title("Sentiment Distribution")
            st.plotly_chart(charts.sentiment_pie(results_df), width="stretch")
        with col2:
            section_title("Confidence Distribution")
            hist = charts.confidence_histogram(results_df) if "confidence" in results_df.columns else None
            if hist is not None:
                st.altair_chart(hist, width="stretch")
            else:
                st.info("No confidence scores available.")

        col3, col4 = st.columns(2, gap="large")
        with col3:
            section_title("Rating Distribution")
            dist = charts.rating_distribution(results_df)
            if dist is not None:
                st.altair_chart(dist, width="stretch")
            else:
                st.info("No star ratings available.")
        with col4:
            section_title("Reviews by Movie Release Year")
            line = charts.reviews_over_time(results_df)
            if line is not None:
                st.altair_chart(line, width="stretch")
            else:
                st.info("No release years available.")

    with tab_movies:
        section_title("Sentiment by Movie")
        st.altair_chart(charts.sentiment_by_movie(results_df), width="stretch")
        avg_chart = charts.avg_rating_by_movie(results_df)
        if avg_chart is not None:
            section_title("Average Rating by Movie")
            st.altair_chart(avg_chart, width="stretch")

    with tab_genres:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            section_title("Sentiment by Genre")
            st.plotly_chart(charts.sentiment_by_genre(results_df), width="stretch")
        with col2:
            section_title("Positive Rate by Genre")
            st.altair_chart(charts.positive_rate_by_genre(results_df), width="stretch")

    with tab_kw:
        section_title("Top Keywords")
        fig, counts = (None, None)
        if "keywords" in results_df.columns:
            fig, counts = charts.top_keywords(results_df)
        if fig is not None:
            st.plotly_chart(fig, width="stretch")
            with st.expander("Frequency table"):
                st.dataframe(counts, width="stretch", hide_index=True)
        else:
            st.info("No keywords extracted yet.")

    with tab_data:
        section_title("Full Results Table")
        st.dataframe(
            results_df,
            width="stretch",
            hide_index=True,
            column_config={
                "confidence": st.column_config.ProgressColumn(
                    "confidence", min_value=0, max_value=1, format="%.2f"
                ),
            },
        )
        st.download_button(
            "Download results as CSV",
            data=results_df.to_csv(index=False).encode("utf-8"),
            file_name="sentiment_results.csv",
            mime="text/csv",
        )