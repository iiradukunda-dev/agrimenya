import streamlit as st
from utils.theme import load_theme
import plotly.express as px
from utils import api_client
from components.icons import render_icon_title

st.set_page_config(page_title="Planification", page_icon="assets/calendar.svg", layout="wide")
load_theme()

render_icon_title("assets/calendar.svg", "Planification", "Roadmaps and execution timelines for agricultural interventions.")

# Sidebar Filters
st.sidebar.header("Plan Context")
selected_zone = st.sidebar.selectbox("Select Zone", ["All Regions", "Northern Province", "Eastern Province", "Southern Province", "Western Province"])
selected_season = st.sidebar.selectbox("Season", ["Season A", "Season B", "Season C"])

st.subheader(f"Execution Roadmap: {selected_zone} ({selected_season})")

df_roadmap = api_client.get_roadmap()

# Gantt-style chart using Plotly timeline
fig = px.timeline(
    df_roadmap, 
    x_start="Start", 
    x_end="End", 
    y="Task", 
    color="Phase",
    color_discrete_map={
        "Preparation": "#C4924A",
        "Execution": "#2D6A4F",
        "Monitoring": "#52B788"
    },
    title="Intervention Schedule"
)
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Detailed Steps")
for idx, row in df_roadmap.iterrows():
    st.checkbox(f"**{row['Phase']}**: {row['Task']} (Due: {row['End']})", key=f"task_{idx}")

st.button("Save & Share Plan", type="primary")
