import streamlit as st
from dotenv import load_dotenv

# 🌍 Load environment variables
load_dotenv()
BASE_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")

# 🎨 Page Configuration
st.set_page_config(
    page_title="AI Quizzer",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 🧠 Custom CSS for a Professional, Modern Look
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(135deg, #141e30, #243b55);
        color: #ffffff;
    }
    .main-card {
        background-color: rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 3rem 3rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        backdrop-filter: blur(8px);
        transition: all 0.3s ease-in-out;
    }
    .main-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 30px rgba(0,0,0,0.5);
    }
    h1 {
        color: #00ffc8;
        font-weight: 700;
        font-size: 2.6rem;
        margin-bottom: 0.4rem;
    }
    h3 {
        color: #b0b0b0;
        font-weight: 400;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .note {
        background-color: rgba(0, 255, 200, 0.15);
        color: #00ffc8;
        border: 1px solid rgba(0, 255, 200, 0.4);
        border-radius: 10px;
        padding: 1rem;
        margin: 1.5rem 0;
        font-size: 0.95rem;
        font-weight: 500;
    }
    .stButton>button {
        background-color: #00ffc8;
        color: black;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00d4aa;
        transform: scale(1.05);
    }
    .footer {
        margin-top: 2rem;
        font-size: 0.9rem;
        color: #cccccc;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 💡 Main Content Layout
st.markdown('<div class="main-card">', unsafe_allow_html=True)
st.markdown("## 🧠 Welcome to **AI Quizzer**")
st.markdown("### Learn smarter, level up faster — no limits, just growth 🚀")

st.write(
    "AI Quizzer adapts to your performance, generating personalized quizzes "
    "that challenge your current level and help you improve progressively. "
    "Track your progress, compete in leaderboards, and unlock smarter learning."
)

# 🧩 Info Note about Login
st.markdown(
    """
    <div class="note">
    💡 <b>Note:</b> You can use <b>any username and password</b> of your choice to log in.<br>
    No registration is required — just enter your preferred credentials to continue.
    </div>
    """,
    unsafe_allow_html=True,
)

# 🌐 Show connected backend URL
st.write(f"**Connected API Base:** `{BASE_URL}`")

# 🚀 Call-to-Action Button
col1, col2, col3 = st.columns(3)
with col2:
    if st.button("🔐 Go to Login"):
        st.switch_page("pages/Login.py")

st.markdown('<p class="footer">Developed by Aditya Vankani • © 2025 AI Quizzer</p>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)