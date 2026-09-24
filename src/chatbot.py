"""Messenger-style chat with persistent history."""

import streamlit as st
from openai import OpenAI


WELCOME_MSG = (
    "Hi! Ask me anything about your movie review dataset — sentiment, "
    "specific movies, genres, keywords, whatever you like."
)


def ask_dataset(api_key: str, base_url: str, model: str, context_df, question: str) -> str:
    client = OpenAI(api_key=api_key, base_url=base_url)
    context_csv = context_df.to_csv(index=False)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You answer questions about a movie review dataset using only "
                    "the data provided. Be concise and specific — cite movie names, "
                    "counts, or percentages where relevant."
                ),
            },
            {"role": "user", "content": f"Dataset:\n{context_csv}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


def _render_user_bubble(content: str):
    st.markdown(
        f"""
        <div style="display:flex;justify-content:flex-end;margin:10px 0;">
            <div style="
                background: linear-gradient(135deg, #7c3aed, #db2777);
                color: #ffffff;
                padding: 12px 16px;
                border-radius: 18px 18px 4px 18px;
                max-width: 75%;
                font-size: 0.92rem;
                line-height: 1.5;
                box-shadow: 0 4px 14px rgba(124,58,237,0.28);
                word-wrap: break-word;
            ">{content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_ai_bubble(content: str, thinking: bool = False):
    if thinking:
        body = "<span style='opacity:0.7;font-style:italic;'>thinking...</span>"
    else:
        body = content.replace("\n", "<br>") if content else ""

    st.markdown(
        f"""
        <div style="display:flex;justify-content:flex-start;margin:10px 0;">
            <div style="
                background: rgba(30,30,45,0.9);
                border: 1px solid rgba(168,85,247,0.25);
                color: #e5e7eb;
                padding: 12px 16px;
                border-radius: 18px 18px 18px 4px;
                max-width: 75%;
                font-size: 0.92rem;
                line-height: 1.55;
                word-wrap: break-word;
            ">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chatbot(api_key: str, base_url: str, model: str, context_df):
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": WELCOME_MSG}
        ]
    if "chat_input_version" not in st.session_state:
        st.session_state["chat_input_version"] = 0

    # Header + Clear
    col_title, col_clear = st.columns([5, 1])
    with col_title:
        st.markdown(
            '<div class="section-title">Ask the dataset a question</div>',
            unsafe_allow_html=True,
        )
    with col_clear:
        if st.button("Clear", use_container_width=True, key="chat_clear_btn"):
            st.session_state["chat_history"] = [
                {"role": "assistant", "content": WELCOME_MSG}
            ]
            st.session_state["chat_input_version"] += 1
            st.rerun()

    # Render messages
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            _render_user_bubble(msg["content"])
        else:
            _render_ai_bubble(msg["content"], thinking=msg.get("thinking", False))

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Input row
    input_key = f"chat_input_box_{st.session_state['chat_input_version']}"

    col_input, col_send = st.columns([6, 1])
    with col_input:
        user_question = st.text_input(
            "message",
            placeholder="Type a message...",
            label_visibility="collapsed",
            key=input_key,
        )
    with col_send:
        send_clicked = st.button("Send", use_container_width=True, key="chat_send_btn")

    # Handle send
    if send_clicked and user_question.strip():
        st.session_state["chat_history"].append(
            {"role": "user", "content": user_question.strip()}
        )
        st.session_state["chat_input_version"] += 1
        st.rerun()

    # Append thinking placeholder if last message is user
    history = st.session_state["chat_history"]
    if history and history[-1]["role"] == "user":
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": "", "thinking": True}
        )
        st.rerun()

    # Resolve thinking placeholder
    history = st.session_state["chat_history"]
    if (
        len(history) >= 2
        and history[-1]["role"] == "assistant"
        and history[-1].get("thinking", False)
        and history[-2]["role"] == "user"
    ):
        question = history[-2]["content"]

        if not api_key:
            answer = "No Groq API key found. Add GROQ_API_KEY to .streamlit/secrets.toml."
        else:
            try:
                answer = ask_dataset(api_key, base_url, model, context_df, question)
            except Exception as e:
                answer = f"Something went wrong asking Groq: {e}"

        history[-1] = {"role": "assistant", "content": answer}
        st.session_state["chat_history"] = history
        st.rerun()