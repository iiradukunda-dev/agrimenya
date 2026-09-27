import plotly.express as px
import streamlit as st

def render_yield_chart(df):
    if df.empty:
        st.info("No data available for chart.")
        return
        
    fig = px.bar(
        df.groupby(["District", "Priority"])["Yield_MT_ha"].mean().reset_index(),
        x="District", 
        y="Yield_MT_ha",
        color="Priority",
        color_discrete_map={"High": "#DC2626", "Medium": "#D97706", "Low": "#2D6A4F"},
        title="Average Yield by District and Priority",
        barmode="group"
    )
    fig.update_layout(xaxis_title="District", yaxis_title="Yield (MT/ha)")
    st.plotly_chart(fig, use_container_width=True)
