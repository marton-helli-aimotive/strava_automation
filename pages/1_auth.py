import streamlit as st
from src.auth import StravaAuth
from src.strava_client import StravaClient

st.title("🔐 Authentication")

if 'auth' not in st.session_state:
    st.session_state.auth = StravaAuth()
if 'strava' not in st.session_state:
    st.session_state.strava = StravaClient()

auth = st.session_state.auth
strava = st.session_state.strava

# Check if we have a code in the URL (callback)
query_params = st.query_params
if 'code' in query_params:
    code = query_params['code']
    with st.spinner("Exchanging code for token..."):
        try:
            auth.exchange_code(code)
            st.query_params.clear() # Clear code from URL
            st.success("Successfully authenticated!")
            st.rerun()
        except Exception as e:
            st.error(f"Authentication failed: {e}")

if strava.is_authenticated():
    athlete = strava.get_athlete()
    if athlete:
        st.success(f"You are connected as **{athlete.firstname} {athlete.lastname}**")
        st.image(athlete.profile_medium, width=100)
    
    if st.button("Disconnect"):
        import os
        if os.path.exists("data/tokens.json"):
            os.remove("data/tokens.json")
        st.session_state.strava = StravaClient() # Reset client
        st.rerun()
else:
    if not auth.client_id or not auth.client_secret:
        st.warning("⚠️ **API Credentials Missing**: Please enter your Strava API details in the section below to enable connection.")
    else:
        st.info("Please click the button below to authorize the app on Strava.")
        try:
            auth_url = auth.get_auth_url()
            st.markdown(f'''
                <a href="{auth_url}" target="_self">
                    <button style="
                        background-color: #FC4C02;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-weight: bold;
                    ">Connect with Strava</button>
                </a>
            ''', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error generating auth URL: {e}")

st.divider()
with st.expander("⚙️ API Configuration (Advanced)", expanded=not (auth.client_id and auth.client_secret)):
    st.markdown("""
    To use this app, you need specialized API credentials from Strava:
    1. Go to [Strava's API Settings](https://www.strava.com/settings/api).
    2. Create an app (set 'Authorization Callback Domain' to `localhost` or your deployed domain).
    3. Copy the **Client ID** and **Client Secret** below.
    """)
    
    new_id = st.text_input("Strava Client ID", value=auth.client_id or "")
    new_secret = st.text_input("Strava Client Secret", value=auth.client_secret or "", type="password")
    new_uri = st.text_input("Redirect URI", value=auth.redirect_uri or "http://localhost:8501")
    
    if st.button("Save API Configuration"):
        auth.save_config(new_id, new_secret, new_uri)
        st.success("Configuration saved! You can now connect to Strava.")
        st.rerun()
