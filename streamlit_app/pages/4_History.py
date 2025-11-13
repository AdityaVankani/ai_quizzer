import streamlit as st
from utils.api_client import get_history
from datetime import datetime, timedelta, timezone
import pytz

# Available subjects with emojis
SUBJECTS = {
    "Mathematics": "🔢",
    "Science": "🔬",
    "English": "📚",
    "History": "🏛️",
    "Geography": "🌍",
    "Computer Science": "💻",
    "Physics": "⚛️",
    "Chemistry": "🧪",
    "Biology": "🧬",
    "Economics": "💹",
    "Art": "🎨",
    "Music": "🎵"
}

def get_subject_with_emoji(subject_name):
    """Return subject name with emoji if available, otherwise return as is"""
    if not subject_name:
        return "General"
    return f"{SUBJECTS.get(subject_name, '📝')} {subject_name}"

st.set_page_config(page_title="Quiz History", layout="wide")

def parse_date(date_str):
    """Parse date string to datetime.date object"""
    if not date_str:
        return None
        
    date_str = str(date_str)
    formats = [
        '%Y-%m-%dT%H:%M:%S.%f',  # ISO format with microseconds
        '%Y-%m-%dT%H:%M:%S',     # ISO format without microseconds
        '%Y-%m-%d %H:%M:%S',     # SQLite format
        '%Y-%m-%d'               # Date only
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.split('+')[0].strip(), fmt).date()
        except ValueError:
            continue
    return None

