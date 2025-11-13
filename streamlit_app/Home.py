import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for API
BASE_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")

# Inject custom CSS for styling
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #f5f7fa, #c3cfe2);
        font-family: 'Poppins', sans-serif;
    }
    .title {
        text-align: center;
        font-size: 2.5em;
        font-weight: 700;
        color: #2b2d42;
        margin-bottom: 0.2em;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2em;
        color: #4b4b4b;
        margin-bottom: 2em;
    }
    .note-box {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
        padding: 15px;
        border-radius: 10px;
        font-size: 1em;
        width: 80%;
        margin: 0 auto;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Display content
st.markdown("<div class='title'>🤖 Welcome to <span style='color:#007bff;'>AI Quizzer</span></div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Learn and improve without limits 🚀</div>", unsafe_allow_html=True)

st.markdown("""
    <div class='note-box'>
        💡 <b>Note:</b> You can use <u>any username and password</u> of your choice to log in.<br>
        It will automatically create your account if it doesn’t exist yet.
    </div>
""", unsafe_allow_html=True)