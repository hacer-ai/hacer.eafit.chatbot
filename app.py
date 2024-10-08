 # Importing required packages
import streamlit as st
import openai
import uuid
import time
import io
from openai import OpenAI
import requests, os
#from langchain.llms import OpenAI

#Global Page Configuration
st.set_page_config(
    page_title="Nodo + Flutter",
    page_icon="🧠",
    initial_sidebar_state="collapsed",
)

# Initialize OpenAI client
client = OpenAI()

# Your chosen model
MODEL = "gpt-4-1106-preview"

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "run" not in st.session_state:
    st.session_state.run = {"status": None}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "retry_error" not in st.session_state:
    st.session_state.retry_error = 0

# Set up the page
#st.set_page_config(page_title="hacer.ai - Automatización")
st.sidebar.title("Nodo + Flutter")
st.sidebar.divider()
st.sidebar.markdown("Mentor de Flutter", unsafe_allow_html=True)
st.sidebar.markdown("hacer Agent Toolkit 1.0")
st.sidebar.divider()


tools_list = [
    {
        "type": "function",
        "function": {
            "name": "get_latest_company_news",
            "description": "Fetches the latest news articles related to a specified company",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The name of the company"
                    }
                },
                "required": ["company_name"]
            }
        }
    }
]

GNEWS_API_KEY = st.secrets["GNEWS_API_KEY"]

def get_latest_company_news(company_name):
    url = f"https://gnews.io/api/v4/search?q={company_name}&token={GNEWS_API_KEY}&lang=en&sortBy=publishedAt"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['articles']
    else:
        return []


st.write("""<img height="70" src="https://es.nodoeafit.com/wp-content/uploads/2024/09/flutter-head.png"/>""", unsafe_allow_html=True)

# File uploader for CSV, XLS, XLSX



# Initialize OpenAI assistant
if "assistant" not in st.session_state:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.assistant = openai.beta.assistants.retrieve(st.secrets["OPENAI_ASSISTANT"])
    st.session_state.thread = client.beta.threads.create(
        metadata={'session_id': st.session_state.session_id}
    )

# Display chat messages
elif hasattr(st.session_state.run, 'status') and st.session_state.run.status == "completed":
    st.session_state.messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread.id
    )
    for message in reversed(st.session_state.messages.data):
        if message.role in ["user", "assistant"]:
            with st.chat_message(message.role):
                for content_part in message.content:
                    message_text = content_part.text.value
                    st.markdown(message_text)

# Chat input and message creation with file ID
if prompt := st.chat_input("¿Cómo puedo ayudarte con tu proyecto de Flutter?"):
    with st.chat_message('user'):
        st.write(prompt)

    message_data = {
        "thread_id": st.session_state.thread.id,
        "role": "user",
        "content": prompt
    }

    # Include file ID in the request if available
    if "file_id" in st.session_state:
        message_data["file_ids"] = [st.session_state.file_id]

    st.session_state.messages = client.beta.threads.messages.create(**message_data)

    st.session_state.run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread.id,
        assistant_id=st.session_state.assistant.id,
    )
    if st.session_state.retry_error < 3:
        time.sleep(1)
        st.rerun()

# Handle run status
if hasattr(st.session_state.run, 'status'):
    if st.session_state.run.status == "running":
        with st.chat_message('assistant'):
            st.write("Buscando Información ......")
        if st.session_state.retry_error < 3:
            time.sleep(1)
            st.rerun()

    elif st.session_state.run.status == "failed":
        st.session_state.retry_error += 1
        with st.chat_message('assistant'):
            if st.session_state.retry_error < 3:
                st.write("Run failed, retrying ......")
                time.sleep(3)
                st.rerun()
            else:
                st.error("FAILED: The OpenAI API is currently processing too many requests. Please try again later ......")

    elif st.session_state.run.status != "completed":
        st.session_state.run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread.id,
            run_id=st.session_state.run.id,
        )
        if st.session_state.retry_error < 3:
            time.sleep(3)
            st.rerun()
