import streamlit as st
from src.auth import StravaAuth
from src.strava_client import StravaClient
import os

st.set_page_config(
    page_title="Strava Commute Analyzer",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if 'auth' not in st.session_state:
    st.session_state.auth = StravaAuth()
if 'strava' not in st.session_state:
    st.session_state.strava = StravaClient()

def main():
    st.title("🚲 Strava Commute Analyzer")
    
    st.markdown("""
    Welcome to your commute assistant! This app helps you:
    *   **Analyze** your monthly rides to identify commutes.
    *   **Detect** your Home and Work locations automatically.
    *   **Group** chained activities (e.g., shopping stops) into single commutes.
    *   **Mass Edit** activities to add the "Commute" flair and update visibility.
    """)

    # Handle OAuth Callback globally
    if 'code' in st.query_params:
        code = st.query_params['code']
        with st.spinner("Exchanging code for token..."):
            try:
                st.session_state.auth.exchange_code(code)
                st.query_params.clear()
                st.success("Successfully authenticated!")
                st.rerun()
            except Exception as e:
                st.error(f"Authentication failed: {e}")

    if not st.session_state.strava.is_authenticated():
        st.warning("Please connect to Strava first in the **Authentication** page.")
        if st.button("Go to Auth Page"):
            st.switch_page("pages/1_auth.py")
    else:
        athlete = st.session_state.strava.get_athlete()
        if athlete:
            st.success(f"Connected as **{athlete.firstname} {athlete.lastname}**")
            
            st.markdown("### Quick Navigation")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🚀 Start New Analysis", width='stretch'):
                    st.switch_page("pages/2_analyze.py")
            with col2:
                if st.button("📂 Browse Saved Logs", width='stretch'):
                    st.switch_page("pages/3_logs.py")
            with col3:
                if st.button("⚙️ Mass Edit Activities", width='stretch'):
                    st.switch_page("pages/4_edit.py")
            
            # Show quick summary of logs
            from src.log_manager import LogManager
            lm = LogManager()
            logs = lm.list_logs()
            
            st.subheader("Your Analysis History")
            if logs:
                for log in logs[:5]:  # Show last 5
                    st.write(f"- {log['year']}/{log['month']:02d}")
            else:
                st.info("No logs found. Start by running an analysis!")

if __name__ == "__main__":
    main()
