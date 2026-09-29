🎬 Movie Review Sentiment Analyzer

CS 315 – Application Development and Emerging Technologies
Hands-on Activity 3: GenAI Application

Name: Merl Rex N. Dolohan
Section: 3CSA
Date: September 25, 2026



Live App Link

Streamlit App: https://movie-sentiment-dolohan.streamlit.app/
GitHub Repository: https://github.com/dods112/movie-sentiment-analyzer



1. App Description

The Movie Review Sentiment Analyzer is a Generative AI–powered web application built with Streamlit. It performs sentiment analysis on a dataset of movie reviews, classifying each review as Positive, Negative, or Neutral using Groq's high-speed inference API (running OpenAI's GPT-OSS-120B model through an OpenAI-compatible endpoint). The app extracts keywords from each review and visualizes the aggregated results through interactive Plotly and Altair charts. It also includes an "Ask the Data" chatbot that answers natural-language questions about the dataset.

2. Features Implemented

- Data loading and cleaning using Pandas (null removal, deduplication, text normalization)
- GenAI sentiment classification using the Groq API
- Keyword extraction per review
- Interactive dashboard with:
  - Sentiment distribution pie chart
  - Confidence score histogram
  - Sentiment breakdown by movie
  - Sentiment and positive rate by genre
  - Reviews over time
  - Top keywords frequency chart
- Movie poster wall — real posters fetched dynamically from the TMDB API
- Filters for genre and movie
- Ask-the-Data chatbot for natural-language queries
- CSV export of analysis results

3. Dataset Source

The dataset used in this application is a sample movie review dataset containing 30 reviews across 15 popular films (Inception, The Dark Knight, Parasite, Oppenheimer, Interstellar, Spider-Man: Into the Spider-Verse, and others). It contains four columns: movie, review, genre, and year.

Citation:
Movie Review Sentiment Dataset. (2026). Synthetic dataset created by the author for CS 315 Activity 3, September 2026. 30 movie reviews across 15 films with columns: movie, review, genre, year.

4. Technologies and APIs Used

Technology              Purpose
Python 3.13              Core language
Streamlit 1.40+          Web UI framework
Pandas 2.2.3              Data loading and cleaning
Plotly 5.24              Interactive charts (pie, bar)
Altair 5.5              Interactive charts (histogram, line, stacked bar)
OpenAI Python SDK 1.55      Client for the Groq API
Groq API              LLM inference for sentiment + chatbot
TMDB API              Movie poster images

GenAI API: Groq — https://api.groq.com/openai/v1
Models used: openai/gpt-oss-120b, openai/gpt-oss-20b, qwen/qwen3.6-27b

5. How the GenAI Integration Works

Each review is sent to the Groq API with a system prompt instructing the model to return a strict JSON object with three fields: sentiment, confidence, and keywords. Requests are processed concurrently using Python's asyncio and a semaphore to limit concurrency (8 parallel requests), dramatically reducing total analysis time. Failed responses are caught per-review so a single error never crashes the batch.

6. References

Groq. (2026). Groq API Documentation. https://console.groq.com/docs
The Movie Database (TMDB). (2026). TMDB API Documentation. https://developers.themoviedb.org/3
Streamlit. (2026). Streamlit Documentation. https://docs.streamlit.io
OpenAI. (2026). OpenAI Python SDK Documentation. https://platform.openai.com/docs
