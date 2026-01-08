import streamlit as st
import datetime
import pandas as pd
from src.strava_client import StravaClient
from src.location_analyzer import LocationAnalyzer
from src.commute_detector import CommuteDetector
from src.log_manager import LogManager
from src.visualizations import create_commute_heatmap, plot_commute_stats, plot_day_distribution
import folium
from streamlit_folium import st_folium

st.title("🔍 Activity Analysis")

if 'strava' not in st.session_state or not st.session_state.strava.is_authenticated():
    st.warning("Please authenticate first!")
    st.stop()

strava = st.session_state.strava
analyzer = LocationAnalyzer()
lm = LogManager()

def safe_latlng(ll):
    if ll is None: return None
    try:
        return [float(ll[0]), float(ll[1])]
    except (TypeError, KeyError, IndexError, AttributeError):
        try:
            return [float(getattr(ll, 'lat')), float(getattr(ll, 'lon', getattr(ll, 'lng')))]
        except:
            return None

# Sidebar for controls
with st.sidebar:
    st.header("Settings")
    today = datetime.date.today()
    default_year = today.year
    default_month = today.month
    
    year = st.selectbox("Year", range(2020, default_year + 1), index=(default_year - 2020))
    month = st.selectbox("Month", range(1, 13), index=(default_month - 1))
    
    radius = st.slider("Detection Radius (meters)", 50, 1000, 300)
    max_gap = st.slider("Max Stop Duration (hours)", 1, 12, 6)

if st.button("Fetch and Analyze Activities"):
    with st.spinner(f"Fetching activities for {year}-{month:02d}..."):
        try:
            rides = strava.fetch_rides(year, month)
            st.session_state.current_rides = rides
            
            if not rides:
                st.warning("No rides found for this month.")
            else:
                home, work = analyzer.estimate_locations(rides)
                st.session_state.home = home
                st.session_state.work = work
                st.session_state.analysis_done = True
        except Exception as e:
            st.error(f"Failed to fetch activities: {e}")
            if "Unauthorized" in str(e):
                st.info("This is likely due to missing permissions. Please go to the **Authentication** page, click **Disconnect**, and then **Connect with Strava** again, making sure to check all permission boxes.")

if 'analysis_done' in st.session_state and st.session_state.analysis_done:
    rides = st.session_state.current_rides
    home = st.session_state.home
    work = st.session_state.work
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Estimated Locations")
        if home:
            st.write(f"🏠 **Home**: {home[0]:.5f}, {home[1]:.5f}")
        if work:
            st.write(f"💼 **Work**: {work[0]:.5f}, {work[1]:.5f}")
        else:
            st.info("Could not reliably estimate a second cluster for Work. You can select it manually.")

    # Map for location selection/verification
    st.subheader("Map Overview")
    m = folium.Map(location=home if home else [0,0], zoom_start=13)
    if home:
        folium.Marker(home, tooltip="Home", icon=folium.Icon(color='blue', icon='home')).add_to(m)
    if work:
        folium.Marker(work, tooltip="Work", icon=folium.Icon(color='red', icon='briefcase')).add_to(m)
    
    # Optional: Plot activity starts/ends
    for r in rides:
        start = safe_latlng(r.start_latlng)
        if start:
            folium.CircleMarker(start, radius=3, color='green', fill=True).add_to(m)
        end = safe_latlng(r.end_latlng)
        if end:
            folium.CircleMarker(end, radius=3, color='orange', fill=True).add_to(m)

    st_folium(m, width=700, height=400)

    # Commute Detection
    if home and work:
        detector = CommuteDetector(home, work, radius_meters=radius, max_time_gap_hours=max_gap)
        commutes = detector.detect_commutes(rides)
        
        st.subheader("Commute Statistics")
        st.metric("Total Rides", len(rides))
        
        # Flatten combined rides for stats
        all_commute_activities = []
        for c in commutes:
            if isinstance(c, list):
                all_commute_activities.extend(c)
            else:
                all_commute_activities.append(c)
        
        st.metric("Commute Activities identified", len(all_commute_activities))
        
        # Create a table of commutes
        commute_data = []
        for c in commutes:
            if isinstance(c, list):
                ids = [r.id for r in c]
                names = ", ".join([r.name for r in c])
                dist = sum([float(r.distance) for r in c]) / 1000.0
                date = c[0].start_date.strftime("%Y-%m-%d %H:%M")
                type_str = "Chained"
            else:
                ids = [c.id]
                names = c.name
                dist = float(c.distance) / 1000.0
                date = c.start_date.strftime("%Y-%m-%d %H:%M")
                type_str = "Simple"
            
            commute_data.append({
                "Date": date,
                "Type": type_str,
                "Distance (km)": f"{dist:.2f}",
                "Name": names,
                "IDs": ids
            })
        
        df = pd.DataFrame(commute_data)
        st.dataframe(df)

        st.subheader("Visualizations")
        tab1, tab2 = st.tabs(["Heatmap", "Statistics"])
        
        with tab1:
            st.markdown("### Geo Heatmap of Commutes")
            hmap = create_commute_heatmap(commutes)
            st_folium(hmap, width=700, height=500, key="heatmap")
            
        with tab2:
            st.markdown("### Commute Trends")
            df['Distance (km)'] = df['Distance (km)'].astype(float)
            fig1 = plot_commute_stats(df)
            if fig1: st.plotly_chart(fig1, width='stretch')
            
            fig2 = plot_day_distribution(df)
            if fig2: st.plotly_chart(fig2, width='stretch')

        if st.button("Save results to Log"):
            log_data = {
                "analysis_timestamp": datetime.datetime.now().isoformat(),
                "home": home,
                "work": work,
                "commutes_count": len(commutes),
                "commute_activity_ids": [id for d in commute_data for id in d['IDs']],
                "statistics": {
                    "total_rides": len(rides),
                    "total_commute_activities": len(all_commute_activities),
                    "total_distance_km": sum([float(d['Distance (km)']) for d in commute_data])
                }
            }
            lm.upsert_log(year, month, log_data)
            st.success(f"Log updated for {year}-{month:02d}!")
    else:
        st.warning("Need both Home and Work locations to detect commutes.")
