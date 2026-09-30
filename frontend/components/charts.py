import plotly.express as px
import streamlit as st
from utils.i18n import t

def render_yield_chart(df):
    if df.empty:
        st.info(t("seg.empty"))
        return
        
    fig = px.bar(
        df.groupby(["District", "Priority"])["Yield_MT_ha"].mean().reset_index(),
        x="District", 
        y="Yield_MT_ha",
        color="Priority",
        color_discrete_map={"High": "#DC2626", "Medium": "#D97706", "Low": "#2D6A4F"},
        title=t("seg.chart_title"),
        barmode="group"
    )
    fig.update_layout(xaxis_title=t("seg.axis_district"), yaxis_title=t("seg.axis_yield"))
    st.plotly_chart(fig, use_container_width=True)
