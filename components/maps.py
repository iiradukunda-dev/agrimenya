import folium
from streamlit_folium import st_folium
import streamlit as st

def render_priority_map(df):
    """Render a Folium map with priority zones."""
    # Center map on Rwanda
    m = folium.Map(location=[-1.9403, 29.8739], zoom_start=8, tiles="CartoDB positron")
    
    color_map = {"High": "red", "Medium": "orange", "Low": "green"}
    
    if not df.empty:
        for idx, row in df.iterrows():
            folium.CircleMarker(
                location=[row["Lat"], row["Lon"]],
                radius=8,
                popup=f"<b>{row['District']}</b><br>Crop: {row['Crop']}<br>Yield: {row['Yield_MT_ha']} MT/ha",
                color=color_map.get(row["Priority"], "gray"),
                fill=True,
                fillColor=color_map.get(row["Priority"], "gray"),
                fillOpacity=0.7
            ).add_to(m)
            
    return st_folium(m, width=700, height=500, returned_objects=[])
