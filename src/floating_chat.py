"""Floating chat: a button pinned to the bottom-right that opens a chat panel on any page.

Open/closed state lives in st.session_state["chat_open"]; the history is shared with the
full-page "Ask the Data" chat (st.session_state["chat_history"]).
Needs Streamlit >= 1.39 (st.container(key=...) gives the CSS hooks used below).
"""
import pandas as pd
import streamlit as st

from src.chatbot import (WELCOME_MSG, _now, _render_ai_bubble, _render_user_bubble,
                         ask_dataset, find_movies)
from src.data import effective_sentiment

MAX_SHOWN = 8       # latest messages shown in the panel, so it never grows past the screen
PANEL_POSTERS = 2   # poster columns inside the narrow panel

FLOAT_CSS = """
<style>
.st-key-chat_fab {
    position: fixed; bottom: 24px; right: 24px; z-index: 1001;
    width: auto !important;
}
.st-key-chat_fab button {
    background: linear-gradient(135deg, #7c3aed, #db2777) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 12px 24px !important;
    font-weight: 700 !important;
    box-shadow: 0 10px 28px rgba(124,58,237,0.45) !important;
}
.st-key-chat_fab button:hover { transform: translateY(-2px); }

.st-key-chat_panel {
    position: fixed; bottom: 84px; right: 24px; z-index: 1000;
    width: min(400px, calc(100vw - 32px)) !important;
    max-height: calc(100vh - 120px);
    overflow-y: auto;
    background: #12121c;
    border: 1px solid rgba(168,85,247,0.35);
    border-radius: 18px;
    padding: 16px;
    box-shadow: 0 24px 60px rgba(0,0,0,0.55);
}
.st-key-chat_panel [data-testid="stForm"] { border: none; padding: 0; }

@media (max-width: 768px) {
    .st-key-chat_fab { bottom: 16px; right: 16px; }
    .st-key-chat_panel {
        bottom: 76px; right: 16px; left: 16px;
        width: auto !important;
        max-height: calc(100vh - 100px);
    }
}
</style>
"""


def _suggestions(focus_movie: str | None) -> list:
    if focus_movie:
        return [
            f"Summarize the reviews of {focus_movie}",
            "What do reviewers like most?",
            "What are the main complaints?",
        ]
    return [
        "Which movie is rated highest?",
        "Which genre is the most positive?",
        "What do people complain about most?",
    ]


def _toggle():
    st.session_state["chat_open"] = not st.session_state.get("chat_open", False)


def _clear():
    st.session_state["chat_history"] = [{"role": "assistant", "content": WELCOME_MSG,
                                         "ts": _now()}]


def render_floating_chat(df: pd.DataFrame, api_key: str, base_url: str, model: str,
                         focus_movie: str | None = None):
    st.markdown(FLOAT_CSS, unsafe_allow_html=True)

    is_open = st.session_state.setdefault("chat_open", False)
    with st.container(key="chat_fab"):
        st.button("Close chat" if is_open else "Ask AI", key="chat_fab_btn", on_click=_toggle)

    if not is_open:
        return

    history = st.session_state.setdefault(
        "chat_history", [{"role": "assistant", "content": WELCOME_MSG, "ts": _now()}]
    )

    # Every review is available to the bot; sentiment is the AI label, or the star-rating
    # label when a review has not been analyzed yet.
    context_df = df.copy()
    context_df["sentiment"] = effective_sentiment(df)

    with st.container(key="chat_panel"):
        col_title, col_clear = st.columns([3, 1])
        with col_title:
            st.markdown('<div class="section-title">Ask about the reviews</div>',
                        unsafe_allow_html=True)
        with col_clear:
            st.button("Clear", key="fchat_clear", on_click=_clear, width="stretch")

        msg_area = st.container()
        with msg_area:
            visible = [(i, m) for i, m in enumerate(history) if not m.get("thinking")][-MAX_SHOWN:]
            for i, msg in visible:
                if msg["role"] == "user":
                    _render_user_bubble(msg["content"], msg.get("ts"))
                else:
                    _render_ai_bubble(msg["content"], movies=msg.get("movies"),
                                      key=f"fchat{i}", ts=msg.get("ts"),
                                      poster_cols=PANEL_POSTERS)

        question = None

        if not any(m["role"] == "user" for m in history):
            for i, text in enumerate(_suggestions(focus_movie)):
                if st.button(text, key=f"fchat_sugg_{i}", width="stretch"):
                    question = text

        with st.form("fchat_form", clear_on_submit=True):
            typed = st.text_input(
                "Message", placeholder="Ask about a movie...",
                label_visibility="collapsed", key="fchat_text",
            )
            sent = st.form_submit_button("Send", width="stretch")
        if sent and typed.strip():
            question = typed.strip()

        if question:
            history.append({"role": "user", "content": question, "ts": _now()})
            with msg_area:
                _render_user_bubble(question, history[-1]["ts"])
                slot = st.empty()
                with slot.container():
                    _render_ai_bubble("", thinking=True)

            if not api_key:
                answer = "No Groq API key found. Add GROQ_API_KEY to .streamlit/secrets.toml."
            else:
                try:
                    answer = ask_dataset(api_key, base_url, model, context_df, question,
                                         focus_movie=focus_movie, history=history)
                except Exception as e:
                    answer = f"Something went wrong asking Groq: {e}"

            history.append({"role": "assistant", "content": answer,
                            "movies": find_movies(context_df, question, answer),
                            "ts": _now()})
            st.session_state["chat_history"] = history
            st.rerun()