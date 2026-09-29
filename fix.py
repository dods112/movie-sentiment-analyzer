import re

print("Fixing src/data.py...")
with open("src/data.py", "r") as f:
    content = f.read()

# Remove old functions
content = re.sub(r'\n\ndef save_review\(.*?\n.*?st\.error.*?\n', '', content, flags=re.DOTALL)

# Add corrected functions at end
new_funcs = '''

def save_review(row: dict, csv_path: str = "data/movie_reviews.csv"):
    import os
    try:
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        new_df = pd.DataFrame([row])
        if os.path.exists(csv_path):
            new_df.to_csv(csv_path, mode='a', header=False, index=False)
        else:
            new_df.to_csv(csv_path, index=False)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Failed to save review: {e}")


@st.cache_data(show_spinner=False)
def get_movie_aggregates(df):
    df = df.copy()
    if "rating" not in df.columns:
        sentiment_map = {"Positive": 4.5, "Neutral": 3.0, "Negative": 1.5, "Error": 0}
        if "sentiment" in df.columns:
            df["rating"] = df["sentiment"].fillna("Error").map(sentiment_map)
        else:
            df["rating"] = 0
    
    agg = (
        df.groupby("movie", as_index=False)
        .agg({"genre": "first", "year": "first", "review": "count", "rating": "mean"})
        .rename(columns={"review": "review_count", "rating": "avg_rating"})
    )
    
    if "sentiment" in df.columns:
        sentiment_counts = (
            df.groupby("movie")["sentiment"]
            .apply(lambda s: {
                "positive": int((s == "Positive").sum()),
                "negative": int((s == "Negative").sum()),
                "neutral": int((s == "Neutral").sum()),
            })
            .reset_index()
        )
        for sent_type in ["positive", "negative", "neutral"]:
            agg[sent_type] = agg["movie"].map(
                sentiment_counts.set_index("movie")["sentiment"].apply(lambda x: x[sent_type])
            )
        agg["pos_rate"] = agg.apply(
            lambda row: row.get("positive", 0) / row["review_count"] if row["review_count"] > 0 else 0,
            axis=1
        )
    else:
        agg["positive"] = agg["negative"] = agg["neutral"] = 0
        agg["pos_rate"] = 0.0
    
    return agg.sort_values("review_count", ascending=False).reset_index(drop=True)
'''

with open("src/data.py", "w") as f:
    f.write(content + new_funcs)
print("✓ src/data.py fixed")

# Fix dashboard.py
print("Fixing src/pages/dashboard.py...")
with open("src/pages/dashboard.py", "r") as f:
    content = f.read()

old = 'results_df = df.dropna(subset=["sentiment"]).copy()'
new = '''if "sentiment" not in df.columns:
        st.info("No sentiment column yet. Analyze some reviews first!")
        return
    
    results_df = df.dropna(subset=["sentiment"]).copy()'''

content = content.replace(old, new)
with open("src/pages/dashboard.py", "w") as f:
    f.write(content)
print("✓ src/pages/dashboard.py fixed")

# Fix ask_data.py
print("Fixing src/pages/ask_data.py...")
with open("src/pages/ask_data.py", "r") as f:
    content = f.read()

old = 'context_df = df.dropna(subset=["sentiment"]).copy()'
new = '''if "sentiment" not in df.columns:
        st.info("No sentiment column yet. Analyze some reviews first!")
        return
    
    context_df = df.dropna(subset=["sentiment"]).copy()'''

content = content.replace(old, new)
with open("src/pages/ask_data.py", "w") as f:
    f.write(content)
print("✓ src/pages/ask_data.py fixed")

# Fix movie_detail.py
print("Fixing src/pages/movie_detail.py...")
with open("src/pages/movie_detail.py", "r") as f:
    content = f.read()

old = 'pos = int((movie_df.get("sentiment", "") == "Positive").sum())'
new = 'pos = int((movie_df["sentiment"] == "Positive").sum()) if "sentiment" in movie_df.columns else 0'
content = content.replace(old, new)

old = 'neg = int((movie_df.get("sentiment", "") == "Negative").sum())'
new = 'neg = int((movie_df["sentiment"] == "Negative").sum()) if "sentiment" in movie_df.columns else 0'
content = content.replace(old, new)

old = 'neu = int((movie_df.get("sentiment", "") == "Neutral").sum())'
new = 'neu = int((movie_df["sentiment"] == "Neutral").sum()) if "sentiment" in movie_df.columns else 0'
content = content.replace(old, new)

with open("src/pages/movie_detail.py", "w") as f:
    f.write(content)
print("✓ src/pages/movie_detail.py fixed")

print("\n✅ All files fixed!")
print("Run: streamlit run app.py")