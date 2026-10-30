"""Browser-side Open-Meteo weather display for deployments with blocked server egress."""
import json

import streamlit.components.v1 as components


def render_browser_weather(district: str, coordinates: tuple[float, float]) -> None:
    latitude, longitude = coordinates
    district_json = json.dumps(district)
    latitude_json = json.dumps(latitude)
    longitude_json = json.dumps(longitude)
    components.html(
        f"""
        <div id="weather-root" style="font-family:Arial,sans-serif;color:#334155;">
          <div id="weather-status" style="padding:1rem 0;color:#64748b;">Loading live weather…</div>
          <div id="weather-data" style="display:none;">
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:12px;">
              <div class="weather-card"><small>TEMPERATURE</small><strong id="temperature"></strong></div>
              <div class="weather-card"><small>RELATIVE HUMIDITY</small><strong id="humidity"></strong></div>
              <div class="weather-card"><small>PRECIPITATION</small><strong id="precipitation"></strong></div>
              <div class="weather-card"><small>WIND SPEED</small><strong id="wind"></strong></div>
            </div>
            <p id="weather-updated" style="font-size:.82rem;color:#64748b;margin:.75rem 0 0;"></p>
            <div id="weather-forecast" style="display:flex;gap:8px;overflow-x:auto;margin-top:12px;"></div>
          </div>
        </div>
        <style>
          .weather-card {{ box-sizing:border-box;padding:16px;border:1px solid #dbeafe;
            border-radius:14px;background:white;min-height:94px; }}
          .weather-card small {{ display:block;font-weight:700;letter-spacing:.04em;color:#475569; }}
          .weather-card strong {{ display:block;font-size:1.55rem;margin-top:10px;color:#334155; }}
          .forecast-card {{ flex:1 0 105px;padding:10px;border:1px solid #dbeafe;
            border-radius:10px;background:white;font-size:.8rem; }}
        </style>
        <script>
        const district = {district_json};
        const latitude = {latitude_json};
        const longitude = {longitude_json};
        const statusNode = document.getElementById("weather-status");
        const showError = () => {{
          statusNode.textContent = "Live weather is temporarily unavailable. Refresh the page to try again.";
          statusNode.style.color = "#b45309";
        }};
        const params = new URLSearchParams({{
          latitude, longitude,
          current: "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
          daily: "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
          wind_speed_unit: "kmh", forecast_days: "5", timezone: "auto"
        }});
        fetch("https://api.open-meteo.com/v1/forecast?" + params.toString())
          .then(response => {{
            if (!response.ok) throw new Error("Weather request failed: " + response.status);
            return response.json();
          }})
          .then(data => {{
            const current = data.current;
            if (!current || current.temperature_2m == null) throw new Error("Weather values are unavailable");
            document.getElementById("temperature").textContent = current.temperature_2m.toFixed(1) + " °C";
            document.getElementById("humidity").textContent = current.relative_humidity_2m + "%";
            document.getElementById("precipitation").textContent = current.precipitation.toFixed(1) + " mm";
            document.getElementById("wind").textContent = current.wind_speed_10m.toFixed(1) + " km/h";
            const updated = current.time ? new Date(current.time).toLocaleString() : "time not reported";
            document.getElementById("weather-updated").textContent =
              district + " · Open-Meteo · Updated " + updated;
            const daily = data.daily || {{}};
            const forecast = document.getElementById("weather-forecast");
            (daily.time || []).forEach((date, index) => {{
              const card = document.createElement("div");
              card.className = "forecast-card";
              card.textContent = new Date(date + "T12:00:00").toLocaleDateString(undefined, {{
                weekday: "short", month: "short", day: "numeric"
              }}) + " · " + daily.temperature_2m_max[index] + "° / " +
                daily.temperature_2m_min[index] + "° · rain " +
                daily.precipitation_probability_max[index] + "%";
              forecast.appendChild(card);
            }});
            statusNode.style.display = "none";
            document.getElementById("weather-data").style.display = "block";
          }})
          .catch(error => {{
            console.error("Open-Meteo browser request failed for " + district, error);
            showError();
          }});
        </script>
        """,
        height=245,
        scrolling=False,
    )
