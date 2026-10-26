import pandas as pd
import requests
import streamlit as st
from components.charts import render_yield_chart
from components.errors import error_boundary, render_error_page
from components.icons import render_icon_title
from components.maps import render_priority_map
from utils import api_client
from utils.i18n import t


@error_boundary("Segmentation")
def render_segment():
    try:
        render_icon_title("assets/map.svg", t("seg.header"), t("seg.subtitle"))

        # Fetch data
        df = api_client.get_priority_data()

        # Keep filters visible in the page: the shared navbar hides Streamlit's sidebar.
        with st.container(border=True):
            st.subheader(t("seg.filters"))
            season_values = (
                sorted(str(value) for value in df["season"].dropna().unique())
                if "season" in df.columns
                else []
            )
            crop_values = (
                sorted(str(value) for value in df["Crop"].dropna().unique())
                if "Crop" in df.columns
                else []
            )
            priority_values = [
                value for value in ("High", "Medium", "Low")
                if "Priority" in df.columns and value in set(df["Priority"].dropna())
            ]
            if "Priority" in df.columns and "Unassessed" in set(df["Priority"].dropna()):
                priority_values.append("Unassessed")
            all_seasons_label = t("common.all_seasons", "All seasons")
            filter_cols = st.columns(2)
            with filter_cols[0]:
                selected_season = st.selectbox(t("seg.season", "Season"), [all_seasons_label] + season_values)
                priority_level = st.multiselect(t("seg.priority_level"), priority_values, default=priority_values)
            with filter_cols[1]:
                selected_crops = st.multiselect(t("seg.crops"), crop_values, default=crop_values)

        if df.empty:
            st.info(t("seg.empty"))
        else:
            # Filter dataframe
            filtered_df = df.copy()
            if selected_season != all_seasons_label and "season" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["season"] == selected_season]
            if "Crop" in filtered_df.columns:
                selected_crop_keys = {crop.casefold() for crop in selected_crops}
                filtered_df = filtered_df[filtered_df["Crop"].astype(str).str.casefold().isin(selected_crop_keys)]
            if "Priority" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["Priority"].isin(priority_level)]

            if filtered_df.empty:
                st.info("No map data matches these filters.")
                return
                
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.subheader(t("seg.map_title"))
                clicked_zone_id = render_priority_map(filtered_df, key="segmentation_priority_map")
                if clicked_zone_id:
                    st.session_state["selected_zone_id"] = clicked_zone_id
                    st.session_state["segment_zone_select"] = clicked_zone_id
            
            with col2:
                st.subheader(t("seg.yield_title"))
                render_yield_chart(filtered_df)
                
                st.divider()
                st.subheader(t("seg.summary_title"))
                if "Production_MT" in filtered_df.columns:
                    cols_to_show = [c for c in ["District", "Crop", "Priority", "Production_MT"] if c in filtered_df.columns]
                    display_df = filtered_df[cols_to_show].sort_values("Production_MT", ascending=False).rename(
                        columns={
                            "District": t("seg.col_district"),
                            "Crop": t("seg.col_crop"),
                            "Priority": t("seg.col_priority"),
                            "Production_MT": t("seg.col_yield"),
                        }
                    )
                    st.dataframe(
                        display_df,
                        width="stretch",
                        hide_index=True
                    )
                else:
                    st.dataframe(filtered_df, width="stretch", hide_index=True)

            zone_rows = (
                filtered_df[filtered_df["id"].notna()].to_dict("records")
                if "id" in filtered_df.columns else []
            )
            zone_ids = [str(row["id"]) for row in zone_rows]
            if zone_ids:
                current_zone_id = str(st.session_state.get("selected_zone_id", zone_ids[0]))
                if current_zone_id not in zone_ids:
                    current_zone_id = zone_ids[0]
                if st.session_state.get("segment_zone_select") not in zone_ids:
                    st.session_state["segment_zone_select"] = current_zone_id

                zone_by_id = {str(row["id"]): row for row in zone_rows}
                selected_zone_id = st.selectbox(
                    "Selected zone",
                    options=zone_ids,
                    key="segment_zone_select",
                    format_func=lambda zone_id: " | ".join(filter(None, [
                        str(zone_by_id[zone_id].get("District", "Unknown")),
                        str(zone_by_id[zone_id].get("Crop", "Unspecified")),
                        f"{zone_by_id[zone_id].get('Priority', 'Unassessed')} priority",
                    ])),
                )
                st.session_state["selected_zone_id"] = selected_zone_id
                selected_row = zone_by_id[selected_zone_id]
                zone_detail = api_client.get_zone_detail(selected_zone_id) or {}

                st.subheader("Selected zone details")
                detail_cols = st.columns(5)
                detail_cols[0].metric("District", zone_detail.get("district") or selected_row.get("District", "Unknown"))
                detail_cols[1].metric("Crop", zone_detail.get("crop_type") or selected_row.get("Crop", "Unspecified"))
                season = zone_detail.get("season")
                if season is None or pd.isna(season):
                    season = selected_row.get("season")
                detail_cols[2].metric("Season", season if season is not None and pd.notna(season) else "Not set")
                area = zone_detail.get("area_cultivated")
                area_value = f"{float(area):,.2f} ha" if area is not None and pd.notna(area) else "Not recorded"
                detail_cols[3].metric("Cultivated area", area_value)
                production = selected_row.get("Production_MT")
                production_value = f"{production:,.2f} MT" if pd.notna(production) else "No prediction yet"
                detail_cols[4].metric("Latest predicted production", production_value)
    except requests.exceptions.RequestException as e:
        import logging
        logging.getLogger(__name__).error(f"Network error in segment.py: {e}")
        render_error_page("network", str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Unexpected error in segment.py: {e}", exc_info=True)
        render_error_page("system", str(e))
