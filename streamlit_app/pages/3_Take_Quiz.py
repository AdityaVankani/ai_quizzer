import streamlit as st
from utils.api_client import evaluate_quiz, get_quiz_by_id, get_ai_hint
import time
import hashlib

# Constants
QUESTION_PREFIX = "q_"
HINT_PREFIX = "hint_"
RADIO_PREFIX = "radio_"

class QuizManager:
    """Manages quiz state and operations."""
    
    @staticmethod
    def initialize_session_state():
        """Initialize all required session state variables."""
        if 'quiz_state' not in st.session_state:
            st.session_state.quiz_state = {
                'answers': {},
                'current_question': 0,
                'start_time': time.time(),
                'hints_shown': {},
                'hint_contents': {},
                'hint_loading': {},
                'quiz': None, 
                'is_submitted': False,
                'result': None
            }

    @staticmethod
    def load_quiz():
        # Case A: Retaking a quiz from History page
        if 'retake_quiz_id' in st.session_state and st.session_state.retake_quiz_id:
            return QuizManager._load_retake_quiz()
        
        # Case B: Taking a newly generated quiz
        return QuizManager._load_current_quiz()
    
    @staticmethod
    def _load_retake_quiz():
        with st.spinner("Loading quiz..."):
            quiz_data = get_quiz_by_id(st.session_state.token, st.session_state.retake_quiz_id)
            
            if 'error' in quiz_data:
                st.error(f"Error loading quiz: {quiz_data['error']}")
                if st.button("Back to History", key="back_to_hist_err"):
                    del st.session_state.retake_quiz_id
                    st.switch_page("pages/4_History.py")
                return False
            
            normalized_quiz = {
                'questions': quiz_data.get('quiz', {}).get('questions', []),
                'metadata': quiz_data.get('quiz', {}).get('metadata', {}),
                'id': quiz_data.get('id')
            }

            st.session_state.quiz_state['quiz'] = normalized_quiz
            del st.session_state.retake_quiz_id
            st.rerun()
        return True
    
    @staticmethod
    def _load_current_quiz():
        if st.session_state.quiz_state.get('quiz'):
            return True

        if 'quiz' in st.session_state and st.session_state.quiz:
            st.session_state.quiz_state['quiz'] = st.session_state.quiz
            st.session_state.quiz_state['start_time'] = time.time()
            return True
            
        st.info("No active quiz found.")
        if st.button("Generate New Quiz", key="gen_new_quiz_missing"):
            st.switch_page("pages/2_Generate_Quiz.py")
        return False
    
    @staticmethod
    def get_questions():
        quiz = st.session_state.quiz_state.get('quiz')
        if not quiz:
            return []
        return quiz.get('questions', [])
    
    @staticmethod
    def get_question_options(question):
        if 'options' in question:
            return question['options']
        if 'choices' in question:
            return question['choices']
        return []
    
    @staticmethod
    def get_question_key(question_index):
        return f"{QUESTION_PREFIX}{question_index}"
    
    @staticmethod
    def get_hint_key(question_index):
        return f"{HINT_PREFIX}{question_index}"
    
    @staticmethod
    def show_question(question, question_index):
        st.subheader(f"Question {question_index + 1}")
        st.markdown(f"**{question.get('question', '')}**")
        
        options = QuizManager.get_question_options(question)
        question_key = QuizManager.get_question_key(question_index)
        
        if question_key not in st.session_state.quiz_state['answers']:
            st.session_state.quiz_state['answers'][question_key] = None
        
        if options:
            radio_key = f"{RADIO_PREFIX}{question_index}_v{int(st.session_state.quiz_state['start_time'])}"
            
            selected = st.radio(
                "Select your answer:",
                options=options,
                index=st.session_state.quiz_state['answers'][question_key],
                key=radio_key
            )
            
            if selected in options:
                answer_index = options.index(selected)
                st.session_state.quiz_state['answers'][question_key] = answer_index
    
    @staticmethod
    def show_hint_section(question, question_index):
        hint_key = QuizManager.get_hint_key(question_index)
        
        if hint_key not in st.session_state.quiz_state['hints_shown']:
            st.session_state.quiz_state['hints_shown'][hint_key] = False
            st.session_state.quiz_state['hint_contents'][hint_key] = None
            st.session_state.quiz_state['hint_loading'][hint_key] = False
        
        btn_key = f"hint_btn_{question_index}"
        
        if st.button(
            "💡 Get a Hint" if not st.session_state.quiz_state['hints_shown'][hint_key] else "❌ Hide Hint",
            key=btn_key,
            disabled=st.session_state.quiz_state['hint_loading'][hint_key]
        ):
            if not st.session_state.quiz_state['hints_shown'][hint_key] and \
               not st.session_state.quiz_state['hint_contents'][hint_key]:
                
                st.session_state.quiz_state['hint_loading'][hint_key] = True
                st.session_state.quiz_state['hints_shown'][hint_key] = True
                st.rerun()
            else:
                st.session_state.quiz_state['hints_shown'][hint_key] = \
                    not st.session_state.quiz_state['hints_shown'][hint_key]
                st.rerun()

        if st.session_state.quiz_state['hint_loading'][hint_key]:
             with st.spinner("Generating hint..."):
                try:
                    hint = get_ai_hint(
                        st.session_state.token,
                        question.get('question', ''),
                        None
                    )
                    st.session_state.quiz_state['hint_contents'][hint_key] = hint
                except Exception:
                    st.session_state.quiz_state['hint_contents'][hint_key] = "Hint unavailable."
                finally:
                    st.session_state.quiz_state['hint_loading'][hint_key] = False
                    st.rerun()

        if st.session_state.quiz_state['hints_shown'][hint_key] and st.session_state.quiz_state['hint_contents'][hint_key]:
             st.info(f"💡 **Hint:** {st.session_state.quiz_state['hint_contents'][hint_key]}")
    
    @staticmethod
    def show_navigation_buttons(total_questions):
        col1, col2, col3 = st.columns([1, 1, 1])
        current_q = st.session_state.quiz_state['current_question']
        
        with col1:
            if current_q > 0:
                if st.button("⬅️ Previous", key="nav_prev"):
                    st.session_state.quiz_state['current_question'] -= 1
                    st.rerun()
        
        with col2:
            if current_q < total_questions - 1:
                if st.button("Next ➡️", key="nav_next"):
                    st.session_state.quiz_state['current_question'] += 1
                    st.rerun()
            else:
                if st.button("✅ Submit Quiz", key="nav_submit", type="primary"):
                    QuizManager.submit_quiz()
        
        with col3:
            if st.button("🔁 Restart", key="nav_restart"):
                st.session_state.quiz_state['answers'] = {}
                st.session_state.quiz_state['current_question'] = 0
                st.session_state.quiz_state['is_submitted'] = False
                st.session_state.quiz_state['start_time'] = time.time()
                st.rerun()

    @staticmethod
    def submit_quiz():
        try:
            quiz_id = st.session_state.quiz_state['quiz'].get('id')
            if not quiz_id:
                st.error("❌ Error: Quiz ID is missing. Cannot submit.")
                return

            questions = QuizManager.get_questions()
            answers_formatted = []
            
            for i, question in enumerate(questions):
                question_key = QuizManager.get_question_key(i)
                answer_idx = st.session_state.quiz_state['answers'].get(question_key)
                
                answer_text = ""
                if answer_idx is not None:
                    options = QuizManager.get_question_options(question)
                    if answer_idx < len(options):
                        answer_text = options[answer_idx]
                
                answers_formatted.append({
                    'question_id': question.get('id', f"q_{i}"),
                    'question_text': question.get('question', ''),
                    'answer': answer_text,
                    'options': question.get('options', [])
                })
            
            # NOTE: api_client.py now handles extracting the answer string
            payload = {
                'quiz_id': quiz_id,
                'user_answers': answers_formatted,
                'time_taken': int(time.time() - st.session_state.quiz_state['start_time'])
            }
            
            result = evaluate_quiz(st.session_state.token, payload)
            
            if 'error' in result:
                st.error(f"Error: {result['error']}")
                return
            
            st.session_state.quiz_state['is_submitted'] = True
            st.session_state.quiz_state['result'] = result
            st.rerun()
            
        except Exception as e:
            st.error(f"Submission error: {str(e)}")

    @staticmethod
    def show_quiz_result():
        result = st.session_state.quiz_state['result']
        st.balloons()
        st.success("🎉 Quiz Submitted!")
        
        # Score Display
        score_val = result.get('total_score', result.get('score', 0))
        max_score_val = result.get('max_score', 0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Score", f"{score_val} / {max_score_val}")
        with col2:
            st.metric("Percentage", f"{result.get('percentage', 0):.1f}%")
        
        st.subheader("Detailed Results & Explanations")
        questions = QuizManager.get_questions()
        feedback_list = result.get('feedback', [])
        
        for i, question in enumerate(questions):
            # Default values
            is_correct = False
            correct_answer_text = "N/A"
            explanation = "No explanation available."
            
            if i < len(feedback_list):
                fb_item = feedback_list[i]
                is_correct = fb_item.get('is_correct', False)
                correct_answer_text = fb_item.get('correct_answer', 'N/A')
                # Get the explanation sent from backend
                explanation = fb_item.get('explanation', None)

            # Visual Indicator
            icon = "✅" if is_correct else "❌"
            
            # Create Expander
            with st.expander(f"{icon} Question {i+1}: {question.get('question', '')}", expanded=True):
                
                # 1. Display User Answer
                q_key = QuizManager.get_question_key(i)
                ans_idx = st.session_state.quiz_state['answers'].get(q_key)
                options = QuizManager.get_question_options(question)
                user_ans = options[ans_idx] if ans_idx is not None else "No Answer"
                
                st.markdown(f"**Your Answer:** {user_ans}")
                
                # 2. Display Correct Answer (styled)
                if not is_correct:
                    st.error(f"**Correct Answer:** {correct_answer_text}")
                else:
                    st.success(f"**Correct Answer:** {correct_answer_text}")
                
                # 3. Display AI Explanation
                if explanation:
                    st.info(f"**ℹ️ Explanation:**\n\n{explanation}")
                else:
                    st.caption("No detailed explanation available for this question.")

        st.markdown("---")
        if st.button("🔄 Take Another Quiz", key="btn_take_another", use_container_width=True):
            del st.session_state.quiz_state
            st.switch_page("pages/2_Generate_Quiz.py")

def main():
    QuizManager.initialize_session_state()
    
    if 'token' not in st.session_state or not st.session_state.token:
        st.error("🔐 Please log in to take a quiz.")
        return
    
    if not QuizManager.load_quiz():
        return
    
    st.title("📝 Take Quiz")
    
    if st.session_state.quiz_state.get('is_submitted'):
        QuizManager.show_quiz_result()
    else:
        questions = QuizManager.get_questions()
        if not questions:
            st.error("Error: Quiz structure is invalid (no questions found).")
            if st.button("Return to Generator", key="err_return_btn"):
                st.switch_page("pages/2_Generate_Quiz.py")
            return

        current_q = st.session_state.quiz_state['current_question']
        if current_q >= len(questions):
            st.session_state.quiz_state['current_question'] = 0
            st.rerun()
            
        QuizManager.show_question(questions[current_q], current_q)
        
        with st.expander("Need a hint?"):
            QuizManager.show_hint_section(questions[current_q], current_q)
        
        st.markdown("---")
        QuizManager.show_navigation_buttons(len(questions))

if __name__ == "__main__":
    main()