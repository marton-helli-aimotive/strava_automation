import streamlit as st
from src.auth import StravaAuth
from src.strava_client import StravaClient

st.title("🔐 Connect to Strava")

# Get shared client instance
if 'strava' not in st.session_state:
    st.session_state.strava = StravaClient()

strava = st.session_state.strava
auth = strava.auth

# Handle OAuth callback (code in URL)
if 'code' in st.query_params:
    code = st.query_params['code']
    with st.spinner("Connecting to Strava..."):
        try:
            auth.exchange_code(code)
            st.query_params.clear()
            st.success("Successfully connected!")
            st.rerun()
        except Exception as e:
            st.error(f"Connection failed: {e}")

# Main UI
if strava.is_authenticated():
    athlete = strava.get_athlete()
    if athlete:
        st.success(f"✅ Connected as **{athlete.firstname} {athlete.lastname}**")
        if athlete.profile_medium:
            st.image(athlete.profile_medium, width=100)
    
    st.divider()
    
    if st.button("🔌 Disconnect from Strava", type="secondary"):
        strava.disconnect()
        st.rerun()
        
    st.info("You're all set! Head to the **Analyze** page to start analyzing your commutes.")
    
else:
    # Check if app is properly configured
    if not auth.is_configured():
        st.error("""
        ⚠️ **App Not Configured**
        
        The app administrator needs to set up Strava API credentials.
        
        If you are the administrator, please set `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET` 
        in your Streamlit secrets or environment variables.
        """)
    else:
        st.markdown("""
        Click the button below to securely connect your Strava account.
        
        You'll be redirected to Strava to authorize this app, then sent back here automatically.
        """)
        
        try:
            auth_url = auth.get_auth_url()
            st.markdown(f'''
                <a href="{auth_url}" target="_self">
                    <button style="
                        background-color: #FC4C02;
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: bold;
                        font-size: 16px;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    ">
                        🔗 Connect with Strava
                    </button>
                </a>
            ''', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")
        
        st.divider()
        
        with st.expander("🔒 Privacy & Permissions"):
            st.markdown("""
            This app requests the following permissions:
            - **Read your profile** - To display your name
            - **Read your activities** - To analyze your rides
            - **Write activities** - To mark commutes and update visibility
            
            Your data stays between you and Strava. We don't store your activities on any server.
            """)
