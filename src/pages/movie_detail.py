"""Movie Detail page - reviews + write-a-review + AI summary + similar movies."""
import html

import pandas as pd
import streamlit as st

from src.api import run_analysis
from src.data import VALID_SENTIMENTS, effective_sentiment, get_movie_aggregates, save_review
from src.posters import (PLACEHOLDER, format_runtime, get_movie_details, get_movie_info,
                         get_poster_urls, get_trailer_keys, short_description)
from src.summary import summarize_reviews
from src.ui import render_backdrop_hero, render_stat_strip, section_title, render_empty_state
from src.pages.home import TRAILER_PREVIEWS, render_card

BADGE_COLORS = {
    "Positive": "#22c55e",
    "Negative": "#ef4444",
    "Neutral": "#94a3b8",
    "Error": "#6b7280",
    "Not analyzed": "#475569",
}

SIMILAR_COUNT = 5     # how many recommendations to show
REVIEWS_PER_PAGE = 10


def _esc(value) -> str:
    return html.escape(str(value), quote=True)


def _review_card(rev: pd.Series, label: str | None) -> str:
    """`label` is the effective sentiment (AI label, or derived from the star rating)."""
    raw = rev.get("sentiment")
    is_ai = isinstance(raw, str) and raw in VALID_SENTIMENTS
    if not (isinstance(label, str) and label):
        label = "Error" if raw == "Error" else "Not analyzed"
    color = BADGE_COLORS.get(label, BADGE_COLORS["Not analyzed"])

    meta = []
    rating = rev.get("rating")
    if pd.notna(rating):
        meta.append(f"Rating: {float(rating):g}/5")
    confidence = rev.get("confidence")
    if is_ai and pd.notna(confidence):
        meta.append(f"Confidence: {float(confidence):.0%}")
    if not is_ai and label in VALID_SENTIMENTS:
        meta.append("From star rating")
    meta_html = "".join(
        f'<span style="font-size:0.85rem;color:#94a3b8;">{_esc(m)}</span>' for m in meta
    )

    chips_html = ""
    keywords_raw = rev.get("keywords")
    if is_ai and pd.notna(keywords_raw):
        keywords = [k.strip() for k in str(keywords_raw).split(",") if k.strip()]
        chips = "".join(
            '<span style="background:rgba(168,85,247,0.15);color:#c4b5fd;padding:2px 8px;'
            f'border-radius:999px;font-size:0.75rem;">{_esc(k)}</span>'
            for k in keywords
        )
        if chips:
            chips_html = f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;">{chips}</div>'

    return (
        '<div style="background:rgba(30,30,45,0.6);border:1px solid rgba(168,85,247,0.2);'
        'border-radius:12px;padding:16px;margin-bottom:12px;">'
        '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:8px;">'
        f'<span style="background:{color};color:white;padding:4px 10px;border-radius:6px;'
        f'font-size:0.8rem;font-weight:600;">{_esc(label)}</span>{meta_html}</div>'
        '<p style="color:#e5e7eb;margin:8px 0;line-height:1.6;font-size:0.95rem;">'
        f'{_esc(rev.get("review", ""))}</p>{chips_html}</div>'
    )


def _average_rating(movie_df: pd.DataFrame, pos: int, neg: int, neu: int) -> float:
    if "rating" in movie_df.columns and movie_df["rating"].notna().any():
        return float(movie_df["rating"].mean())
    analyzed = pos + neg + neu
    if analyzed:
        return (4.5 * pos + 3.0 * neu + 1.5 * neg) / analyzed
    return 0.0


