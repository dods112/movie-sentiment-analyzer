"""Data loading and cleaning."""
import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def load_data(path: str = "data/movie_reviews.csv") -> pd.DataFrame:
    df = pd.read_csv(path)

    for col in ("review", "movie", "genre"):
        df[col] = df[col].astype(str).str.strip()

    df = df.dropna(subset=["review"])
    df = df[df["review"] != ""]
    df = df.drop_duplicates(subset=["review"]).reset_index(drop=True)

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    return df