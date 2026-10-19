"""Creative, animated agro-intelligence hero for the agrimenya landing page."""
import streamlit as st


def render_home_hero() -> None:
    """Render a modern, animated hero section with glowing gradient mesh and live indicators."""
    st.html("""
    <style>
      .ag-hero-container {
        position: relative;
        overflow: hidden;
        display: grid;
        grid-template-columns: 1.35fr 0.65fr;
        gap: 2.2rem;
        align-items: center;
        min-height: 290px;
        padding: 2.8rem 3.2rem;
        margin: 0.2rem 0 1.8rem;
        color: #ffffff;
        background: linear-gradient(135deg, #07261a 0%, #0e3b28 40%, #175438 75%, #0b3020 100%);
        border-radius: 22px;
        box-shadow: 0 20px 50px rgba(7, 38, 26, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.15);
      }

      /* Animated organic light orbs in the background */
      .ag-hero-container::before {
        content: "";
        position: absolute;
        top: -60px;
        right: 15%;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.28) 0%, rgba(16, 185, 129, 0) 70%);
        border-radius: 50%;
        filter: blur(35px);
        pointer-events: none;
        animation: ag-hero-orb-float 7s ease-in-out infinite alternate;
      }
      .ag-hero-container::after {
        content: "";
        position: absolute;
        bottom: -80px;
        left: 20%;
        width: 360px;
        height: 360px;
        background: radial-gradient(circle, rgba(245, 158, 11, 0.16) 0%, rgba(245, 158, 11, 0) 70%);
        border-radius: 50%;
        filter: blur(40px);
        pointer-events: none;
        animation: ag-hero-orb-float-2 9s ease-in-out infinite alternate;
      }

      @keyframes ag-hero-orb-float {
        0% { transform: translate(0, 0) scale(1); }
        100% { transform: translate(-30px, 25px) scale(1.15); }
      }
      @keyframes ag-hero-orb-float-2 {
        0% { transform: translate(0, 0) scale(1); }
        100% { transform: translate(35px, -20px) scale(1.12); }
      }

      .ag-hero-content {
        position: relative;
        z-index: 2;
      }

      /* Live Beacon Badge */
      .ag-hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.22);
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #d1fae5;
        margin-bottom: 0.9rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      }
      .ag-hero-beacon {
        width: 8px;
        height: 8px;
        background-color: #34d399;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.7);
        animation: ag-beacon-radar 2s infinite;
      }
      @keyframes ag-beacon-radar {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 7px rgba(52, 211, 153, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
      }

      /* Headline - explicitly white with glowing highlight */
      .ag-hero-title {
        margin: 0 0 0.85rem !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: clamp(2.1rem, 3.8vw, 3.35rem) !important;
        line-height: 1.08 !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.25) !important;
      }
      .ag-hero-glow-text {
        background: linear-gradient(135deg, #a7f3d0 0%, #34d399 50%, #fef08a 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        display: inline-block !important;
      }

      .ag-hero-copy {
        max-width: 660px;
        margin: 0 0 1.6rem;
        color: #e0eee4;
        font-size: 1.02rem;
        line-height: 1.65;
        font-weight: 450;
      }

      /* Stats Ticker Strip */
      .ag-hero-stats {
        display: flex;
        flex-wrap: wrap;
        gap: 1.4rem;
        align-items: center;
        padding-top: 1.1rem;
        border-top: 1px solid rgba(255, 255, 255, 0.14);
      }
      .ag-hero-stat-item {
        display: flex;
        flex-direction: column;
      }
      .ag-hero-stat-val {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.15rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.02em;
      }
      .ag-hero-stat-lbl {
        font-size: 0.74rem;
        font-weight: 600;
        color: #a7f3d0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      /* Right Column: Liquid Glass Horizon Card */
      .ag-hero-glass-card {
        position: relative;
        z-index: 2;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0.06) 100%);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.28);
        border-radius: 18px;
        padding: 1.5rem 1.6rem;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.15), inset 0 1px 1px rgba(255, 255, 255, 0.4);
        transition: transform 0.3s ease, border-color 0.3s ease;
      }
      .ag-hero-glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(255, 255, 255, 0.45);
      }

      .ag-hero-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.8rem;
      }
      .ag-hero-card-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.94rem;
        font-weight: 750;
        color: #ffffff;
        letter-spacing: -0.01em;
      }
      .ag-hero-card-tag {
        font-size: 0.72rem;
        font-weight: 700;
        background: rgba(52, 211, 153, 0.22);
        color: #6ee7b7;
        border: 1px solid rgba(52, 211, 153, 0.4);
        padding: 2px 8px;
        border-radius: 9999px;
        text-transform: uppercase;
      }

      .ag-hero-card-desc {
        color: #d1e7d8;
        font-size: 0.86rem;
        line-height: 1.55;
        margin-bottom: 1rem;
      }

      .ag-hero-card-row {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }
      .ag-hero-pill-info {
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(0, 0, 0, 0.16);
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 0.78rem;
        color: #ecfdf5;
      }

      @media (max-width: 900px) {
        .ag-hero-container {
          grid-template-columns: 1fr;
          padding: 2rem 1.6rem;
          gap: 1.8rem;
        }
      }
    </style>

    <section class="ag-hero-container" aria-label="agrimenya overview">
      <div class="ag-hero-content">
        <div class="ag-hero-badge">
          <span class="ag-hero-beacon"></span>
          Rwanda Agro-Climate Decision Engine
        </div>
        <h1 class="ag-hero-title">
          Make the next<br/>
          <span class="ag-hero-glow-text">field decision</span> clearer.
        </h1>
        <p class="ag-hero-copy">
          Explore spatial zone intelligence, evaluate seasonal crop recommendations, and turn data-grounded insights into synchronized field plans.
        </p>

        <div class="ag-hero-stats">
          <div class="ag-hero-stat-item">
            <span class="ag-hero-stat-val">30 Districts</span>
            <span class="ag-hero-stat-lbl">Spatial Coverage</span>
          </div>
          <div class="ag-hero-stat-item">
            <span class="ag-hero-stat-val">10+ Key Crops</span>
            <span class="ag-hero-stat-lbl">SAS Baselines</span>
          </div>
          <div class="ag-hero-stat-item">
            <span class="ag-hero-stat-val">Real-time Weather</span>
            <span class="ag-hero-stat-lbl">Satellite Indicators</span>
          </div>
          <div class="ag-hero-stat-item">
            <span class="ag-hero-stat-val">CAT (UTC+2)</span>
            <span class="ag-hero-stat-lbl">System Timezone</span>
          </div>
        </div>
      </div>

      <aside class="ag-hero-glass-card">
        <div class="ag-hero-card-header">
          <span class="ag-hero-card-title">Seasonal Horizon</span>
          <span class="ag-hero-card-tag">2026 Season A</span>
        </div>
        <p class="ag-hero-card-desc">
          Current agricultural campaign is active. Review localized soil moisture and yield projections before dispatching field advisories.
        </p>
        <div class="ag-hero-card-row">
          <div class="ag-hero-pill-info">
            <span>📍</span>
            <span>Priority Zones: Gasabo, Bugesera, Musanze</span>
          </div>
          <div class="ag-hero-pill-info">
            <span>🌦️</span>
            <span>Optimal planting window actively tracked</span>
          </div>
          <div class="ag-hero-pill-info">
            <span>💡</span>
            <span>AI Assistant available via corner bulb</span>
          </div>
        </div>
      </aside>
    </section>
    """)
