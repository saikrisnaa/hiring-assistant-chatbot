import streamlit as st
import json
from privacy import securely_store_candidate, cipher
from prompts import get_gathering_system_prompt, get_parsing_prompt, get_question_generation_prompt, get_feedback_prompt
from utils import call_llm, extract_questions, is_exit_command, extract_json, end_conversation
from sentiment import analyze_sentiment, get_empathy_prefix

# UI and Privacy - blocks before main logic
st.set_page_config(page_title="TalentScout", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
st.title("🤖 TalentScout - Hiring Assistant Chatbot")

with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; justify-content: center;">
            <img src="https://cdn-icons-png.flaticon.com/512/1250/1250689.png" width="100">
        </div>
        """,
        unsafe_allow_html=True
    )
    st.title("TalentScout")
    st.markdown(
        "**Hiring Assistant**\n\n"
        "Your data is anonymized for your privacy.\n"
    )
    st.info(
        "Your responses are collected solely for the purpose of this Screening demo. "
        "We do not store personal information and all data is anonymized. "
        "You may stop at any time."
    )

consent_given = st.sidebar.checkbox(
    "I agree to the collection and processing of my data in accordance with the privacy policy."
)

if not consent_given:
    st.warning("Please provide consent to continue the Screening.")
    st.stop()

# Initialize Session State 
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": get_gathering_system_prompt()},
        {"role": "assistant", "content": "**Welcome to TalentScout!**. I'm your Hiring Assistant Chatbot, here to guide you through a quick technical screening.\n\n"
        "We'll start by collecting a few basic details about you and then ask a few relevant questions "
        "based on your selected tech stack.\n\n" "To get started, what is your full name?"}
    ]
    
    st.session_state.candidate_data = {}
    st.session_state.questions_list = []
    st.session_state.current_question_index = 0
    st.session_state.gathering_phase = True
    st.session_state.interview_finished = False
    st.session_state.sentiment_trend = []  # New for advanced features

# To Display Chat History 
for message in st.session_state.chat_history:
    if message["role"] != "system":
        avatar = "🤖" if message["role"] == "assistant" else "🧑‍💻"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# Main Logic 
if not st.session_state.interview_finished:
    user_input = st.chat_input("Your response (or type 'exit' to end)")
    if user_input:
        # === ADV: Sentiment for every message ===
        user_sentiment = analyze_sentiment(user_input)
        st.session_state.sentiment_trend.append(user_sentiment)

        if user_input.lower().strip() in ["done", "next", "proceed"]:
            st.session_state.gathering_phase = False
            with st.spinner("Finalizing details and preparing questions..."):
                st.session_state.chat_history.append({"role": "user", "content": user_input})

                chat_history_trim = st.session_state.chat_history[-20:]
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history_trim])
                parsing_prompt = get_parsing_prompt(history_text)
                parsing_messages = [
                    {"role": "system", "content": "You are a JSON parsing expert."},
                    {"role": "user", "content": parsing_prompt}
                ]
                raw_json = call_llm(parsing_messages)

                try:
                    clean_json = extract_json(raw_json)
                    if not clean_json:
                        raise ValueError("No valid JSON found in output.")
                    st.session_state.candidate_data = json.loads(clean_json)

                    details_summary = "Excellent, thank you! Here is a summary of the information I've gathered:\n"
                    for key, value in st.session_state.candidate_data.items():
                        display_value = ', '.join(value) if isinstance(value, list) else value
                        details_summary += f"- **{key.replace('_', ' ').title()}:** {display_value}\n"
                    details_summary += "\n\nNow, let's move on to a few technical questions."
                    st.session_state.chat_history.append({"role": "assistant", "content": details_summary})

                    tech_stack = st.session_state.candidate_data.get("tech_stack", [])
                    question_prompt = get_question_generation_prompt(tech_stack)
                    q_gen_messages = [
                        {"role": "system", "content": "You are a technical question generator."},
                        {"role": "user", "content": question_prompt}
                    ]
                    questions_text = call_llm(q_gen_messages)
                    st.session_state.questions_list = extract_questions(questions_text)
                    if st.session_state.questions_list:
                        st.session_state.current_question_index = 0
                        first_question = st.session_state.questions_list[0]
                        st.session_state.chat_history.append({"role": "assistant", "content": first_question})
                    else:
                        end_conversation()
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    st.error(f"There was an issue processing your details. Raw output: {raw_json}\nError: {e}\nCould you please type 'done' again?")
                    st.session_state.gathering_phase = True
        elif is_exit_command(user_input):
            end_conversation()
        else:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            empathy = get_empathy_prefix(user_sentiment)  

            with st.spinner("Thinking..."):
                if st.session_state.gathering_phase:
                    ai_response = call_llm(st.session_state.chat_history)
                    st.session_state.chat_history.append({"role": "assistant", "content": empathy + ai_response})
                else:
                    current_q_index = st.session_state.current_question_index
                    question = st.session_state.questions_list[current_q_index]
                    feedback_prompt = get_feedback_prompt(question, user_input)
                    feedback_messages = [
                        {"role": "system", "content": "You are a helpful AI interview assistant."},
                        {"role": "user", "content": feedback_prompt}
                    ]
                    feedback = call_llm(feedback_messages)
                    st.session_state.chat_history.append({"role": "assistant", "content": empathy + feedback})

                    if feedback.startswith("IRRELEVANT_ANSWER"):
                        reask_msg = (
                            "It looks like your response may not have addressed the technical question above.\n\n"
                            "Let's try that again!\n\n"
                            f"**{question}**"
                        )
                        st.session_state.chat_history.append({"role": "assistant", "content": reask_msg})
                    else:
                        st.session_state.current_question_index += 1
                        if st.session_state.current_question_index < len(st.session_state.questions_list):
                            next_question = st.session_state.questions_list[st.session_state.current_question_index]
                            st.session_state.chat_history.append({"role": "assistant", "content": next_question})
                        else:
                            end_conversation()
        st.rerun()

# Display Candidate Info in Sidebar 
if st.session_state.candidate_data:
    st.sidebar.subheader("📝 Candidate Info")
    for key, value in st.session_state.candidate_data.items():
        display_value = ', '.join(value) if isinstance(value, list) else value
        st.sidebar.markdown(f"**{key.replace('_', ' ').title()}:** {display_value}")
    st.sidebar.subheader("📊 Candidate Screening Progress Bar")
    st.sidebar.progress(
        int(100 * (
            (st.session_state.current_question_index + st.session_state.gathering_phase) /
            (len(st.session_state.questions_list) + st.session_state.gathering_phase + 0.0001)
        ))
    )

# Store simulated data only after Screening is finished 
if st.session_state.interview_finished and st.session_state.candidate_data:
    securely_store_candidate(st.session_state.candidate_data)
    if st.button("Show simulated (anonymized) stored data"):
        with open("candidate.dat", "rb") as f:
            encrypted_data = f.read()
        decrypted_json = cipher.decrypt(encrypted_data).decode()
        st.json(json.loads(decrypted_json))
