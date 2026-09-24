"""All chart builders. Emoji-free legends and labels."""
import altair as alt
import pandas as pd
import plotly.express as px

from .ui import SENTIMENT_COLORS

_SENT_DOMAIN = list(SENTIMENT_COLORS.keys())
_SENT_RANGE = list(SENTIMENT_COLORS.values())


def sentiment_pie(results_df: pd.DataFrame):
    counts = results_df["sentiment"].value_counts().reset_index()
    counts.columns = ["Sentiment", "Count"]
    fig = px.pie(
        counts, names="Sentiment", values="Count", hole=0.62,
        color="Sentiment", color_discrete_map=SENTIMENT_COLORS,
    )
    fig.update_traces(
        textinfo="percent+label",
        textfont_size=13,
        marker=dict(line=dict(color="#0a0a0f", width=3)),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        annotations=[dict(
            text=f"<b>{len(results_df)}</b><br>reviews",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=15, color="#e5e7eb"),
        )],
    )
    return fig


def confidence_histogram(results_df: pd.DataFrame):
    conf_df = results_df.dropna(subset=["confidence"])
    if conf_df.empty:
        return None
    base = alt.Chart(conf_df).mark_bar(cornerRadius=3).encode(
        x=alt.X("confidence:Q", bin=alt.Bin(maxbins=15), title="Confidence"),
        y=alt.Y("count()", title="Reviews"),
        color=alt.Color(
            "sentiment:N",
            scale=alt.Scale(domain=_SENT_DOMAIN, range=_SENT_RANGE),
            legend=alt.Legend(title=None, orient="top"),
        ),
        tooltip=["sentiment", "count()"],
    )
    return base.properties(height=320, background="transparent").configure_view(strokeWidth=0)


def sentiment_by_movie(results_df: pd.DataFrame):
    data = results_df.groupby(["movie", "sentiment"]).size().reset_index(name="count")
    height = 28 * results_df["movie"].nunique() + 60
    chart = alt.Chart(data).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X("count:Q", title="Reviews"),
        y=alt.Y("movie:N", sort="-x", title=None),
        color=alt.Color(
            "sentiment:N",
            scale=alt.Scale(domain=_SENT_DOMAIN, range=_SENT_RANGE),
            legend=alt.Legend(title=None, orient="top"),
        ),
        tooltip=["movie", "sentiment", "count"],
    )
    return chart.properties(height=height, background="transparent").configure_view(strokeWidth=0)


def sentiment_by_genre(results_df: pd.DataFrame):
    data = results_df.groupby(["genre", "sentiment"]).size().reset_index(name="count")
    fig = px.bar(
        data, x="genre", y="count", color="sentiment",
        barmode="group", color_discrete_map=SENTIMENT_COLORS,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
        margin=dict(t=10, b=10, l=10, r=10),
        legend_title=None,
        xaxis_title=None,
    )
    return fig


def positive_rate_by_genre(results_df: pd.DataFrame):
    data = (
        results_df.groupby("genre")["sentiment"]
        .apply(lambda s: (s == "Positive").mean())
        .reset_index(name="positive_rate")
    )
    chart = alt.Chart(data).mark_bar(color="#22c55e", cornerRadiusEnd=4).encode(
        x=alt.X("positive_rate:Q", title="Positive rate",
                axis=alt.Axis(format="%")),
        y=alt.Y("genre:N", sort="-x", title=None),
        tooltip=[alt.Tooltip("positive_rate:Q", format=".0%")],
    )
    return chart.properties(height=320, background="transparent").configure_view(strokeWidth=0)


def reviews_over_time(results_df: pd.DataFrame):
    if "year" not in results_df.columns:
        return None
    data = (
        results_df.dropna(subset=["year"])
        .groupby(["year", "sentiment"]).size().reset_index(name="count")
    )
    if data.empty:
        return None
    chart = alt.Chart(data).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("count:Q", title="Reviews"),
        color=alt.Color(
            "sentiment:N",
            scale=alt.Scale(domain=_SENT_DOMAIN, range=_SENT_RANGE),
            legend=alt.Legend(orient="top", title=None),
        ),
        tooltip=["year", "sentiment", "count"],
    )
    return chart.properties(height=330, background="transparent").configure_view(strokeWidth=0)


def top_keywords(results_df: pd.DataFrame, top_n: int = 15):
    kws = ", ".join(results_df["keywords"].dropna()).split(", ")
    kws = [k.strip().lower() for k in kws if k.strip()]
    if not kws:
        return None, None
    counts = pd.Series(kws).value_counts().head(top_n).reset_index()
    counts.columns = ["Keyword", "Frequency"]
    fig = px.bar(
        counts, x="Frequency", y="Keyword", orientation="h",
        color="Frequency", color_continuous_scale=["#a855f7", "#db2777"],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
        yaxis={"categoryorder": "total ascending"},
        margin=dict(t=10, b=10, l=10, r=10),
        coloraxis_showscale=False,
    )
    return fig, counts