import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8001"  # Adjust if needed

# Session state for auth and conv
if "token" not in st.session_state:
    st.session_state.token = None
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

def login():
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button and username and password:
            try:
                response = requests.post(
                    f"{API_BASE}/token", 
                    data={"username": username, "password": password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if response.status_code == 200:
                    st.session_state.token = response.json()["access_token"]
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error(f"Login failed: {response.json().get('detail', 'Invalid credentials')}")
            except requests.RequestException as e:
                st.error(f"Connection error: {str(e)}")

def register():
    st.subheader("Register")
    with st.form("register_form"):
        username = st.text_input("Username", key="reg_user")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password", key="reg_pass")
        submit_button = st.form_submit_button("Register")
        
        if submit_button and username and email and password:
            try:
                response = requests.post(
                    f"{API_BASE}/register", 
                    json={"username": username, "email": email, "password": password}
                )
                if response.status_code == 200:
                    st.success("Registered successfully! Now you can login.")
                else:
                    st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
            except requests.RequestException as e:
                st.error(f"Connection error: {str(e)}")

def upload_document():
    st.subheader("Upload Document")
    file = st.file_uploader("Choose a file (PDF/DOCX/TXT)")
    if file and st.button("Upload"):
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            files = {"file": (file.name, file.getvalue(), file.type)}
            response = requests.post(f"{API_BASE}/upload", headers=headers, files=files)
            if response.status_code == 200:
                st.success("Document uploaded and processed successfully!")
            else:
                st.error(f"Upload failed: {response.json().get('detail', 'Unknown error')}")
        except requests.RequestException as e:
            st.error(f"Connection error: {str(e)}")

def chat():
    st.subheader("Chat")
    
    # Load conversation history if conversation_id exists
    if st.session_state.conversation_id and not st.session_state.messages:
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            response = requests.get(f"{API_BASE}/history/{st.session_state.conversation_id}", headers=headers)
            if response.status_code == 200:
                st.session_state.messages = response.json()
        except requests.RequestException as e:
            st.error(f"Error loading chat history: {str(e)}")

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message("user" if msg["is_user"] else "assistant"):
            st.write(msg["content"])

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message to chat
        st.session_state.messages.append({"content": prompt, "is_user": True})
        with st.chat_message("user"):
            st.write(prompt)

        # Send message to API
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            data = {"message": prompt, "conversation_id": st.session_state.conversation_id}
            response = requests.post(f"{API_BASE}/chat", headers=headers, json=data)
            
            if response.status_code == 200:
                response_data = response.json()
                bot_response = response_data["response"]
                st.session_state.conversation_id = response_data["conversation_id"]
                st.session_state.messages.append({"content": bot_response, "is_user": False})
                with st.chat_message("assistant"):
                    st.write(bot_response)
            else:
                error_msg = f"Error: {response.json().get('detail', 'Unknown error')}"
                st.error(error_msg)
                st.session_state.messages.append({"content": error_msg, "is_user": False})
        except requests.RequestException as e:
            error_msg = f"Connection error: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"content": error_msg, "is_user": False})

# Add logout functionality
def logout():
    st.session_state.token = None
    st.session_state.conversation_id = None
    st.session_state.messages = []
    st.rerun()

# Main app
st.title("RAG Chatbot")

if not st.session_state.token:
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        login()
    with tab2:
        register()
else:
    # Add logout button in sidebar
    with st.sidebar:
        st.write("Logged in successfully!")
        if st.button("Logout"):
            logout()
        
        # Add new conversation button
        if st.button("New Conversation"):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()
    
    tab1, tab2 = st.tabs(["Upload Document", "Chat"])
    with tab1:
        upload_document()
    with tab2:
        chat()