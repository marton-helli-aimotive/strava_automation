import plotly.express as px
import pandas as pd
import folium
from folium.plugins import HeatMap
import polyline

def create_commute_heatmap(commutes):
    # Center map on first commute if available
    first_point = [0, 0]
    points = []
    
    for c in commutes:
        if isinstance(c, list):
            for r in c:
                if r.map.summary_polyline:
                    decoded = polyline.decode(r.map.summary_polyline)
                    points.extend(decoded)
        else:
            if c.map.summary_polyline:
                decoded = polyline.decode(c.map.summary_polyline)
                points.extend(decoded)
    
    if points:
        first_point = points[0]
        
    m = folium.Map(location=first_point, zoom_start=12)
    HeatMap(points).add_to(m)
    return m

def plot_commute_stats(df):
    if df.empty:
        return None
    
    # Example: Distance over time
    df['Date'] = pd.to_datetime(df['Date'])
    fig = px.bar(df, x='Date', y='Distance (km)', title='Commute Distances', labels={'Distance (km)': 'Distance (km)'})
    fig.update_layout(xaxis_title="Date", yaxis_title="Distance (km)")
    return fig

def plot_day_distribution(df):
    if df.empty:
        return None
    
    df['Date'] = pd.to_datetime(df['Date'])
    df['Day'] = df['Date'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    counts = df['Day'].value_counts().reindex(day_order).fillna(0).reset_index()
    counts.columns = ['Day', 'Count']
    
    fig = px.pie(counts, values='Count', names='Day', title='Commute Distribution by Day')
    return fig
