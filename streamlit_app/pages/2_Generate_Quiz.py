import streamlit as st
from utils.api_client import generate_quiz, get_next_difficulty, get_history
from utils.session_state import init_session_state
from datetime import datetime, timedelta
import time

# Initialize basic session state
init_session_state()

# Available subjects with emojis
SUBJECTS = {
    "Mathematics": "🔢", "Science": "🔬", "English": "📚", "History": "🏛️",
    "Geography": "🌍", "Computer Science": "💻", "Physics": "⚛️", "Chemistry": "🧪",
    "Biology": "🧬", "Economics": "💹", "Art": "🎨", "Music": "🎵"
}

def get_recent_performance():
    """Get the user's recent quiz performance to suggest difficulty"""
    try:
        history = get_history(st.session_state.token)
        if not history or not isinstance(history, list):
            return None
            
        recent_quizzes = []
        for item in history:
            if isinstance(item, dict) and 'date' in item and 'percentage' in item:
                try:
                    quiz_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
                    if (datetime.now().date() - quiz_date) <= timedelta(days=30):
                        recent_quizzes.append(item)
                except (ValueError, TypeError):
                    continue
        
        if not recent_quizzes:
            return None
            
        total = sum(float(q.get('percentage', 0)) for q in recent_quizzes if q.get('percentage') is not None)
        return total / len(recent_quizzes)
    except Exception as e:
        print(f"Error getting recent performance: {e}")
        return None

st.title("🧠 Generate New Quiz")

if not st.session_state.token:
    st.warning("Please log in first!")
    st.stop()

# Check for recent performance
recent_performance = get_recent_performance()
suggested_difficulty = None

if recent_performance is not None:
    try:
        suggested_difficulty = get_next_difficulty(st.session_state.token, recent_performance)
        st.sidebar.metric("Your Recent Performance", f"{recent_performance:.1f}%")
        if suggested_difficulty:
            st.sidebar.info(f"Suggested difficulty: {suggested_difficulty}")
    except Exception:
        suggested_difficulty = "MEDIUM"

# Quiz generation form
with st.form("quiz_form"):
    col1, col2 = st.columns(2)
    with col1:
        grade = st.number_input("Grade", min_value=1, max_value=12, step=1, value=5)
        subject = st.selectbox("Subject", options=list(SUBJECTS.keys()), format_func=lambda x: f"{SUBJECTS[x]} {x}")
    
    with col2:
        st.markdown("### 📝 Quiz Configuration")
        total_questions = st.slider("Number of Questions", 5, 30, 10)
        max_score = total_questions * 2
        
        st.info(f"• Total questions: {total_questions}")
        st.info(f"• Max score: {max_score}")

    # Default values
    include_images = True
    time_limit = 30
    enable_hints = True
    adaptive_difficulty = True if suggested_difficulty else False
    
    if st.form_submit_button("🚀 Generate Quiz", use_container_width=True):
        with st.spinner("🧠 Crafting your personalized quiz..."):
            try:
                # Calculate distribution
                default_easy = max(1, int(total_questions * 0.4))
                default_medium = max(1, int(total_questions * 0.4))
                default_hard = max(1, total_questions - default_easy - default_medium)
                
                payload = {
                    "subject": subject,
                    "grade": int(grade),
                    "total_questions": int(total_questions),
                    "max_score": int(max_score),
                    "question_distribution": {"easy": default_easy, "medium": default_medium, "hard": default_hard},
                    "points_strategy": {"easy": 1.0, "medium": 2.0, "hard": 3.0},
                    "include_images": bool(include_images),
                    "time_limit": int(time_limit),
                    "enable_hints": bool(enable_hints),
                    "adaptive_difficulty": bool(adaptive_difficulty),
                    "difficulty": suggested_difficulty or "ADAPTIVE"
                }
                
                res = generate_quiz(st.session_state.token, payload)
                
                if "error" in res:
                    st.error(f"❌ {res['error']}")
                else:
                    # NORMALIZATION LOGIC:
                    # 1. Extract inner 'quiz' dict if it exists (backend structure)
                    # 2. Or use 'res' directly if it's flat
                    if 'quiz' in res and isinstance(res['quiz'], dict):
                        raw_quiz = res['quiz']
                        # Sometimes ID is at root, sometimes inside
                        quiz_id = res.get('id', raw_quiz.get('id'))
                    else:
                        raw_quiz = res
                        quiz_id = res.get('id')

                    questions = raw_quiz.get('questions', [])
                    
                    if not questions:
                        st.error("❌ API returned success but no questions found.")
                        st.stop()

                    # Create the standardized structure for Take Quiz
                    final_quiz_data = {
                        'id': quiz_id,
                        'questions': questions,
                        'metadata': {
                            'subject': subject,
                            'difficulty': suggested_difficulty or "ADAPTIVE",
                            'time_limit': time_limit,
                            'enable_hints': enable_hints,
                            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                    }
                    
                    # SAVE TO SESSION STATE
                    st.session_state.quiz = final_quiz_data
                    
                    # Clean up previous quiz states
                    if 'quiz_state' in st.session_state:
                        del st.session_state.quiz_state
                    
                    st.success("✅ Quiz generated successfully!")
                    time.sleep(1)
                    st.switch_page("pages/3_Take_Quiz.py")
                        
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")