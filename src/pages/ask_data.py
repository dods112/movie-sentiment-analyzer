"""Ask the Data page - messenger-style chatbot."""
import pandas as pd
import streamlit as st

from src.chatbot import render_chatbot
from src.data import effective_sentiment


def render_page(df: pd.DataFrame, api_key: str, base_url: str, model: str):
    """Chatbot page. Uses every review; sentiment is the AI label, or the label derived
    from the star rating when a review has not been analyzed (same as the floating chat)."""
    if df.empty:
        st.info("No reviews yet. Add data/movie_reviews.csv first.")
        return

    context_df = df.copy()
    context_df["sentiment"] = effective_sentiment(df)

    render_chatbot(api_key=api_key, base_url=base_url, model=model, context_df=context_df)