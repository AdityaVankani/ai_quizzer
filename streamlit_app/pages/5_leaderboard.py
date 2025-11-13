import streamlit as st
from utils.api_client import get_leaderboard
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")

# Reuse subject dictionary for consistent emojis
SUBJECTS = {
    "Mathematics": "🔢", "Science": "🔬", "English": "📚", "History": "🏛️",
    "Geography": "🌍", "Computer Science": "💻", "Physics": "⚛️", "Chemistry": "🧪",
    "Biology": "🧬", "Economics": "💹", "Art": "🎨", "Music": "🎵"
}

def main():
    st.title("🏆 Class Leaderboard")
    st.markdown("See who is topping the charts in various subjects!")

    if 'token' not in st.session_state or not st.session_state.token:
        st.warning("Please log in to view the leaderboard.")
        return

    # --- Filters Section ---
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            grade_filter = st.number_input("Filter by Grade", min_value=1, max_value=12, value=5, step=1)
        
        with col2:
            # Add "All Subjects" option
            subject_options = ["All Subjects"] + list(SUBJECTS.keys())
            subject_display = st.selectbox("Filter by Subject", subject_options)
            
            # Handle API logic for "All Subjects"
            subject_filter = None if subject_display == "All Subjects" else subject_display

        with col3:
            st.write("") # Spacer
            st.write("") # Spacer
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

    st.markdown("---")

    # --- Fetch Data ---
    with st.spinner("Calculating rankings..."):
        data = get_leaderboard(st.session_state.token, grade=grade_filter, subject=subject_filter)
        entries = data.get("entries", [])

    if not entries:
        st.info("No quiz records found for this selection. Be the first to take a quiz!")
        return

    # --- Display Metrics ---
    top_score = entries[0]
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("🥇 Top Scorer", f"{top_score['user_id']}")
    with m2:
        st.metric("📚 Subject", f"{top_score['subject']}")
    with m3:
        st.metric("⚡ High Score", f"{top_score['percentage']}%")

    # --- Display Table ---
    # Convert to DataFrame for a nicer table display
    df_data = []
    for entry in entries:
        # Format Date
        dt = datetime.fromisoformat(entry['date'])
        date_str = dt.strftime("%b %d, %Y")
        
        # Add Medal Emojis for top 3
        rank_display = str(entry['rank'])
        if entry['rank'] == 1: rank_display = "🥇"
        elif entry['rank'] == 2: rank_display = "🥈"
        elif entry['rank'] == 3: rank_display = "🥉"

        df_data.append({
            "Rank": rank_display,
            "Student": entry['user_id'],
            "Subject": f"{SUBJECTS.get(entry['subject'], '')} {entry['subject']}",
            "Score": f"{entry['score']} / {entry['max_score']}",
            "Percentage": f"{entry['percentage']}%",
            "Date": date_str
        })

    df = pd.DataFrame(df_data)
    
    # CSS to style the table slightly
    st.markdown("""
    <style>
        [data-testid="stDataFrame"] { font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.TextColumn("Rank", width="small"),
            "Percentage": st.column_config.ProgressColumn(
                "Performance",
                format="%s",
                min_value=0,
                max_value=100,
            ),
        }
    )

if __name__ == "__main__":
    main()