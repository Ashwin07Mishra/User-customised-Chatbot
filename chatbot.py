import streamlit as st
import requests

# --- CONFIG ---
LLM_API_URL = ""  # 👈 Replace with your actual LLM URL

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = "You are a helpful and intelligent chatbot designed to assist users in a polite and concise way."

# --- Session Chat History ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Title ---
st.title("💬 Custom LLM Chatbot")

# --- Chat Input ---
user_input = st.chat_input("Say something...")

if user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Construct full prompt
    full_prompt = SYSTEM_PROMPT + "\n\n"
    for msg in st.session_state.chat_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        full_prompt += f"{role}: {msg['content']}\n"
    full_prompt += "Assistant:"

    # Final payload structure for your LLM
    payload = {
        "input": {
            "prompt": full_prompt
        }
    }

    try:
        # Call the LLM
        res = requests.post(LLM_API_URL, json=payload)

        if res.status_code == 200:
            data = res.json()
            # Adjust based on your LLM's return structure
            reply = data.get("response") or data.get("output") or data.get("message") or "⚠️ No response key found."
        else:
            reply = f"❌ LLM Error {res.status_code}: {res.text}"

    except Exception as e:
        reply = f"❌ Exception occurred: {e}"

    # Add assistant reply to history
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

# --- Display Chat ---
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
