import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for API
BASE_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")

# Custom CSS for full-page styling
st.markdown("""
    <style>
    /* General page styling */
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
        margin: 0 auto 60px auto;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        text-align: center;
    }
    /* Centered footer styling */
    .footer-container {
        display: flex;
        justify-content: center;
        align-items: center;
        position: fixed;
        bottom: 10px;
        left: 0;
        right: 0;
        text-align: center;
    }
    .footer {
        font-size: 0.9em;
        color: #6c757d;
        background-color: rgba(255, 255, 255, 0.6);
        padding: 8px 16px;
        border-radius: 12px;
        backdrop-filter: blur(5px);
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .footer a {
        color: #007bff;
        text-decoration: none;
        font-weight: 500;
    }
    .footer a:hover {
        text-decoration: underline;
    }
    </style>
""", unsafe_allow_html=True)

# Display Title and Subtitle
st.markdown("<div class='title'>🤖 Welcome to <span style='color:#007bff;'>AI Quizzer</span></div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Learn and improve without limits 🚀</div>", unsafe_allow_html=True)

# Note Box
st.markdown("""
    <div class='note-box'>
        💡 <b>Note:</b> You can use <u>any username and password</u> of your choice to log in.<br>
        It will automatically create your account if it doesn’t exist yet.
    </div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
    <div class='footer-container'>
        <div class='footer'>
            Made with ❤️ by <b>Adi</b> | 
            <a href="https://github.com/AdityaVankani" target="_blank">GitHub</a> • 
            <a href="https://www.linkedin.com/in/adityavankani" target="_blank">LinkedIn</a>
        </div>
    </div>
""", unsafe_allow_html=True)