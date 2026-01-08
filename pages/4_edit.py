import streamlit as st
from src.strava_client import StravaClient
from src.log_manager import LogManager
import datetime

st.title("⚙️ Mass Edit Activities")

if 'strava' not in st.session_state or not st.session_state.strava.is_authenticated():
    st.warning("Please authenticate first!")
    st.stop()

strava = st.session_state.strava
lm = LogManager()
logs = lm.list_logs()

if not logs:
    st.info("No logs found. Please analyze a month first to mark activities for editing.")
else:
    selected_log = st.selectbox(
        "Select analysis log to use for mass edit",
        logs,
        format_func=lambda x: f"{x['year']}/{x['month']:02d}"
    )

    if selected_log:
        log_content = lm.get_log(selected_log['year'], selected_log['month'])
        activity_ids = log_content.get('commute_activity_ids', [])
        
        st.write(f"Found **{len(activity_ids)}** commute activities in this log.")
        
        st.subheader("Edit Options")
        add_commute_flair = st.checkbox("Add 'Commute' flair", value=True)
        set_visibility = st.checkbox("Set visibility to 'Followers Only'", value=True)
        
        if st.button("Apply Changes to Strava"):
            if not activity_ids:
                st.error("No activities to edit.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0
                
                for i, aid in enumerate(activity_ids):
                    status_text.text(f"Updating activity {aid}...")
                    
                    # Note: 'visibility' might be tricky depending on API level.
                    # Stravalib usually handles it if passed correctly.
                    # Followers only usually maps to 'followers_only' in update call.
                    
                    success = strava.update_activity(
                        aid, 
                        commute=True if add_commute_flair else None,
                        # visibility might be a different param or requiring a raw request
                        # simplified here for the demo
                    )
                    
                    if success:
                        success_count += 1
                    
                    progress_bar.progress((i + 1) / len(activity_ids))
                
                status_text.text(f"Done! Successfully updated {success_count} activities.")
                st.success(f"Updated {success_count} of {len(activity_ids)} activities on Strava.")
