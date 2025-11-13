# 🧠 AI Quizzer - Adaptive Learning Platform

**AI Quizzer** is a full-stack educational application that leverages **Generative AI** to create personalized, adaptive assessments. It features a **FastAPI backend** for robust logic and data management, and a **Streamlit frontend** for an interactive user experience.

---
## Live Demo

[https://aiquizzer.streamlit.app](https://aiquizzer.streamlit.app)

---

## 🚀 Key Features

- **🤖 AI-Powered Generation:** Instantly generates quizzes for any subject and grade level (1–12) using Google Gemini.
- **📈 Adaptive Difficulty:** Automatically adjusts question difficulty (Easy/Medium/Hard) based on the user's historical performance.
- **💡 Real-Time Hints:** Users can request AI-generated hints for specific questions without revealing the answer.
- **📝 Detailed Explanations:** Provides instant feedback with detailed AI explanations for every correct and incorrect answer.
- **📊 Analytics & History:** Tracks performance over time with history logs, scoring percentages, and retake capabilities.
- **🏆 Leaderboard:** Displays top-performing students filtered by grade and subject.
- **🔒 Secure Authentication:** JWT-based authentication for secure user signup and login.

---

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI
- **Database:** SQLite (Local) / PostgreSQL (Production)
- **ORM:** SQLAlchemy
- **AI Model:** Google Gemini 2.0 Flash (`google-generativeai`)
- **Authentication:** OAuth2 with JWT (`python-jose`, `passlib`)

### Frontend
- **Framework:** Streamlit
- **HTTP Client:** Python Requests
- **Visualization:** Pandas (for Leaderboard tables)

---

## ⚙️ Local Installation & Setup

Follow these steps to run **AI Quizzer** locally on your system.

### 🧩 1. Clone the Repository

```bash
git clone [https://github.com/AdityaVankani/ai_quizzer.git](https://github.com/AdityaVankani/ai_quizzer.git)
cd ai-quizzer
```
## ⚙️ 2. Backend Setup

It is recommended to run the backend in a virtual environment.

### A. Create Virtual Environment & Install Dependencies

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```
### B. Configuration (.env)

Create a file named `.env` in the root directory and add the following:

```bash

GEMINI_API_KEY=your_google_gemini_api_key_here
JWT_SECRET=your_random_secret_string_for_jwt

```
### C. Run the Backend

```bash
uvicorn app.main:app --reload
```

Once started, the FastAPI backend will be available at: 👉 http://127.0.0.1:8000

You can also explore the interactive API docs at: 👉 http://127.0.0.1:8000/docs

## 🎨 3. Frontend Setup (Streamlit App)

Open a **new terminal** (keep the backend running).

### 🧰 Install Dependencies
```bash

pip install -r requirements.txt
streamlit run streamlit_app/Home.py
```
Once started, the Streamlit frontend will open automatically in your browser at:
👉 http://localhost:8501￼

## 🧩 Key Functionality Details

### 🎯 Adaptive Difficulty Logic

The system calculates a **`performance_ratio`** based on the user’s last 3 quizzes in a specific subject:

| Performance Range | Difficulty Adjustment |
|--------------------|------------------------|
| > 80% Score        | Shifts question distribution toward **Hard** |
| 50% - 80% Score    | Maintains a **Balanced** question set |
| < 50% Score        | Shifts question distribution toward **Easy** |

---

### 🏅 Leaderboard Logic

Rankings are calculated dynamically based on the following criteria:

1. **Highest Total Score**  
2. **Highest Max Possible Score** *(Tie-breaker 1: Harder quizzes rank higher)*  
3. **Most Recent Submission** *(Tie-breaker 2)*  

---

## 🔍 Quiz History Filters

The **History** page includes a robust filtering system to help students track their academic progress over time.

---

### 1. 🧠 Subject Filter

This filter isolates performance in specific academic areas.

- **Dynamic Population:** The filter options are *not hardcoded*. The system dynamically scans the user's history to find unique subjects and populates the dropdown.  
- **Visual Enhancement:** Subject names are automatically mapped to specific emojis (e.g., *Mathematics → 🔢*, *Science → 🔬*) for an intuitive UI.  
- **Logic:** Defaults to **"All Subjects"** but allows instant filtering for specific subjects.  

---

### 2. 📅 Date Range Filter

This filter enables analysis of performance during specific timeframes (e.g., a particular semester).

- **Smart Defaults:** To prevent information overload, the view defaults to the **last 30 days**.  
- **Data-Aware Constraints:** The date pickers automatically set their minimum and maximum limits based on the user's actual quiz history — preventing invalid selections.  
- **Logic Validation:** The system ensures the **"Start Date"** is never later than the **"End Date"**.  