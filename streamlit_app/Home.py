import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BASE_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")
st.write("Using API:", BASE_URL)
