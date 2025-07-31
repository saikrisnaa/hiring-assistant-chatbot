# helpers.py

import streamlit as st
import openai
import re
from sentiment import get_user_mood
from llm import LLM_MODEL

def call_llm(messages):
    try:
        response = openai.ChatCompletion.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ API Error: {e}")
        return ""

def extract_questions(question_text):
    numbered = re.findall(r"\d+\.\s+(.*)", question_text)
    if numbered:
        return numbered
    fallback = [line.strip() for line in question_text.splitlines() if "?" in line]
    return fallback[:5]

def is_exit_command(user_input):
    return user_input.strip().lower() in ["exit", "quit", "bye"]

def extract_json(text):
    match = re.search(r'({.*?})', text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return None

def end_conversation():
    mood_str = ""
    if "sentiment_trend" in st.session_state:
        mood_str = f"\n\nThroughout the interview, you {get_user_mood(st.session_state['sentiment_trend'])}."
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": (
            f"Thank you for completing the interview! 🎉{mood_str}\n\n"
            "We appreciate your time and responses. Our team will review your answers and contact you with the next steps soon.\n\n"
            "Have a wonderful day! 👋"
        )
    })
    st.session_state.interview_finished = True