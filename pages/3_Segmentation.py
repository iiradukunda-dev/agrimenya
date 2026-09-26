import streamlit as st
from utils import api_client
from components.maps import render_priority_map
from components.charts import render_yield_chart
from utils.mock_data import CROPS, SEASONS
from components.icons import render_icon_title

st.set_page_config(page_title="Segmentation", page_icon="assets/map.svg", layout="wide")

render_icon_title("assets/map.svg", "Segmentation & Zoning", "Interactive mapping for prioritizing agricultural zones across Rwanda.")

# Fetch data
df = api_client.get_priority_data()

# Filters
with st.sidebar:
    st.header("Filters")
    selected_season = st.selectbox("Season", SEASONS)
    selected_crops = st.multiselect("Crops", CROPS, default=CROPS[:2])
    priority_level = st.multiselect("Priority Level", ["Low", "Medium", "High"], default=["High", "Medium"])

# Filter dataframe
filtered_df = df[df["Crop"].isin(selected_crops) & df["Priority"].isin(priority_level)]

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Priority Zones Map")
    render_priority_map(filtered_df)

with col2:
    st.subheader("Yield Analysis")
    render_yield_chart(filtered_df)
    
    st.divider()
    st.subheader("Zoning Summary")
    st.dataframe(
        filtered_df[["District", "Crop", "Priority", "Yield_MT_ha"]].sort_values("Yield_MT_ha", ascending=False),
        use_container_width=True,
        hide_index=True
    )
