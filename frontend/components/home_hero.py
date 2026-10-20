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
        background: linear-gradient(135deg, #021824 0%, #042633 30%, #063836 65%, #08422e 100%);
        border-radius: 22px;
        border: 1px solid rgba(56, 189, 248, 0.22);
        box-shadow: 0 20px 50px rgba(2, 24, 36, 0.28), 0 0 35px rgba(56, 189, 248, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.25);
      }

      /* Animated cyan bulb & tree emerald light orbs in the background */
      .ag-hero-container::before {
        content: "";
        position: absolute;
        top: -60px;
        right: 15%;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(56, 189, 248, 0.32) 0%, rgba(14, 165, 233, 0) 70%);
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
        background: radial-gradient(circle, rgba(74, 222, 128, 0.28) 0%, rgba(34, 197, 94, 0) 70%);
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

      /* Live Beacon Badge - Cyan & Emerald */
      .ag-hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.18) 0%, rgba(74, 222, 128, 0.14) 100%);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(125, 211, 252, 0.35);
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #e0f2fe;
        margin-bottom: 0.9rem;
        box-shadow: 0 4px 14px rgba(14, 165, 233, 0.18);
      }
      .ag-hero-beacon {
        width: 8px;
        height: 8px;
        background-color: #38bdf8;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.8);
        animation: ag-beacon-radar 2s infinite;
      }
      @keyframes ag-beacon-radar {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.8); }
        50% { box-shadow: 0 0 0 6px rgba(74, 222, 128, 0.35); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
      }

      /* Headline - explicitly white with cyan-to-emerald highlight */
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
        background: linear-gradient(135deg, #7dd3fc 0%, #38bdf8 35%, #4ade80 75%, #a7f3d0 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        display: inline-block !important;
        filter: drop-shadow(0 0 16px rgba(56, 189, 248, 0.35)) !important;
      }

      .ag-hero-copy {
        max-width: 660px;
        margin: 0 0 1.6rem;
        color: #e0f2fe;
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
        border-top: 1px solid rgba(56, 189, 248, 0.2);
      }
      .ag-hero-stat-item {
        display: flex;
        flex-direction: column;
      }
      .ag-hero-stat-val {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.15rem;
        font-weight: 800;
        color: #f0fdfa;
        letter-spacing: -0.02em;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
      }
      .ag-hero-stat-lbl {
        font-size: 0.74rem;
        font-weight: 600;
        color: #7dd3fc;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      /* Right Column: Liquid Glass Bulb Horizon Card */
      .ag-hero-glass-card {
        position: relative;
        z-index: 2;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.18) 0%, rgba(56, 189, 248, 0.1) 40%, rgba(34, 197, 94, 0.1) 100%);
        backdrop-filter: blur(20px) saturate(190%);
        -webkit-backdrop-filter: blur(20px) saturate(190%);
        border: 1px solid rgba(125, 211, 252, 0.35);
        border-top: 1.5px solid rgba(255, 255, 255, 0.65);
        border-radius: 18px;
        padding: 1.5rem 1.6rem;
        box-shadow: 0 16px 40px rgba(2, 24, 36, 0.3), inset 0 1.5px 2px rgba(255, 255, 255, 0.4), inset 0 -1.5px 2px rgba(56, 189, 248, 0.2);
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
      }
      .ag-hero-glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(125, 211, 252, 0.55);
        box-shadow: 0 20px 48px rgba(2, 24, 36, 0.35), 0 0 24px rgba(56, 189, 248, 0.2);
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
        background: rgba(56, 189, 248, 0.22);
        color: #bae6fd;
        border: 1px solid rgba(56, 189, 248, 0.45);
        padding: 2px 8px;
        border-radius: 9999px;
        text-transform: uppercase;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
      }

      .ag-hero-card-desc {
        color: #e0f2fe;
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
        background: rgba(2, 24, 36, 0.35);
        border: 1px solid rgba(56, 189, 248, 0.15);
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 0.78rem;
        color: #f0fdfa;
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
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
            <span>Priority Zones: Gasabo, Bugesera, Musanze</span>
          </div>
          <div class="ag-hero-pill-info">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"></path></svg>
            <span>Optimal planting window actively tracked</span>
          </div>
          <div class="ag-hero-pill-info">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
            <span>AI Assistant available via corner bulb</span>
          </div>
        </div>
      </aside>
    </section>
    """)
