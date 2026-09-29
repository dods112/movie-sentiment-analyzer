"""Data loading, cleaning, persistence, and per-movie aggregates."""
import os

import numpy as np
import pandas as pd
import streamlit as st

CSV_PATH = "data/movie_reviews.csv"
VALID_SENTIMENTS = ["Positive", "Negative", "Neutral"]
KNOWN_SENTIMENTS = VALID_SENTIMENTS + ["Error"]
SENTIMENT_TO_RATING = {"Positive": 4.5, "Neutral": 3.0, "Negative": 1.5}
BASE_COLUMNS = ["review", "movie", "genre", "year"]
AGG_COLUMNS = [
    "movie", "genre", "year", "review_count", "avg_rating",
    "positive", "negative", "neutral", "pos_rate", "pos_score", "rating_score",
]


def _db():
    """Import the SQLAlchemy layer lazily so CSV-only setups don't need sqlalchemy installed."""
    from src import db
    return db


def _database_url() -> str:
    """DATABASE_URL from Streamlit secrets or the environment; empty means 'use the CSV'."""
    try:
        url = st.secrets.get("DATABASE_URL", "")
    except Exception:  # no secrets.toml
        url = ""
    return url or os.environ.get("DATABASE_URL", "")


def _engine():
    url = _database_url()
    return _db().get_engine(url) if url else None


def using_database() -> bool:
    return bool(_database_url())


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    for col in BASE_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    # Drop NaNs BEFORE converting to str, otherwise NaN becomes the string "nan".
    df = df.dropna(subset=["review", "movie"]).copy()
    df["genre"] = df["genre"].fillna("Unknown")
    for col in ("review", "movie", "genre"):
        df[col] = df[col].astype(str).str.strip()

    df = df[(df["review"] != "") & (df["movie"] != "")]
    df = df.drop_duplicates(subset=["review", "movie"]).reset_index(drop=True)

    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    if "confidence" in df.columns:
        df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    if "sentiment" in df.columns:
        s = df["sentiment"].astype(str).str.strip().str.title()
        df["sentiment"] = s.where(s.isin(KNOWN_SENTIMENTS), np.nan)
    return df


def _read_csv(path: str, quiet: bool = False) -> pd.DataFrame:
    """Read the CSV tolerantly (BOM, header case/spaces) and explain problems on screen."""
    empty = pd.DataFrame(columns=BASE_COLUMNS)
    abs_path = os.path.abspath(path)

    if not os.path.exists(path):
        if not quiet:
            st.error(f"CSV not found at: {abs_path}\n\nRun `streamlit run app.py` from the "
                     "project root, or put the file at data/movie_reviews.csv.")
        return empty
    try:
        raw = pd.read_csv(path, encoding="utf-8-sig")
    except pd.errors.EmptyDataError:
        if not quiet:
            st.error(f"The CSV is empty: {abs_path}")
        return empty

    raw.columns = [str(c).strip().lower() for c in raw.columns]
    missing = [c for c in ("review", "movie") if c not in raw.columns]
    if missing:
        if not quiet:
            st.error(f"{abs_path} is missing column(s): {missing}. "
                     f"Columns found: {list(raw.columns)}. "
                     "Expected header: review,movie,genre,year,rating")
        return empty
    return raw


@st.cache_data(show_spinner=False, ttl=120)
def load_data(path: str = CSV_PATH) -> pd.DataFrame:
    """Load reviews from the database if DATABASE_URL is set, otherwise from the CSV."""
    engine = _engine()
    if engine is not None:
        try:
            # First deploy: an empty table gets seeded from the CSV committed with the repo.
            if _db().count_rows(engine) == 0 and os.path.exists(path):
                _db().seed_from_csv(engine, path)
            raw = _db().fetch_all(engine)
        except Exception as e:
            st.error(f"Could not read from the database: {e}")
            raw = pd.DataFrame(columns=_db().COLUMNS)
        return _clean(raw)

    return _clean(_read_csv(path))


def clear_data_cache():
    """Invalidate only the data caches (leaves the TMDB poster cache alone)."""
    load_data.clear()
    get_movie_aggregates.clear()


def _write_csv(df: pd.DataFrame, csv_path: str):
    """Write atomically so a crash mid-write can't corrupt the CSV."""
    folder = os.path.dirname(csv_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = csv_path + ".tmp"
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, csv_path)


def save_review(row: dict, csv_path: str = CSV_PATH) -> bool:
    """Append one review (database if configured, otherwise the CSV)."""
    engine = _engine()
    if engine is not None:
        try:
            _db().insert_rows(engine, [row])
        except Exception as e:
            st.error(f"Failed to save review: {e}")
            return False
        clear_data_cache()
        return True

    try:
        new_df = pd.DataFrame([row])
        if os.path.exists(csv_path):
            old = _read_csv(csv_path, quiet=True)
            new_df = pd.concat([old, new_df], ignore_index=True)
        _write_csv(new_df, csv_path)
    except Exception as e:
        st.error(f"Failed to save review: {e}")
        return False
    clear_data_cache()
    return True


