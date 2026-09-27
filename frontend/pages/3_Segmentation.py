import streamlit as st
from frontend.utils.theme import load_theme
from frontend.utils import api_client
from frontend.components.maps import render_priority_map
from frontend.components.charts import render_yield_chart
from frontend.utils.mock_data import CROPS, SEASONS
from frontend.components.icons import render_icon_title

st.set_page_config(page_title="Segmentation", page_icon="frontend/assets/map.svg", layout="wide")
load_theme()

render_icon_title("frontend/assets/map.svg", "Segmentation & Zoning", "Interactive mapping for prioritizing agricultural zones across Rwanda.")

# Fetch data
df = api_client.get_priority_data()

# Filters
with st.sidebar:
    st.header("Filters")
    selected_season = st.selectbox("Season", SEASONS)
    selected_crops = st.multiselect("Crops", CROPS, default=CROPS[:2])
    priority_level = st.multiselect("Priority Level", ["Low", "Medium", "High"], default=["High", "Medium"])

if df.empty:
    st.info("No data available. Please check the backend connection.")
else:
    # Filter dataframe
    # Use `.get` or ensure columns exist to avoid KeyErrors on malformed data
    if "Crop" in df.columns and "Priority" in df.columns:
        filtered_df = df[df["Crop"].isin(selected_crops) & df["Priority"].isin(priority_level)]
    else:
        filtered_df = df
        
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Priority Zones Map")
        render_priority_map(filtered_df)
    
    with col2:
        st.subheader("Yield Analysis")
        render_yield_chart(filtered_df)
        
        st.divider()
        st.subheader("Zoning Summary")
        if "Yield_MT_ha" in filtered_df.columns:
            st.dataframe(
                filtered_df[["District", "Crop", "Priority", "Yield_MT_ha"]].sort_values("Yield_MT_ha", ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
