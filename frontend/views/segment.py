import streamlit as st
import requests
from utils.i18n import t
from utils import api_client
from components.maps import render_priority_map
from components.charts import render_yield_chart
from utils.mock_data import CROPS, SEASONS
from components.icons import render_icon_title
from components.errors import render_error_page

def render_segment():
    try:
        render_icon_title("assets/map.svg", t("seg.header"), t("seg.subtitle"))

        # Fetch data
        df = api_client.get_priority_data()

        # Filters
        with st.sidebar:
            st.header(t("seg.filters"))
            selected_season = st.selectbox(t("seg.season"), SEASONS)
            selected_crops = st.multiselect(t("seg.crops"), CROPS, default=CROPS[:2])
            priority_level = st.multiselect(t("seg.priority_level"), ["Low", "Medium", "High"], default=["High", "Medium"])

        if df.empty:
            st.info(t("seg.empty"))
        else:
            # Filter dataframe
            if "Crop" in df.columns and "Priority" in df.columns:
                filtered_df = df[df["Crop"].isin(selected_crops) & df["Priority"].isin(priority_level)]
            else:
                filtered_df = df
                
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.subheader(t("seg.map_title"))
                render_priority_map(filtered_df)
            
            with col2:
                st.subheader(t("seg.yield_title"))
                render_yield_chart(filtered_df)
                
                st.divider()
                st.subheader(t("seg.summary_title"))
                if "Yield_MT_ha" in filtered_df.columns:
                    display_df = filtered_df[["District", "Crop", "Priority", "Yield_MT_ha"]].sort_values("Yield_MT_ha", ascending=False).copy()
                    display_df.columns = [t("seg.col_district"), t("seg.col_crop"), t("seg.col_priority"), t("seg.col_yield")]
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    except requests.exceptions.RequestException as e:
        render_error_page("network", str(e))
    except Exception as e:
        render_error_page("system", str(e))
