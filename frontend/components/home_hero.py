"""Creative, animated agro-intelligence hero for agrimenya."""
import os
import streamlit as st
import streamlit.components.v1 as components
from utils.i18n import t


def _ensure_landing_video() -> str:
    """Legacy helper maintained for backward compatibility."""
    return ""


def render_home_hero() -> None:
    """Render a floating hero command center with high-contrast intelligence cards."""
    badge_text = t("hero.badge", "Rwanda Agro-Climate Decision Engine")
    title_pre = t("hero.title_pre", "Make the next")
    title_glow = t("hero.title_glow", "field decision")
    title_post = t("hero.title_post", "clearer.")
    copy_text = t("hero.copy", "Explore spatial zone intelligence, evaluate seasonal crop recommendations, and turn data-grounded insights into synchronized field plans.")
    stat_districts_val = t("hero.stat.districts_val", "30 Districts")
    stat_districts_lbl = t("hero.stat.districts_lbl", "Spatial Coverage")
    stat_crops_val = t("hero.stat.crops_val", "10+ Key Crops")
    stat_crops_lbl = t("hero.stat.crops_lbl", "SAS Baselines")
    stat_weather_val = t("hero.stat.weather_val", "Real-time Weather")
    stat_weather_lbl = t("hero.stat.weather_lbl", "Satellite Indicators")
    stat_timezone_val = t("hero.stat.timezone_val", "CAT (UTC+2)")
    stat_timezone_lbl = t("hero.stat.timezone_lbl", "System Timezone")
    card_title = t("hero.card.title", "Seasonal Horizon")
    card_tag = t("hero.card.tag", "2026 Season A")
    card_desc = t("hero.card.desc", "Active 2026 Season A campaign. Tracking soil moisture and conformal yield bounds.")
    pill_priority = t("hero.pill.priority", "Priority Zones: Gasabo, Bugesera, Musanze")
    pill_window = t("hero.pill.window", "Optimal planting window actively tracked")
    pill_ai = t("hero.pill.ai", "AI Assistant available via corner bulb")

    st.html("""
    <style>
      iframe[title="streamlit.components.v1.custom_component"] {
        border: none !important;
        background: transparent !important;
        width: 100% !important;
        border-radius: 22px !important;
        overflow: hidden !important;
      }
      div[data-testid="stCustomComponentV1"] {
        margin-bottom: 1.5rem !important;
      }
      /* Action workflow cards: structured modern cards with classic motion */
      [data-testid="stVerticalBlockBorderWrapper"] {
        position: relative !important;
        overflow: hidden !important;
        background: #ffffff !important;
        border: 1px solid rgba(2, 132, 199, 0.20) !important;
        border-top: 3px solid #0284c7 !important;
        box-shadow: 0 4px 18px rgba(2, 132, 199, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        border-radius: 18px !important;
        transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                    box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                    border-color 0.3s ease,
                    background 0.3s ease !important;
        will-change: transform, box-shadow;
      }
      [data-testid="stVerticalBlockBorderWrapper"]:hover {
        background: #f0f9ff !important;
        border-color: #0284c7 !important;
        border-top-color: #0369a1 !important;
        box-shadow: 0 12px 32px rgba(2, 132, 199, 0.16), 0 2px 6px rgba(0, 0, 0, 0.04) !important;
        transform: translateY(-4px) scale(1.008) !important;
      }
      [data-testid="stVerticalBlockBorderWrapper"]:active {
        transform: translateY(-1px) scale(0.998) !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.12) !important;
        transition: transform 0.12s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.12s ease !important;
      }

      /* Headings & Text inside cards */
      [data-testid="stVerticalBlockBorderWrapper"] h1,
      [data-testid="stVerticalBlockBorderWrapper"] h2,
      [data-testid="stVerticalBlockBorderWrapper"] h3,
      [data-testid="stVerticalBlockBorderWrapper"] h4 {
        color: #0f172a !important;
        text-shadow: none !important;
      }
      [data-testid="stVerticalBlockBorderWrapper"] p,
      [data-testid="stVerticalBlockBorderWrapper"] span:not([style*="color"]) {
        color: #475569 !important;
        text-shadow: none !important;
      }

      /* Structured Card Buttons - High specificity override */
      [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:not([role="tab"]):not([data-baseweb="tab"]),
      [data-testid="stVerticalBlockBorderWrapper"] button:not([role="tab"]):not([data-baseweb="tab"]):not([aria-selected]),
      [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stBaseButton-secondary"]:not([role="tab"]):not([data-baseweb="tab"]):not([aria-selected]) {
        background: #f0f9ff !important;
        border: 1.5px solid rgba(2, 132, 199, 0.35) !important;
        border-radius: 10px !important;
        color: #0284c7 !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        text-shadow: none !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.08) !important;
      }
      [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:not([role="tab"]):not([data-baseweb="tab"]) *,
      [data-testid="stVerticalBlockBorderWrapper"] button:not([role="tab"]):not([data-baseweb="tab"]):not([aria-selected]) * {
        color: #0284c7 !important;
        font-weight: 700 !important;
      }
      [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:not([role="tab"]):not([data-baseweb="tab"]):hover,
      [data-testid="stVerticalBlockBorderWrapper"] button:not([role="tab"]):not([data-baseweb="tab"]):not([aria-selected]):hover,
      [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stBaseButton-secondary"]:not([role="tab"]):not([data-baseweb="tab"]):not([aria-selected]):hover {
        background: #0284c7 !important;
        border-color: #0284c7 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.30) !important;
        transform: translateY(-2px) !important;
      }
      [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover *,
      [data-testid="stVerticalBlockBorderWrapper"] button:hover * {
        color: #ffffff !important;
      }

      /* Clean section titles & subtitles */
      .ag-section-title, h2.ag-section-title {
        color: #0a1f26 !important;
        -webkit-text-fill-color: #0a1f26 !important;
        text-shadow: none !important;
      }
      .ag-section-subtitle, p.ag-section-subtitle {
        color: #48656c !important;
        -webkit-text-fill-color: #48656c !important;
        text-shadow: none !important;
      }
    </style>
    """)

    hero_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
      <style>
        * {{
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }}
        html, body {{
          background: transparent;
          font-family: 'Plus Jakarta Sans', sans-serif;
          overflow: hidden;
          width: 100%;
          height: 100%;
        }}

        /* Command center card */
        .ag-hero-wrapper {{
          position: relative;
          overflow: hidden;
          width: 100%;
          min-height: 380px;
          color: #0f172a;
          background: linear-gradient(
            135deg,
            #ffffff 0%,
            #f0f9ff 50%,
            #e0f2fe 100%
          );
          border-radius: 22px;
          border: 1px solid rgba(2, 132, 199, 0.22);
          border-top: 2.5px solid #0284c7;
          box-shadow: 0 16px 40px rgba(2, 132, 199, 0.12), 0 2px 8px rgba(0, 0, 0, 0.04);
          animation: ag-hero-enter 0.7s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        @keyframes ag-hero-enter {{
          from {{ opacity: 0; transform: translateY(16px) scale(0.99); }}
          to {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}

        @keyframes ag-text-shimmer {{
          0% {{ filter: drop-shadow(0 0 14px rgba(56, 189, 248, 0.45)); }}
          50% {{ filter: drop-shadow(0 0 24px rgba(56, 189, 248, 0.75)); }}
          100% {{ filter: drop-shadow(0 0 18px rgba(56, 189, 248, 0.6)); }}
        }}

        @keyframes ag-hero-card-float {{
          0% {{ transform: translateY(0); }}
          100% {{ transform: translateY(-5px); }}
        }}

        /* Ambient Cyan Bulb & Tree Emerald Light Orbs inside hero card */
        .ag-hero-glow-1 {{
          position: absolute;
          top: -60px;
          right: 18%;
          width: 320px;
          height: 320px;
          background: radial-gradient(circle, rgba(56, 189, 248, 0.24) 0%, rgba(14, 165, 233, 0) 70%);
          border-radius: 50%;
          filter: blur(35px);
          pointer-events: none;
          z-index: 1;
          animation: ag-hero-orb-float 7s ease-in-out infinite alternate;
        }}
        .ag-hero-glow-2 {{
          position: absolute;
          bottom: -80px;
          left: 20%;
          width: 360px;
          height: 360px;
          background: radial-gradient(circle, rgba(74, 222, 128, 0.20) 0%, rgba(34, 197, 94, 0) 70%);
          border-radius: 50%;
          filter: blur(40px);
          pointer-events: none;
          z-index: 1;
          animation: ag-hero-orb-float-2 9s ease-in-out infinite alternate;
        }}

        @keyframes ag-hero-orb-float {{
          0% {{ transform: translate(0, 0) scale(1); }}
          100% {{ transform: translate(-30px, 25px) scale(1.15); }}
        }}
        @keyframes ag-hero-orb-float-2 {{
          0% {{ transform: translate(0, 0) scale(1); }}
          100% {{ transform: translate(35px, -20px) scale(1.12); }}
        }}

        /* Symmetrical 2-Column Grid Layout */
        .ag-hero-grid {{
          position: relative;
          z-index: 2;
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2.5rem;
          align-items: center;
          padding: 2.8rem 3rem;
          min-height: 380px;
        }}

        .ag-hero-content {{
          position: relative;
        }}

        /* Live Beacon Badge - Cyan & Emerald */
        .ag-hero-badge {{
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: #ffffff;
          border: 1px solid rgba(2, 132, 199, 0.35);
          padding: 5px 14px;
          border-radius: 9999px;
          font-size: 0.76rem;
          font-weight: 750;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #0284c7;
          margin-bottom: 0.85rem;
          box-shadow: 0 2px 8px rgba(2, 132, 199, 0.12);
          transition: transform 0.25s ease;
        }}
        .ag-hero-badge:hover {{
          transform: scale(1.03);
        }}
        .ag-hero-beacon {{
          width: 8px;
          height: 8px;
          background-color: #0284c7;
          border-radius: 50%;
          display: inline-block;
          box-shadow: 0 0 0 0 rgba(2, 132, 199, 0.8);
          animation: ag-beacon-radar 2s infinite;
        }}
        @keyframes ag-beacon-radar {{
          0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(2, 132, 199, 0.8); }}
          50% {{ box-shadow: 0 0 0 6px rgba(2, 132, 199, 0.35); }}
          100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(2, 132, 199, 0); }}
        }}

        /* Headline with High Contrast */
        .ag-hero-title {{
          margin: 0 0 0.8rem !important;
          color: #0f172a !important;
          font-size: clamp(2rem, 3.5vw, 3.1rem) !important;
          line-height: 1.1 !important;
          font-weight: 800 !important;
          letter-spacing: -0.04em !important;
          text-shadow: none !important;
        }}
        .ag-hero-glow-text {{
          background: linear-gradient(135deg, #0369a1 0%, #0284c7 60%, #0ea5e9 100%) !important;
          -webkit-background-clip: text !important;
          -webkit-text-fill-color: transparent !important;
          display: inline-block !important;
          filter: drop-shadow(0 2px 8px rgba(2, 132, 199, 0.25)) !important;
        }}

        .ag-hero-copy {{
          max-width: 640px;
          margin: 0 0 1.5rem;
          color: #334155;
          font-size: 0.98rem;
          line-height: 1.6;
          font-weight: 500;
          text-shadow: none;
        }}

        /* Stats Ticker Strip with Hover Lift */
        .ag-hero-stats {{
          display: flex;
          flex-wrap: wrap;
          gap: 1.4rem;
          align-items: center;
          padding-top: 1rem;
          border-top: 1px solid rgba(2, 132, 199, 0.20);
        }}
        .ag-hero-stat-item {{
          display: flex;
          flex-direction: column;
          transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
          cursor: default;
        }}
        .ag-hero-stat-item:hover {{
          transform: translateY(-3px) scale(1.04);
        }}
        .ag-hero-stat-val {{
          font-size: 1.15rem;
          font-weight: 800;
          color: #0f172a;
          letter-spacing: -0.02em;
          text-shadow: none;
          transition: color 0.2s ease;
        }}
        .ag-hero-stat-item:hover .ag-hero-stat-val {{
          color: #0284c7;
        }}
        .ag-hero-stat-lbl {{
          font-size: 0.72rem;
          font-weight: 650;
          color: #0284c7;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          text-shadow: none;
        }}

        /* Right Column: Structured Horizon Card with Subtle Float */
        .ag-hero-horizon-card {{
          position: relative;
          background: #ffffff;
          border: 1px solid rgba(2, 132, 199, 0.22);
          border-top: 2.5px solid #0284c7;
          border-radius: 18px;
          padding: 1.5rem 1.6rem;
          box-shadow: 0 12px 32px rgba(2, 132, 199, 0.12), 0 2px 8px rgba(0, 0, 0, 0.04);
          animation: ag-hero-card-float 6s ease-in-out infinite alternate;
          transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        .ag-hero-horizon-card:hover {{
          transform: translateY(-4px);
          box-shadow: 0 16px 40px rgba(2, 132, 199, 0.18);
          border-color: #0284c7;
        }}
        .ag-hero-card-header {{
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0.75rem;
        }}
        .ag-hero-card-title {{
          font-size: 0.92rem;
          font-weight: 750;
          color: #0f172a;
          letter-spacing: -0.01em;
          text-shadow: none;
        }}
        .ag-hero-card-tag {{
          font-size: 0.72rem;
          font-weight: 700;
          background: #e0f2fe;
          color: #0284c7;
          border: 1px solid rgba(2, 132, 199, 0.35);
          padding: 2px 8px;
          border-radius: 9999px;
          text-transform: uppercase;
        }}
        .ag-hero-card-desc {{
          color: #475569;
          font-size: 0.85rem;
          line-height: 1.5;
          margin-bottom: 0.9rem;
          text-shadow: none;
        }}
        .ag-hero-card-row {{
          display: flex;
          flex-direction: column;
          gap: 0.45rem;
        }}
        .ag-hero-pill-info {{
          display: flex;
          align-items: center;
          gap: 8px;
          background: #f0f9ff;
          border: 1px solid rgba(2, 132, 199, 0.20);
          padding: 6px 10px;
          border-radius: 8px;
          font-size: 0.78rem;
          color: #0369a1;
          transition: all 0.25s ease;
        }}
        .ag-hero-pill-info:hover {{
          background: #e0f2fe;
          border-color: rgba(2, 132, 199, 0.45);
          transform: translateX(4px);
          box-shadow: 0 2px 8px rgba(2, 132, 199, 0.12);
        }}

        @media (max-width: 900px) {{
          .ag-hero-grid {{
            grid-template-columns: 1fr;
            padding: 1.8rem 1.5rem;
            gap: 1.5rem;
          }}
        }}
      </style>
    </head>
    <body>
      <section class="ag-hero-wrapper" aria-label="agrimenya overview">
        <div class="ag-hero-glow-1"></div>
        <div class="ag-hero-glow-2"></div>

        <div class="ag-hero-grid">
          <div class="ag-hero-content">
            <div class="ag-hero-badge">
              <span class="ag-hero-beacon"></span>
              {badge_text}
            </div>
            <h1 class="ag-hero-title">
              {title_pre}<br/>
              <span class="ag-hero-glow-text">{title_glow}</span> {title_post}
            </h1>
            <p class="ag-hero-copy">
              {copy_text}
            </p>

            <div class="ag-hero-stats">
              <div class="ag-hero-stat-item">
                <span class="ag-hero-stat-val">{stat_districts_val}</span>
                <span class="ag-hero-stat-lbl">{stat_districts_lbl}</span>
              </div>
              <div class="ag-hero-stat-item">
                <span class="ag-hero-stat-val">{stat_crops_val}</span>
                <span class="ag-hero-stat-lbl">{stat_crops_lbl}</span>
              </div>
              <div class="ag-hero-stat-item">
                <span class="ag-hero-stat-val">{stat_weather_val}</span>
                <span class="ag-hero-stat-lbl">{stat_weather_lbl}</span>
              </div>
              <div class="ag-hero-stat-item">
                <span class="ag-hero-stat-val">{stat_timezone_val}</span>
                <span class="ag-hero-stat-lbl">{stat_timezone_lbl}</span>
              </div>
            </div>
          </div>

          <aside class="ag-hero-horizon-card">
            <div class="ag-hero-card-header">
              <span class="ag-hero-card-title">{card_title}</span>
              <span class="ag-hero-card-tag">{card_tag}</span>
            </div>
            <p class="ag-hero-card-desc">
              {card_desc}
            </p>
            <div class="ag-hero-card-row">
              <div class="ag-hero-pill-info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                <span>{pill_priority}</span>
              </div>
              <div class="ag-hero-pill-info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"></path></svg>
                <span>{pill_window}</span>
              </div>
              <div class="ag-hero-pill-info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                <span>{pill_ai}</span>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <script>
        (function cleanupVideoBackground() {{
          try {{
            const parentDoc = window.parent.document;
            if (!parentDoc) return;
            const video = parentDoc.getElementById('ag-landing-fullpage-video');
            if (video) video.remove();
            const overlay = parentDoc.getElementById('ag-landing-fullpage-overlay');
            if (overlay) overlay.remove();
          }} catch (err) {{
            console.debug('Video cleanup note:', err);
          }}
        }})();
      </script>
    </body>
    </html>
    """

    components.html(hero_html, height=420)

