# Strava Commute Analyzer

A Streamlit app to analyze and manage your Strava commutes.

## Features

- 🔗 **Easy Strava Connection** - Just click "Connect with Strava" to get started
- 📊 **Automatic Analysis** - Detects your home/work locations and identifies commutes
- ⛓️ **Chained Activities** - Groups multi-segment commutes (e.g., coffee stops)
- ✏️ **Mass Edit** - Update commute flags and visibility for multiple activities at once

## Deployment to Streamlit Cloud

### 1. Create Your Strava API Application

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create a new application with these settings:
   - **Application Name**: Your app name (e.g., "My Commute Analyzer")
   - **Category**: Choose any
   - **Website**: Your deployed app URL
   - **Authorization Callback Domain**: `stravaautomation.streamlit.app` (or your custom domain)

3. After creating, note down your **Client ID** and **Client Secret**

### 2. Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Deploy from your GitHub repo

### 3. Configure Secrets

In Streamlit Cloud, go to your app's **Settings** → **Secrets** and add:

```toml
STRAVA_CLIENT_ID = "your_client_id_here"
STRAVA_CLIENT_SECRET = "your_client_secret_here"
STRAVA_REDIRECT_URI = "https://stravaautomation.streamlit.app"
```

That's it! Users can now connect with just their Strava login.

## Local Development

Create a `.env` file (gitignored):

```bash
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REDIRECT_URI=http://localhost:8501
```

Then run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## How OAuth Works

1. User clicks "Connect with Strava"
2. Redirected to Strava's login page
3. User authorizes the app
4. Strava redirects back with an authorization code
5. App exchanges code for access tokens
6. Tokens stored in session (per-user, not shared)

Each user gets their own tokens - your API credentials are never exposed to users.