def _render_summary(movie_df: pd.DataFrame, eff: pd.Series, movie_title: str,
                    api_key: str, base_url: str, model: str):
    if not api_key:
        return

    reviews = movie_df[movie_df["review"].astype(str).str.strip() != ""]
    if reviews.empty:
        return

    def _tag(idx):
        s = eff.get(idx)
        return s if isinstance(s, str) and s in VALID_SENTIMENTS else "unrated"

    lines = tuple(
        f"[{_tag(idx)}] {str(r['review']).strip()[:300]}"
        for idx, r in reviews.tail(40).iterrows()
    )
    if not lines:
        return

    section_title("What reviewers say")
    try:
        with st.spinner("Summarizing reviews..."):
            summ = summarize_reviews(api_key, base_url, model, movie_title, lines)
    except Exception as e:
        st.info(f"Summary unavailable right now. ({e})")
        return

    if isinstance(summ, dict):
        verdict = summ.get("verdict", "")
        loved_list = summ.get("loved", []) or []
        complaints_list = summ.get("complaints", []) or []
    elif isinstance(summ, (tuple, list)):
        verdict = summ[0] if len(summ) > 0 else ""
        loved_list = summ[1] if len(summ) > 1 else []
        complaints_list = summ[2] if len(summ) > 2 else []
    else:
        st.info("Summary unavailable right now.")
        return

    loved = "".join(f"<li>{html.escape(str(p))}</li>" for p in loved_list) \
        or "<li style='color:#94a3b8;'>Nothing highlighted.</li>"
    if complaints_list:
        complaints = "".join(f"<li>{html.escape(str(p))}</li>" for p in complaints_list)
    else:
        complaints = "<li style='color:#94a3b8;'>None reported.</li>"

    st.markdown(
        "<div style='background:linear-gradient(135deg,rgba(30,30,45,0.85),"
        "rgba(20,20,32,0.85));border:1px solid rgba(168,85,247,0.25);"
        "border-left:4px solid #a855f7;border-radius:14px;padding:20px 22px;"
        "margin-bottom:20px;'>"
        f"<p style='color:#e5e7eb;margin:0 0 16px;line-height:1.6;font-size:0.95rem;'>"
        f"{html.escape(str(verdict))}</p>"
        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:20px;'>"
        "<div>"
        "<div style='color:#22c55e;font-weight:700;font-size:0.78rem;"
        "letter-spacing:1.5px;margin-bottom:8px;'>LOVED</div>"
        f"<ul style='color:#cbd5e1;margin:0;padding-left:18px;font-size:0.9rem;line-height:1.7;'>{loved}</ul>"
        "</div><div>"
        "<div style='color:#ef4444;font-weight:700;font-size:0.78rem;"
        "letter-spacing:1.5px;margin-bottom:8px;'>COMPLAINTS</div>"
        f"<ul style='color:#cbd5e1;margin:0;padding-left:18px;font-size:0.9rem;line-height:1.7;'>{complaints}</ul>"
        "</div></div></div>",
        unsafe_allow_html=True,
    )


def _pick_similar(agg: pd.DataFrame, movie_title: str, current_genre: str,
                  n: int = SIMILAR_COUNT) -> list:
    """Same-genre movies first, ranked by the smoothed scores (so a single 5-star review
    does not win); filled up with the best movies from other genres if needed."""
    pool = agg[agg["movie"] != movie_title].copy()
    if pool.empty:
        return []

    rank = ["pos_score", "rating_score", "review_count"]
    same = pool[pool["genre"] == current_genre].sort_values(rank, ascending=False)
    others = pool[pool["genre"] != current_genre].sort_values(rank, ascending=False)

    picked = list(same.head(n)["movie"])
    for m in others["movie"]:
        if len(picked) >= n:
            break
        if m not in picked:
            picked.append(m)
    return picked


def _render_similar(agg: pd.DataFrame, movie_title: str, current_genre: str):
    picks = _pick_similar(agg, movie_title, current_genre)
    if not picks:
        return

    section_title("You might also like")

    rows = agg[agg["movie"].isin(picks)].to_dict("records")
    order = {m: i for i, m in enumerate(picks)}
    rows.sort(key=lambda r: order.get(r["movie"], 999))

    # Only the recommended movies are sent to TMDB (not the whole catalogue).
    items = [(r["movie"], r["year"]) for r in rows]
    try:
        posters = get_poster_urls(items)
    except Exception:
        posters = {}
    trailers = {}
    if TRAILER_PREVIEWS:
        try:
            trailers = get_trailer_keys(items)
        except Exception:
            trailers = {}

    cols = st.columns(len(rows), gap="medium")
    for col, row in zip(cols, rows):
        with col:
            render_card(
                row,
                key=f"similar_{row['movie']}",
                poster_url=posters.get(row["movie"], PLACEHOLDER),
                trailer_key=trailers.get(row["movie"]),
            )


def _more_reviews(key: str):
    st.session_state[key] = st.session_state.get(key, REVIEWS_PER_PAGE) + REVIEWS_PER_PAGE


