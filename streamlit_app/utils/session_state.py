import streamlit as st

def init_session_state():
    if "token" not in st.session_state:
        st.session_state.token = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "quiz" not in st.session_state:
        st.session_state.quiz = None