def get_date_range():
    """Get default date range (last 30 days)"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    return start_date, end_date

def main():
    st.title("📜 Quiz History")

    if not st.session_state.get('token'):
        st.warning("Please log in first!")
        return

    try:
        # Load data with loading indicator
        with st.spinner("Loading your quiz history..."):
            data = get_history(st.session_state.token)
            
            if isinstance(data, dict) and 'error' in data:
                st.error(f"❌ {data['error']}")
                return
                
            if not data:
                st.info("No quiz history found. Take a quiz to see your history!")
                return
            
            # Normalize data format
            history_items = data.get("results", data) if isinstance(data, dict) else data
            
            if not isinstance(history_items, list):
                st.error("❌ Invalid data format received from server")
                if st.checkbox("Show raw response"):
                    st.json(data)
                return
                
            # Process and validate items
            valid_items = []
            for item in history_items:
                if not isinstance(item, dict):
                    continue
                # Ensure required fields exist
                if 'created_at' not in item:
                    continue
                valid_items.append(item)
                
            if not valid_items:
                st.info("No valid quiz attempts found in your history.")
                return
                
            # Sort by date (newest first)
            valid_items.sort(
                key=lambda x: parse_date(x['created_at']) or datetime.min.date(),
                reverse=True
            )
            
            # Get unique subjects from all possible subject fields
            subjects = set()
            subject_map = {}  # Map display name to original name
            
            for item in valid_items:
                # Try different possible subject fields
                subject = (
                    item.get('subject') or 
                    item.get('quiz', {}).get('subject') or 
                    item.get('quiz_subject')
                )
                if subject and str(subject).strip():
                    subject = str(subject).strip()
                    display_name = get_subject_with_emoji(subject)
                    subjects.add(display_name)
                    subject_map[display_name] = subject
            
            # Sort subjects alphabetically by display name
            subjects = sorted(list(subjects))
            
        # Filters
        st.sidebar.header("🔍 Filters")
        
        # Subject filter with emojis
        st.sidebar.subheader("Subject")
        subject_options = ["All Subjects"] + subjects
        selected_display = st.sidebar.selectbox(
            "Select Subject",
            subject_options,
            key="subject_filter_display",
            index=0
        )
        
        # Map the selected display name back to the original subject name
        if selected_display == "All Subjects":
            subject_filter = "All Subjects"
        else:
            subject_filter = subject_map.get(selected_display, selected_display.replace(selected_display.split(' ')[0] + ' ', ''))
        
        # Date range filter
        st.sidebar.subheader("Date Range")
        
        # Get min and max dates from the data
        min_date = min(parse_date(item.get('created_at')) or datetime.max.date() for item in valid_items)
        max_date = max(parse_date(item.get('created_at')) or datetime.min.date() for item in valid_items)
        
        # Set default date range to last 30 days, but within the available data range
        default_end = min(datetime.now().date(), max_date)
        default_start = max(min_date, default_end - timedelta(days=30))
        
        # Date inputs with validation
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input(
                "From",
                value=default_start,
                min_value=min_date,
                max_value=max_date,
                key="start_date"
            )
        with col2:
            end_date = st.date_input(
                "To",
                value=default_end,
                min_value=min_date,
                max_value=max_date,
                key="end_date"
            )
        
        # Validate date range
        if start_date > end_date:
            st.sidebar.error("End date must be after start date")
            st.stop()
            
        # Apply filters
        filtered_items = []
        for item in valid_items:
            # Get the item's subject from all possible fields
            item_subject = (
                item.get('subject') or 
                item.get('quiz', {}).get('subject') or 
                item.get('quiz_subject') or 
                'General'
            )
            
            # Apply subject filter
            if subject_filter != "All Subjects":
                if str(item_subject).strip().lower() != subject_filter.lower():
                    continue
                    
            # Apply date filter
            item_date = parse_date(item.get('created_at'))
            if not item_date:
                continue
            
            # Ensure both dates are timezone-aware and in the same timezone (UTC)
            if isinstance(item_date, datetime):
                if item_date.tzinfo is None:
                    item_date = item_date.replace(tzinfo=timezone.utc)
                # Convert to date for comparison
                item_date = item_date.date()
            
            # Ensure the date is within the selected range (inclusive)
            if isinstance(start_date, datetime):
                start = start_date.date()
            else:
                start = start_date
                
            if isinstance(end_date, datetime):
                end = end_date.date()
            else:
                end = end_date
            
            if start <= item_date <= end:
                filtered_items.append(item)
                
        # Show active filters with better formatting
        st.sidebar.markdown("---")
        
        # Format date range display
        start_fmt = start_date.strftime('%b %d, %Y') if hasattr(start_date, 'strftime') else str(start_date)
        end_fmt = end_date.strftime('%b %d, %Y') if hasattr(end_date, 'strftime') else str(end_date)
        
        st.sidebar.markdown("### Active Filters")
        st.sidebar.markdown(f"**Subject:** {selected_display if subject_filter != 'All Subjects' else 'All Subjects'}")
        st.sidebar.markdown(f"**Date Range:** {start_fmt} to {end_fmt}")
        st.sidebar.markdown(f"**Showing:** {len(filtered_items)} of {len(valid_items)} quizzes")
                
        # Display results with improved layout
        st.subheader(f"📋 Quiz History ({len(filtered_items)} records)")
        
        if not filtered_items:
            st.info("No quizzes match your filters. Try adjusting your criteria.")
            return
            
        # Create a grid of cards for better visualization
        cols_per_row = 2
        for i in range(0, len(filtered_items), cols_per_row):
            row_items = filtered_items[i:i + cols_per_row]
            cols = st.columns(cols_per_row)
            
            for idx, item in enumerate(row_items):
                with cols[idx]:
                    item_date = parse_date(item.get('created_at'))
                    date_str = item_date.strftime('%b %d, %Y') if item_date else 'Unknown date'
                    
                    # Get subject from the most likely fields, default to 'General' only if not found
                    subject = (
                        item.get('subject') or  # First try 'subject'
                        item.get('quiz', {}).get('subject') or  # Then try quiz.subject
                        item.get('quiz_subject') or  # Then try quiz_subject
                        'General'  # Default only if none found
                    )
                    
                    score = item.get('total_score', 0)
                    max_score = item.get('max_score', 10)
                    percentage = item.get('percentage', 0)
                    
                    # Create a card for each quiz
                    with st.container():
                        # Card header with subject and date
                        st.markdown(
                            f"""
                            <div style='
                                background-color: #f8f9fa;
                                border-radius: 10px;
                                padding: 15px;
                                margin-bottom: 15px;
                                border-left: 5px solid #4e73df;
                            '>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <h3 style='margin: 0; color: #2e59d9;'>{subject}</h3>
                                    <span style='color: #6c757d; font-size: 0.9em;'>{date_str}</span>
                                </div>
                                <div style='margin: 10px 0; display: flex; justify-content: space-around;'>
                                    <div style='text-align: center; padding: 0 10px;'>
                                        <div style='font-size: 0.9em; color: #6c757d;'>Score</div>
                                        <div style='font-size: 1.2em; font-weight: bold;'>{score}/{max_score}</div>
                                    </div>
                                    <div style='text-align: center; padding: 0 10px;'>
                                        <div style='font-size: 0.9em; color: #6c757d;'>Percentage</div>
                                        <div style='font-size: 1.2em; font-weight: bold; color: {'#28a745' if percentage >= 70 else '#dc3545'}'>{percentage:.1f}%</div>
                                    </div>
                                </div>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                        
                        # View Feedback section
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            with st.expander("📝 View Feedback", expanded=False):
                                if 'feedback' in item and isinstance(item['feedback'], list) and item['feedback']:
                                    for i, fb in enumerate(item['feedback'], 1):
                                        if not isinstance(fb, dict):
                                            continue
                                            
                                        # Question and user's answer
                                        question = fb.get('question', f'Question {i}')
                                        user_answer = fb.get('user_answer', 'No answer provided')
                                        correct_answer = fb.get('correct_answer', 'No correct answer provided')
                                        is_correct = fb.get('is_correct', False)
                                        
                                        # Display question and answers
                                        st.markdown(f"**{i}. {question}**")
                                        
                                        # Show user's answer with correct/incorrect indicator
                                        status_emoji = "✅" if is_correct else "❌"
                                        st.markdown(f"{status_emoji} **Your Answer:** {user_answer}")
                                        
                                        # Show correct answer if user was wrong
                                        if not is_correct:
                                            st.markdown(f"✓ **Correct Answer:** {correct_answer}")
                                        
                                        # Show explanation if available
                                        if 'explanation' in fb and fb['explanation']:
                                            st.markdown(f"*Explanation:* {fb['explanation']}")
                                        
                                        # Show score for this question if available
                                        if 'marks_awarded' in fb and 'max_marks' in fb:
                                            st.caption(f"Score: {fb['marks_awarded']}/{fb['max_marks']}")
                                        
                                        st.markdown("---")
                                else:
                                    st.info("No feedback available for this quiz.")
                                
                                # Remove suggestions if present in the response
                                if 'suggestions' in item:
                                    del item['suggestions']
                        
                        # Add Retake Quiz button
                        with col2:
                            if st.button("🔄 Retake Quiz", key=f"retake_{item['id']}", use_container_width=True):
                                # Store the quiz ID in session state to be used in the quiz page
                                st.session_state.retake_quiz_id = item['quiz_id']
                                st.session_state.retake_quiz_data = item
                                st.switch_page("pages/3_Take_Quiz.py")
                    
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        if st.checkbox("Show error details"):
            st.exception(e)
            if 'data' in locals():
                st.json(data)  # Show raw data for debugging

if __name__ == "__main__":
    main()