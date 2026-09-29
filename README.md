# 🎬 Movie Review Sentiment Analyzer

A Generative AI-powered web application that performs sentiment analysis on movie reviews, visualizes insights through interactive dashboards, and lets you chat with your data in natural language.

**Live App:** https://movie-sentiment-dolohan.streamlit.app/
**Repository:** https://github.com/dods112/movie-sentiment-analyzer

---

## 📖 Overview

The **Movie Review Sentiment Analyzer** is built with **Streamlit** and powered by **Groq's high-speed inference API** (running OpenAI's GPT-OSS-120B model through an OpenAI-compatible endpoint). It classifies each review as **Positive**, **Negative**, or **Neutral**, extracts keywords, and visualizes results with interactive Plotly and Altair charts.

It also includes an **"Ask the Data" chatbot** that answers natural-language questions about the dataset, and a **floating AI assistant** available on every page.

---

## ✨ Features

### Core Analysis

* **Data loading & cleaning** with Pandas (null removal, deduplication, text normalization)
* **GenAI sentiment classification** using Groq API (concurrent requests via `asyncio`)
* **Keyword extraction** per review
* **Confidence scoring** for every AI prediction
* **CSV export** of analysis results

### Interactive Dashboard

* Sentiment distribution pie chart
* Confidence score histogram
* Sentiment breakdown by movie
* Sentiment and positive rate by genre
* Reviews over time (release year trend)
* Average rating by movie
* Rating distribution by sentiment
* Top keywords frequency chart

### Movie Discovery

* **Movie poster wall** — real posters fetched dynamically from the TMDB API
* **Featured banner carousel** with auto-playing trailer previews
* **Movie detail pages** with backdrop hero, cast, director, runtime, and trailer
* **Similar movie recommendations** (same-genre first, ranked by smoothed scores)
* **AI-generated review summaries** ("What reviewers say")
* **Filters** for genre, movie, sentiment, plus search and sort
* **"My List" watchlist** persisted to `data/watchlist.json`

### Chatbots

* **Full-page "Ask the Data" chatbot** for natural-language dataset queries
* **Floating chat panel** accessible from any page

---

## 📁 Project Structure

```text
movie-sentiment-analyzer/
├── app.py                     # Entry point + page router
├── requirements.txt
├── README.md
├── data/
│   ├── movie_reviews.csv
│   ├── movie_reviews_analyzed.csv
│   └── watchlist.json
└── src/
    ├── __init__.py
    ├── api.py                 # Groq sentiment analysis (async + concurrent)
    ├── charts.py              # All chart builders
    ├── chatbot.py             # Chat logic + message bubbles
    ├── data.py                # Data loading, cleaning, aggregates
    ├── db.py                  # Optional SQLAlchemy layer
    ├── floating_chat.py       # Floating chat panel
    ├── posters.py             # TMDB poster/backdrop/trailer fetcher
    ├── summary.py             # AI review summarization
    ├── ui.py                  # Theme, CSS, reusable UI components
    └── pages/
        ├── __init__.py
        ├── home.py            # Featured banner + poster grid
        ├── dashboard.py       # Analytics dashboard
        ├── movie_detail.py    # Individual movie page
        ├── ask_data.py        # Full-page chatbot
        └── watchlist.py       # "My List" page
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/dods112/movie-sentiment-analyzer.git
cd movie-sentiment-analyzer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API keys

Create a `.streamlit/secrets.toml` file in the project root:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
TMDB_API_KEY = "your_tmdb_api_key_here"
```

* Get a **Groq API key:** https://console.groq.com/keys
* Get a **TMDB API key:** https://www.themoviedb.org/settings/api

### 4. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 🤖 How the GenAI Integration Works

### Sentiment Analysis

Each review is sent to the Groq API with a system prompt instructing the model to return a **strict JSON object** with three fields: `sentiment`, `confidence`, and `keywords`.

* Requests are processed **concurrently** using Python's `asyncio` and a semaphore (default: 3 parallel requests).
* **Rate limits** are handled gracefully using Groq's `try again in ...` hint with exponential backoff.
* **Failures are isolated** per-review — a single error never crashes the batch.
* Results are **persisted** to the CSV/database so subsequent runs are instant.

### Chatbot

The dataset is summarized into a compact CSV context (per-movie aggregates, per-genre stats, recent reviews) and injected into the system prompt on **every turn**, so the model never loses context. Conversation history is trimmed to the last 6 turns.

### Review Summarization

A single cached Groq call returns a JSON with `verdict`, `loved`, and `complaints` for each movie, shown as the "What reviewers say" panel.

---

## 📊 Dataset

The sample dataset contains **30 movie reviews across 15 popular films** including *Inception*, *The Dark Knight*, *Parasite*, *Oppenheimer*, *Interstellar*, and *Spider-Man: Into the Spider-Verse*.

**Columns:** `review`, `movie`, `genre`, `year`, `rating`, `sentiment`, `confidence`, `keywords`

> **Citation:** Movie Review Sentiment Dataset. (2026). Synthetic dataset created by the author for CS 315 Activity 3, September 2026. 30 movie reviews across 15 films with columns: movie, review, genre, year.

You can swap in your own CSV — just keep the same column names and place it at `data/movie_reviews.csv`.

---

## 📚 References

* **Groq.** (2026). *Groq API Documentation.* https://console.groq.com/docs
* **The Movie Database (TMDB).** (2026). *TMDB API Documentation.* https://developers.themoviedb.org/3
* **Streamlit.** (2026). *Streamlit Documentation.* https://docs.streamlit.io
* **OpenAI.** (2026). *OpenAI Python SDK Documentation.* https://platform.openai.com/docs

---

## 👤 Author

**Merl Rex N. Dolohan**
Section: 3CSA
Course: CS 315 – Application Development and Emerging Technologies
Hands-on Activity 3: GenAI Application

---

## 📄 License

This project is created for academic purposes as part of CS 315 coursework.
