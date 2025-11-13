# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router
from app.quiz.routes import router as quiz_router
from app.database import create_tables
import streamlit as st
# ------------------------------
# FastAPI initialization
# ------------------------------
app = FastAPI(
    title="AI Quiz Microservice",
    description="Backend for AI-powered quiz with JWT authentication, Gemini-based AI scoring, and adaptive difficulty engine.",
    version="1.0.0"
)
if "API_URL" in st.secrets:
    BASE_URL = st.secrets["API_URL"]
else:
    BASE_URL = "http://127.0.0.1:8000"
# ------------------------------
# Middleware (CORS for frontend or testing tools)
# ------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later you can restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# Routers
# ------------------------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(quiz_router, tags=["Quiz"])

# ------------------------------
# Root endpoint
# ------------------------------
@app.get("/", tags=["Root"])
def root():
    return {"message": "AI Quiz Microservice is up and running 🚀"}

# ------------------------------
# Startup event — auto-create tables
# ------------------------------
@app.on_event("startup")
def on_startup():
    create_tables()
    print("✅ Database tables verified or created successfully.")
    print("🚀 AI Quiz Microservice is ready at: {BASE_URL}")