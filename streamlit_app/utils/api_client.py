import requests
import json

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


BASE_URL =  os.getenv("API_URL", "http://127.0.0.1:8000")  # FastAPI running locally

def login(username, password):
    try:
        res = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token")
        else:
            print(f"Login failed: {res.text}")
            return None
    except Exception as e:
        print(f"Login connection error: {e}")
        return None

def generate_quiz(token, payload):
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print("\n=== Sending to /quiz/generate ===")
        
        res = requests.post(
            f"{BASE_URL}/quiz/generate", 
            json=payload, 
            headers=headers,
            timeout=45  # Increased timeout for AI generation
        )
        
        if res.status_code != 200:
            return {"error": f"Failed to generate quiz: {res.status_code} - {res.text}"}
            
        data = res.json()
        
        if "error" in data:
            return {"error": data["error"]}
            
        if "quiz" not in data and "questions" not in data:
            return {"error": "No quiz data in response"}
            
        return data
        
    except Exception as e:
        return {"error": f"Network error: {str(e)}"}

def evaluate_quiz(token, payload):
    """
    Submit quiz answers for evaluation.
    Fixes the issue where dictionaries were being stringified instead of extracting the answer text.
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if 'quiz_id' not in payload or 'user_answers' not in payload:
            return {"error": "Missing required fields in payload."}
        
        # --- FIX STARTS HERE ---
        # The frontend sends a list of dictionaries (metadata + answer).
        # We need to extract just the answer text string for the backend to evaluate.
        raw_answers = payload['user_answers']
        cleaned_answers = []

        if isinstance(raw_answers, list):
            for item in raw_answers:
                if isinstance(item, dict):
                    # Extract the 'answer' key if it's a dictionary
                    # Example: item is {'question_id': 'q_0', 'answer': 'A) 25', ...}
                    cleaned_answers.append(str(item.get('answer', '')))
                else:
                    # If it's already a string/int, just use it
                    cleaned_answers.append(str(item) if item is not None else "")
        else:
            return {"error": "user_answers must be a list"}
        # --- FIX ENDS HERE ---

        request_data = {
            "quiz_id": int(payload['quiz_id']),
            "user_answers": cleaned_answers 
        }
        
        print(f"\n=== Submitting Answers ===")
        print(f"Quiz ID: {request_data['quiz_id']}")
        print(f"Processed Answers: {request_data['user_answers']}")
        
        response = requests.post(
            f"{BASE_URL}/quiz/evaluate",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                return {"error": error_data.get('detail', response.text)}
            except:
                return {"error": f"Evaluation failed: {response.status_code}"}
        
        return response.json()
            
    except Exception as e:
        print(f"Evaluate error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

def get_history(token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/quiz/history", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"History error: {e}")
        return []

def get_quiz_by_id(token, quiz_id):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/quiz/{quiz_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"error": "Quiz not found"}
    except Exception as e:
        return {"error": str(e)}

def get_ai_hint(token, question_text, user_answer=""):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"question": question_text, "user_answer": user_answer}
        
        response = requests.post(
            f"{BASE_URL}/quiz/hint",
            json=payload,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("hint", "No hint available.")
        return "Hint unavailable."
    except Exception:
        return "Hint unavailable."

def get_next_difficulty(token, previous_score):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"previous_score": previous_score}
        res = requests.post(f"{BASE_URL}/quiz/next_difficulty", json=payload, headers=headers)
        if res.status_code == 200:
            return res.json().get("next_difficulty", "MEDIUM")
    except:
        pass
    return "MEDIUM"

def get_leaderboard(token, grade=None, subject=None):
    """
    Fetch leaderboard data.
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if grade: params['grade'] = grade
        if subject: params['subject'] = subject
        
        response = requests.get(
            f"{BASE_URL}/quiz/leaderboard", 
            headers=headers, 
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return {"entries": []}
    except Exception as e:
        print(f"Leaderboard API Error: {e}")
        return {"entries": []}