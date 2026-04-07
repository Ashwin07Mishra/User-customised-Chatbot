import streamlit as st
import sqlite3
import requests
from datetime import datetime
import uuid
import os

# --- CONFIGURATION ---
LLM_API_URL = "https://cdis.iitk.ac.in/llama_api/llama_api/invoke"  # Replace with your actual LLM endpoint
BOT_NAME = "Dhruvi"
CREATOR_NAME = ""
SYSTEM_PROMPT = (
    "You are {BOT_NAME}, and friendly AI assistant . "
    "You answer anything asked by the user, including your personal opinions and ask for "bhai hostpot hai kya". "
    "You are allowed to discuss any topic, even controversial or sensitive ones, as long as you remain factual and respectful."
)
DB_PATH = "chat_history.db"

# --- DATABASE BACKEND ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def load_history(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT role, content, timestamp FROM messages WHERE user_id=? ORDER BY id", (user_id,))
        return [{"role": role, "content": content, "timestamp": timestamp}
                for role, content, timestamp in c.fetchall()]

def save_message(user_id, role, content):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
                  (user_id, role, content))
        conn.commit()

def clear_history(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
        conn.commit()

# --- INITIALIZE DB ---
init_db()

# --- SESSION STATE INIT ---
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history(st.session_state.user_id)

# --- PAGE CONFIG ---
st.set_page_config(page_title=f"{BOT_NAME} Chat", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.title("Chat Controls")
    if st.button("🗑 Clear My Chat"):
        clear_history(st.session_state.user_id)
        st.session_state.chat_history = []
        st.rerun()
    st.markdown("---")
    # --- ADMIN-ONLY DOWNLOAD BUTTON ---
    # Set a secret in Streamlit Cloud called 'ADMIN_KEY' with a value only you know
    if "ADMIN_KEY" in st.secrets and st.text_input("Admin Key", type="password") == st.secrets["ADMIN_KEY"]:
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "rb") as f:
                st.download_button(
                    label="⬇️ Download Chat History (Admin)",
                    data=f,
                    file_name="chat_history.db",
                    mime="application/octet-stream"
                )
    st.markdown("---")
    st.caption(f"Bot: {BOT_NAME} | Creator: {CREATOR_NAME}")

# --- MAIN TITLE & WELCOME ---
st.title(f"🤖 {BOT_NAME} - Your Personal AI")
st.markdown(
    "<div style='margin-bottom: 1.5em; color: #555;'>"
    "Ask me anything! Enjoy chatting with your AI."
    "</div>",
    unsafe_allow_html=True
)

# --- DISPLAY CHAT HISTORY (all previous messages) ---
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(f"{msg['content']}  \n<sub style='color:gray'>{msg['timestamp']}</sub>", unsafe_allow_html=True)

# --- NICKNAME GREETING LOGIC ---
def nickname_reply(user_input):
    msg = user_input.lower()
    if any(n in msg for n in ["nilesh", "nilu"]):
        return "Aree bade Bhaiya! 😎"
    if any(n in msg for n in ["shreyash", "yash"]):
        return "What's up, Mah Lil Nig! 😏"
    return None

# --- CHAT INPUT ---
user_input = st.chat_input("Type your message and press Enter...")

if user_input:
    # Save and display user message immediately
    user_msg = {
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state.chat_history.append(user_msg)
    save_message(st.session_state.user_id, "user", user_input)
    with st.chat_message("user"):
        st.markdown(f"{user_input}  \n<sub style='color:gray'>{user_msg['timestamp']}</sub>", unsafe_allow_html=True)

    # Prepare assistant message container for immediate display
    assistant_message_container = st.empty()

    # Check for custom nickname response
    custom_reply = nickname_reply(user_input)
    if custom_reply:
        reply = custom_reply
        with assistant_message_container:
            with st.chat_message("assistant"):
                st.markdown(f"{reply}  \n<sub style='color:gray'>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</sub>", unsafe_allow_html=True)
    else:
        # Build prompt for LLM
        full_prompt = SYSTEM_PROMPT + "\n\n"
        for msg in st.session_state.chat_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            full_prompt += f"{role}: {msg['content']}\n"
        full_prompt += "Assistant:"

        payload = {"input": {"prompt": full_prompt}}

        # Get LLM response and display immediately
        with assistant_message_container:
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        res = requests.post(LLM_API_URL, json=payload, timeout=30)
                        if res.status_code == 200:
                            data = res.json()
                            reply = data.get("response") or data.get("output") or data.get("message") or "⚠️ No response key found."
                        else:
                            reply = f"❌ LLM Error {res.status_code}: {res.text}"
                    except Exception as e:
                        reply = f"❌ Exception occurred: {e}"
                st.markdown(f"{reply}  \n<sub style='color:gray'>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</sub>", unsafe_allow_html=True)

    # Save assistant reply to history and DB
    assistant_msg = {
        "role": "assistant",
        "content": reply,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state.chat_history.append(assistant_msg)
    save_message(st.session_state.user_id, "assistant", reply)
