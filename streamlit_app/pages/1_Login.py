import streamlit as st
from utils.api_client import login
from utils.session_state import init_session_state

init_session_state()

st.title("🔐 Login to AI Quiz Platform")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    token = login(username, password)
    if token:
        st.session_state.token = token
        st.session_state.username = username
        st.success("✅ Logged in successfully!")
        st.switch_page("pages/2_Generate_Quiz.py")
    else:
        st.error("❌ Invalid login.")