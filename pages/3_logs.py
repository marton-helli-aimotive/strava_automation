import streamlit as st
from src.log_manager import LogManager
import pandas as pd
import json

st.title("📂 Analysis Logs")

lm = LogManager()
logs = lm.list_logs()

if not logs:
    st.info("No logs generated yet. Run an analysis first!")
else:
    selected_log = st.selectbox(
        "Select a month to view",
        logs,
        format_func=lambda x: f"{x['year']}/{x['month']:02d}"
    )

    if selected_log:
        log_content = lm.get_log(selected_log['year'], selected_log['month'])
        
        if log_content:
            st.subheader(f"Summary for {selected_log['year']}/{selected_log['month']:02d}")
            col1, col2, col3 = st.columns(3)
            stats = log_content.get('statistics', {})
            col1.metric("Commutes", log_content.get('commutes_count', 0))
            col2.metric("Total Activities", stats.get('total_commute_activities', 0))
            col3.metric("Total Distance", f"{stats.get('total_distance_km', 0):.1f} km")
            
            st.write(f"**Last updated**: {log_content.get('analysis_timestamp')}")
            
            with st.expander("Show Activity IDs"):
                st.write(log_content.get('commute_activity_ids', []))

            with st.expander("Raw Log Data"):
                st.json(log_content)