def write_analysis(results: dict, csv_path: str = CSV_PATH) -> bool:
    """
    Store sentiment results for existing reviews.
    `results` maps (review_text, movie) -> {"sentiment", "confidence", "keywords"}.
    """
    engine = _engine()
    if engine is not None:
        try:
            _db().update_analysis(engine, results)
        except Exception as e:
            st.error(f"Failed to save analysis: {e}")
            return False
        clear_data_cache()
        return True

    try:
        raw = _read_csv(csv_path, quiet=True)
        for col in ("sentiment", "confidence", "keywords"):
            if col not in raw.columns:
                raw[col] = None
            raw[col] = raw[col].astype("object")

        for i, r in raw.iterrows():
            key = (str(r["review"]).strip(), str(r["movie"]).strip())
            res = results.get(key)
            if res:
                raw.at[i, "sentiment"] = res["sentiment"]
                raw.at[i, "confidence"] = res["confidence"]
                raw.at[i, "keywords"] = ", ".join(res.get("keywords", []))

        _write_csv(raw, csv_path)
    except Exception as e:
        st.error(f"Failed to save analysis: {e}")
        return False
    clear_data_cache()
    return True


def effective_sentiment(df: pd.DataFrame) -> pd.Series:
    """
    Sentiment to display for each review: the AI's label when there is one, otherwise a
    label derived from the star rating (4-5 Positive, 3 Neutral, 1-2 Negative).
    Reviews with neither stay NaN.
    """
    if "sentiment" in df.columns:
        sent = df["sentiment"].where(df["sentiment"].isin(VALID_SENTIMENTS), np.nan)
    else:
        sent = pd.Series(np.nan, index=df.index, dtype="object")
    if "rating" in df.columns:
        derived = df["rating"].map(
            lambda r: np.nan if pd.isna(r) else "Positive" if r >= 4 else "Neutral" if r >= 3 else "Negative"
        )
        sent = sent.fillna(derived)
    return sent


def wilson_lower(pos: int, n: int, z: float = 1.96) -> float:
    """Lower bound of the positive rate's 95% interval, so 1/1 positive scores far
    lower than 40/40 positive."""
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float((centre - margin) / denom)


@st.cache_data(show_spinner=False)
def get_movie_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per movie: review_count, avg_rating, sentiment counts, pos_rate,
    plus two smoothed ranking scores:
      pos_score    - Wilson lower bound of the positive rate
      rating_score - Bayesian average of the star rating

    avg_rating uses the real `rating` column when present; rows without a rating
    fall back to a sentiment-derived value (Positive 4.5, Neutral 3.0, Negative 1.5).
    """
    if df.empty:
        return pd.DataFrame(columns=AGG_COLUMNS)

    d = df.copy()
    has_sent = "sentiment" in d.columns

    derived = d["sentiment"].map(SENTIMENT_TO_RATING) if has_sent else pd.Series(np.nan, index=d.index)
    if "rating" in d.columns:
        d["rating"] = d["rating"].fillna(derived)
    else:
        d["rating"] = derived

    agg = (
        d.groupby("movie", as_index=False)
        .agg(
            genre=("genre", "first"),
            year=("year", "first"),
            review_count=("review", "count"),
            avg_rating=("rating", "mean"),
        )
    )
    agg["avg_rating"] = agg["avg_rating"].fillna(0.0)

    for col in ("positive", "negative", "neutral"):
        agg[col] = 0

    d["_eff"] = effective_sentiment(df)
    valid = d[d["_eff"].notna()]
    if not valid.empty:
        counts = (
            valid.groupby(["movie", "_eff"]).size()
            .unstack(fill_value=0)
            .reindex(columns=VALID_SENTIMENTS, fill_value=0)
        )
        for sent in VALID_SENTIMENTS:
            agg[sent.lower()] = agg["movie"].map(counts[sent]).fillna(0).astype(int)

    analyzed = agg["positive"] + agg["negative"] + agg["neutral"]
    agg["pos_rate"] = (agg["positive"] / analyzed.where(analyzed > 0)).fillna(0.0)

    # Smoothed ranking scores: a movie with one glowing review no longer tops the lists.
    agg["pos_score"] = [wilson_lower(int(p), int(a)) for p, a in zip(agg["positive"], analyzed)]

    M = 3  # every movie starts with this many "average" reviews
    C = agg.loc[agg["avg_rating"] > 0, "avg_rating"].mean()
    C = 0.0 if pd.isna(C) else float(C)
    agg["rating_score"] = (agg["review_count"] * agg["avg_rating"] + M * C) / (agg["review_count"] + M)

    return agg.sort_values(["review_count", "movie"], ascending=[False, True]).reset_index(drop=True)