def render_page(df: pd.DataFrame, movie_title: str, api_key: str, base_url: str, model: str):
    if not movie_title:
        st.warning("No movie selected.")
        return

    movie_df = df[df["movie"] == movie_title].copy()
    if movie_df.empty:
        st.warning(f"No reviews found for '{movie_title}'.")
        return

    # --- Back button (top-left) ---
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Back", key="movie_back", width="stretch"):
            st.session_state["page"] = "Home"
            st.session_state["selected_movie"] = None
            st.rerun()
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    genre = movie_df["genre"].iloc[0]
    year = movie_df["year"].iloc[0] if "year" in movie_df.columns else pd.NA
    year_int = int(year) if pd.notna(year) else None
    year_txt = f" | {year_int}" if year_int else ""

    total = len(movie_df)
    eff = effective_sentiment(movie_df)
    pos = int((eff == "Positive").sum())
    neg = int((eff == "Negative").sum())
    neu = int((eff == "Neutral").sum())
    ai_count = (
        int(movie_df["sentiment"].isin(VALID_SENTIMENTS).sum())
        if "sentiment" in movie_df.columns else 0
    )

    avg_rating = _average_rating(movie_df, pos, neg, neu)

    info = get_movie_info(movie_title, year_int)
    details = get_movie_details(movie_title, year_int)
    runtime_txt = format_runtime(details["runtime"])
    meta_line = f"{genre}{year_txt}" + (f" | {runtime_txt}" if runtime_txt else "")

    render_backdrop_hero(
        title=movie_title,
        backdrop_url=info["backdrop"] or info["poster"],
        rating=avg_rating * 2,
        rating_count=total,
        meta_line=meta_line,
        synopsis=short_description(info["overview"]),
        director=details["director"],
        stars=", ".join(details["cast"]),
        trailer_url=details["trailer"] or "",
    )

    render_stat_strip([
        ("Positive", str(pos), "linear-gradient(135deg,#16a34a,#22c55e)"),
        ("Negative", str(neg), "linear-gradient(135deg,#b91c1c,#ef4444)"),
        ("Neutral", str(neu), "linear-gradient(135deg,#475569,#94a3b8)"),
    ])

    if ai_count < total:
        st.caption(
            f"{ai_count} of {total} reviews analyzed by AI. The rest are counted from their "
            "star ratings (4-5 Positive, 3 Neutral, 1-2 Negative)."
        )

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    if details["trailer"]:
        with st.expander("Watch the trailer here"):
            st.video(details["trailer"])

    _render_summary(movie_df, eff, movie_title, api_key, base_url, model)

    col_reviews, col_form = st.columns([1.4, 1], gap="large")

    with col_reviews:
        section_title("Reviews")
        if movie_df.empty:
            render_empty_state()
        else:
            shown_key = f"rev_shown_{movie_title}"
            shown = st.session_state.setdefault(shown_key, REVIEWS_PER_PAGE)
            newest_first = movie_df.iloc[::-1]
            for idx, rev in newest_first.head(shown).iterrows():
                st.markdown(_review_card(rev, eff.get(idx)), unsafe_allow_html=True)
            if total > shown:
                st.button(f"Show more reviews ({total - shown} left)",
                          key=f"rev_more_{movie_title}", width="stretch",
                          on_click=_more_reviews, args=(shown_key,))

    with col_form:
        section_title("Write a Review")

        ver = st.session_state.setdefault("review_form_version", 0)

        flash = st.session_state.pop("review_flash", None)
        if flash:
            st.success(flash)

        with st.form(f"write_review_form_{ver}"):
            user_rating = st.slider("Rate this movie", 1, 5, value=3, key=f"rating_{ver}")
            review_text = st.text_area(
                "Your thoughts...",
                placeholder="What did you think?",
                height=200,
                label_visibility="collapsed",
                key=f"text_{ver}",
            )
            submitted = st.form_submit_button("Post Review", width="stretch")

        if submitted:
            text = review_text.strip()
            existing = movie_df["review"].astype(str).str.strip().str.lower()
            if not text:
                st.warning("Write something first.")
            elif not api_key:
                st.error("No Groq API key found. Add GROQ_API_KEY to .streamlit/secrets.toml.")
            elif (existing == text.lower()).any():
                st.warning("That exact review already exists for this movie.")
            else:
                with st.spinner("Analyzing sentiment..."):
                    result = run_analysis(api_key, base_url, model, [text])[0]

                if result["sentiment"] == "Error":
                    detail = result["keywords"][0] if result["keywords"] else "unknown error"
                    st.error(f"Sentiment analysis failed, so the review was not saved. ({detail})")
                else:
                    saved = save_review({
                        "review": text,
                        "movie": movie_title,
                        "genre": genre,
                        "year": year_int if year_int else "",
                        "rating": user_rating,
                        "sentiment": result["sentiment"],
                        "confidence": result["confidence"],
                        "keywords": ", ".join(result["keywords"]),
                    })
                    if saved:
                        st.session_state["review_form_version"] = ver + 1
                        st.session_state["review_flash"] = (
                            f"Review posted: {result['sentiment']} "
                            f"({result['confidence']:.0%} confidence)"
                        )
                        st.rerun()

    # ---------------- Similar movies ----------------
    st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)

    agg = get_movie_aggregates(df)
    if not agg.empty:
        _render_similar(agg, movie_title, genre)

    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    if st.button("Back to Home", width="stretch", key="back_home"):
        st.session_state["page"] = "Home"
        st.session_state["selected_movie"] = None
        st.rerun()